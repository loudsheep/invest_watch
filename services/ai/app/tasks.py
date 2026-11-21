import json
from pathlib import Path

from investwatch_common.app_settings import get_setting
from investwatch_common.config import settings
from investwatch_common.db import SessionLocal
from investwatch_common.logging import get_logger
from investwatch_common.models import Case, Document, Finding, Label, Mention, ModelRun, User
from investwatch_common.redis_client import HIGH_RISK_CHANNEL, get_redis

from .celery_app import celery_app
from .classifiers import m1, m2, m3
from .classifiers.head import get_model_version, score_with_fallback, train_head
from .embeddings import embed
from .entity_resolution import find_entities_by_ids, find_entities_in_text, resolve_by_domain, resolve_mention
from .language import detect_language
from .llm import JUDGE_PROMPT_VERSION, PROMPT_VERSION, analyze, judge_criterion, translate_to_polish
from .topic_centroids import get_topic_vectors

logger = get_logger(__name__)

SCAN_STAGE_CHANNEL = "scan:stages"
LLM_CANDIDATE_THRESHOLD = 0.6
RELEVANCE_THRESHOLD = 0.5  # classifier score below which a document is off-topic for the module
HIGH_RISK_THRESHOLD = 0.8
LLM_CACHE_PREFIX = "llm_cache:"
LLM_CACHE_TTL_SECONDS = 86400 * 7
_REFERENCE_LABELS_PATH = Path("/app/data/reference_labels.json")


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


TRANSLATION_CACHE_PREFIX = "translation:"
TRANSLATION_CACHE_TTL_SECONDS = 86400 * 30


def _translation(doc: Document) -> dict | None:
    """Polish translation of a non-Polish document (LLM, cached by content hash and model)."""
    original = doc.text_normalized or doc.content or ""
    language = detect_language(original)
    if language in (None, "pl"):
        return None
    cache_key = f"{TRANSLATION_CACHE_PREFIX}{doc.content_hash}:{settings.llm_model}"
    redis_client = get_redis()
    cached = redis_client.get(cache_key)
    if cached is not None:
        return json.loads(cached)
    text_pl = translate_to_polish(doc.content or original)
    if not text_pl:
        return None
    payload = {"language": language, "text_pl": text_pl, "model": settings.llm_model}
    redis_client.set(cache_key, json.dumps(payload), ex=TRANSLATION_CACHE_TTL_SECONDS)
    return payload


JUDGE_CACHE_PREFIX = "llm_judge:"


def _make_judge(doc: Document):
    """LLM verdict per (document, criterion), cached by content hash and prompt version."""
    redis_client = get_redis()

    def judge(criterion: dict, subject: str) -> dict | None:
        key = f"{JUDGE_CACHE_PREFIX}{doc.content_hash}:{criterion['id']}:v{JUDGE_PROMPT_VERSION}:{settings.llm_model}"
        cached = redis_client.get(key)
        if cached is not None:
            return json.loads(cached)
        verdict = judge_criterion(criterion["llm_instruction"], subject)
        if verdict is not None:
            redis_client.set(key, json.dumps(verdict), ex=LLM_CACHE_TTL_SECONDS)
        return verdict

    return judge


def _module_details(db, doc: Document, module: str, translation: dict | None = None, judge=None) -> dict:
    text = translation["text_pl"] if translation else doc.text_normalized or doc.content or ""
    if module == "m1":
        # raw content: normalization replaces URLs, which would hide ?ref= links and keeps case of promo codes
        return m1.build_details(text if translation else doc.content or text)
    if module == "m2":
        return m2.evaluate(text, doc.computed_styles, judge=judge)
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
        if any(not match["authorized"] for match in details.get("registry_id_matches", [])):
            return 0.95  # the text quotes the KRS/NIP of an entity from the public warnings list
        age = details.get("domain_age_days")
        young_domain = age is not None and age < 365
        lookalike_score = 0.9 if has_lookalike and young_domain else 0.8
        return max(lookalike_score if has_lookalike else 0.0, 0.6 if has_advisory else 0.0)
    return 0.0


def _create_mentions(db, doc: Document) -> None:
    domain_entity = resolve_by_domain(db, doc.url)
    if domain_entity:
        db.add(Mention(document_id=doc.id, entity_id=domain_entity.id, role="advertised_firm"))

    if doc.author:
        author_entity = resolve_mention(db, doc.author)
        if author_entity and (not domain_entity or author_entity.id != domain_entity.id):
            db.add(Mention(document_id=doc.id, entity_id=author_entity.id, role="publisher"))

    db.flush()
    known = {m.entity_id for m in db.query(Mention).filter(Mention.document_id == doc.id).all()}
    by_ids = [entity for _kind, _number, entity in find_entities_by_ids(db, doc.content or "")]
    for entity in [*find_entities_in_text(db, doc.content or ""), *by_ids]:
        if entity.id not in known:
            known.add(entity.id)
            db.add(Mention(document_id=doc.id, entity_id=entity.id, role="advertised_firm"))
    db.commit()


def _is_authorized_site(db, doc: Document, details: dict) -> bool:
    """M3 looks for unauthorized advisers: a page on the registered domain of an authorized firm is not one."""
    if not get_setting(db, "m3_suppress_authorized_domains") or details.get("lookalike_domain"):
        return False
    owner = resolve_by_domain(db, doc.url)
    return owner is not None and bool(owner.authorized)


def _ground_truth(doc: Document, module: str) -> bool | None:
    """Dataset labels (bool or per-module object) win over the demo-sites reference file."""
    dataset_label = (doc.computed_styles or {}).get("dataset_label")
    if isinstance(dataset_label, bool):
        return dataset_label
    if isinstance(dataset_label, dict):
        return bool(dataset_label[module]) if module in dataset_label else None
    if not _REFERENCE_LABELS_PATH.exists() or not any(host in doc.url for host in ("demo-sites", "-demo.local")):
        return None
    reference = json.loads(_REFERENCE_LABELS_PATH.read_text(encoding="utf-8"))
    slug = doc.url.split("?")[0].rstrip("/").rsplit("/", 1)[-1]
    return module in reference[slug] if slug in reference else None


def _apply_ground_truth(db, finding: Finding, doc: Document) -> None:
    """Seeds calibration labels from a labeled dataset and the demo-sites fixtures."""
    truth = _ground_truth(doc, finding.module)
    admin = db.query(User).filter(User.role == "admin").first()
    if truth is None or admin is None:
        return
    db.add(Label(finding_id=finding.id, label=truth, created_by=admin.id))
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
        translation = _translation(doc)
        module_results: dict[str, dict] = {}
        llm_ran = False
        for module in ("m1", "m2", "m3"):
            details = _module_details(db, doc, module, translation)
            if translation:
                details["translation"] = translation
            if module == "m3" and _is_authorized_site(db, doc, details):
                continue
            rule_score = _rule_signal_score(module, details)
            head_score = score_with_fallback(module, embedding, get_topic_vectors(module))
            module_results[module] = {"relevance": round(head_score, 2), "score": None, "finding_id": None}
            removed_disclaimer = module == "m2" and bool((doc.computed_styles or {}).get("change_detection"))
            warned_entity = module == "m3" and any(
                not match["authorized"] for match in details.get("registry_id_matches", [])
            )
            if head_score < RELEVANCE_THRESHOLD and not (removed_disclaimer or warned_entity):
                continue  # rules only measure how bad a relevant document is
            combined_score = max(rule_score, head_score)

            threshold = _get_threshold(module)
            if combined_score < threshold * 0.5:
                continue  # not even a weak candidate, skip creating noise

            if module == "m2":  # the LLM judge runs only for documents that are relevant enough to become findings
                details = _module_details(db, doc, module, translation, judge=_make_judge(doc))
                if translation:
                    details["translation"] = translation
                rule_score = _rule_signal_score(module, details)
                combined_score = max(rule_score, head_score)

            evidence_text = json.dumps(details, ensure_ascii=False)[:2000]
            explanation = f"Rule signal={rule_score:.2f}, classifier={head_score:.2f}"
            prompt_version = 1

            if combined_score >= LLM_CANDIDATE_THRESHOLD:
                llm_ran = True
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
            module_results[module].update(score=round(combined_score, 2), finding_id=finding.id)

            _aggregate_into_case(db, finding, doc)
            _apply_ground_truth(db, finding, doc)

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

        _publish_scan_stage(scan_id, "classify", "done", data={"modules": module_results})
        if not llm_ran:
            _publish_scan_stage(scan_id, "llm", "done", "Pominięto: żaden wynik nie przekroczył progu analizy LLM")
        created = [m for m, r in module_results.items() if r["finding_id"]]
        if created:
            message = f"Utworzono findingi: {', '.join(m.upper() for m in created)}"
        else:
            message = (
                "Brak findingów: treść nie dotyczy żadnego modułu "
                f"(trafność poniżej progu {RELEVANCE_THRESHOLD:.2f}, albo wynik zbyt niski)"
            )
        _publish_scan_stage(scan_id, "done", "done", message, {"modules": module_results})
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
        if result["status"] == "trained":
            db.add(
                ModelRun(
                    module=module,
                    version=result["version"],
                    labels=result["n_samples"],
                    positives=result["positives"],
                    metrics=result["metrics"],
                )
            )
            db.commit()
        logger.info("retrain_complete", module=module, result=result)
        return result
    finally:
        db.close()
