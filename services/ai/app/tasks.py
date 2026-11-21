import json

from investwatch_common.db import SessionLocal
from investwatch_common.logging import get_logger
from investwatch_common.models import Case, Document, Finding, Label, Mention
from investwatch_common.redis_client import HIGH_RISK_CHANNEL, get_redis

from .celery_app import celery_app
from .classifiers import m1, m2, m3
from .classifiers.head import get_model_version, score_with_fallback, train_head
from .embeddings import embed
from .entity_resolution import resolve_by_domain, resolve_mention
from .llm import PROMPT_VERSION, analyze
from .topic_centroids import get_centroid

logger = get_logger(__name__)

SCAN_STAGE_CHANNEL = "scan:stages"
LLM_CANDIDATE_THRESHOLD = 0.6
HIGH_RISK_THRESHOLD = 0.8
LLM_CACHE_PREFIX = "llm_cache:"
LLM_CACHE_TTL_SECONDS = 86400 * 7


def _publish_scan_stage(
    scan_id: str | None, stage: str, status: str, message: str | None = None, data: dict | None = None
):
    if not scan_id:
        return
    payload = {"scan_id": scan_id, "stage": stage, "status": status, "message": message, "data": data or {}}
    get_redis().publish(SCAN_STAGE_CHANNEL, json.dumps(payload))


def _get_threshold(module: str) -> float:
    raw = get_redis().get(f"threshold:{module}")
    return float(raw) if raw is not None else 0.5


def _cached_llm_analysis(doc: Document, module: str):
    cache_key = f"{LLM_CACHE_PREFIX}{doc.content_hash}:{module}:v{PROMPT_VERSION}"
    redis_client = get_redis()
    cached = redis_client.get(cache_key)
    if cached is not None:
        data = json.loads(cached)
        return data

    result = analyze(doc.text_normalized or doc.content, module)
    if result is None:
        return None

    payload = result.model_dump()
    redis_client.set(cache_key, json.dumps(payload), ex=LLM_CACHE_TTL_SECONDS)
    return payload


def _module_details(db, doc: Document, module: str) -> dict:
    text = doc.text_normalized or doc.content or ""
    if module == "m1":
        return m1.build_details(text)
    if module == "m2":
        return m2.evaluate(text, doc.computed_styles)
    if module == "m3":
        return m3.build_details(db, text, doc.url)
    return {}


def _rule_signal_score(module: str, details: dict) -> float:
    if module == "m1":
        if details.get("undisclosed_cooperation"):
            return 0.9
        return 0.3 if details.get("affiliate_evidence") else 0.0
    if module == "m2":
        return details.get("risk_score", 0.0)
    if module == "m3":
        has_advisory = bool(details.get("advisory_offer_evidence"))
        has_lookalike = bool(details.get("lookalike_domain"))
        return max(0.8 if has_lookalike else 0.0, 0.6 if has_advisory else 0.0)
    return 0.0


def _create_mentions(db, doc: Document) -> None:
    domain_entity = resolve_by_domain(db, doc.url)
    if domain_entity:
        db.add(Mention(document_id=doc.id, entity_id=domain_entity.id, role="advertised_firm"))

    if doc.author:
        author_entity = resolve_mention(db, doc.author)
        if author_entity and (not domain_entity or author_entity.id != domain_entity.id):
            db.add(Mention(document_id=doc.id, entity_id=author_entity.id, role="publisher"))
    db.commit()


def _aggregate_into_case(db, finding: Finding, doc: Document) -> None:
    mention = db.query(Mention).filter(Mention.document_id == doc.id).first()
    if mention is None:
        return

    case = db.query(Case).filter(Case.primary_entity_id == mention.entity_id).first()
    if case is None:
        case = Case(
            primary_entity_id=mention.entity_id,
            finding_ids=[finding.id],
            description=f"Case for entity {mention.entity_id}",
        )
        db.add(case)
    else:
        case.finding_ids = list(set((case.finding_ids or []) + [finding.id]))
    db.commit()


@celery_app.task(name="ai_worker.tasks.process_document")
def process_document(document_id: int, scan_id: str | None = None):
    db = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if doc is None:
            logger.warning("document_not_found", document_id=document_id)
            return

        _publish_scan_stage(scan_id, "embed", "running")
        embedding = embed(doc.text_normalized or doc.content or "")
        doc.embedding = embedding
        db.commit()
        _publish_scan_stage(scan_id, "embed", "done")

        _create_mentions(db, doc)

        _publish_scan_stage(scan_id, "classify", "running")
        for module in ("m1", "m2", "m3"):
            details = _module_details(db, doc, module)
            rule_score = _rule_signal_score(module, details)
            head_score = score_with_fallback(module, embedding, get_centroid(module))
            combined_score = max(rule_score, head_score)

            threshold = _get_threshold(module)
            if combined_score < threshold * 0.5:
                continue  # not even a weak candidate, skip creating noise

            evidence_text = json.dumps(details, ensure_ascii=False)[:2000]
            explanation = f"Rule signal={rule_score:.2f}, classifier={head_score:.2f}"
            prompt_version = 1

            if combined_score >= LLM_CANDIDATE_THRESHOLD:
                _publish_scan_stage(scan_id, "llm", "running")
                llm_result = _cached_llm_analysis(doc, module)
                if llm_result:
                    explanation = llm_result.get("rationale", explanation)
                    details["llm"] = llm_result
                    prompt_version = PROMPT_VERSION
                _publish_scan_stage(scan_id, "llm", "done")

            finding = Finding(
                document_id=doc.id,
                module=module,
                score=combined_score,
                model_version=get_model_version(module),
                prompt_version=prompt_version,
                evidence=evidence_text,
                explanation=explanation,
                details=details,
                status="new",
            )
            db.add(finding)
            db.commit()
            db.refresh(finding)

            _aggregate_into_case(db, finding, doc)

            if combined_score >= HIGH_RISK_THRESHOLD:
                get_redis().publish(
                    HIGH_RISK_CHANNEL,
                    json.dumps(
                        {
                            "id": finding.id,
                            "module": finding.module,
                            "score": finding.score,
                            "document_url": doc.url,
                            "document_title": doc.title,
                        }
                    ),
                )

        _publish_scan_stage(scan_id, "classify", "done")
        _publish_scan_stage(scan_id, "done", "done")
    except Exception as exc:
        logger.exception("process_document_failed", document_id=document_id, error=str(exc))
        _publish_scan_stage(scan_id, "error", "error", str(exc))
    finally:
        db.close()


@celery_app.task(name="ai_worker.tasks.retrain_classifier")
def retrain_classifier(module: str):
    db = SessionLocal()
    try:
        rows = (
            db.query(Finding.document_id, Label.label)
            .join(Label, Label.finding_id == Finding.id)
            .filter(Finding.module == module)
            .all()
        )
        embeddings = []
        labels = []
        for document_id, label in rows:
            doc = db.get(Document, document_id)
            if doc is not None and doc.embedding is not None:
                embeddings.append(list(doc.embedding))
                labels.append(bool(label))

        result = train_head(module, embeddings, labels)
        logger.info("retrain_complete", module=module, result=result)
        return result
    finally:
        db.close()
