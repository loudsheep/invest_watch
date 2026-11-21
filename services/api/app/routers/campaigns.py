from collections import defaultdict
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Query
from investwatch_common.db import get_db
from investwatch_common.models import Document, Finding, User
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..auth import get_current_user

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

PAIRS_SQL = text(
    """
    SELECT a.id, b.id
    FROM documents a
    JOIN documents b ON a.id < b.id
    WHERE a.embedding IS NOT NULL AND b.embedding IS NOT NULL
      AND (a.embedding <=> b.embedding) < :distance
      AND EXISTS (SELECT 1 FROM findings f WHERE f.document_id = a.id)
      AND EXISTS (SELECT 1 FROM findings f WHERE f.document_id = b.id)
    """
)


def _components(pairs: list[tuple[int, int]]) -> list[set[int]]:
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        parent[find(a)] = find(b)
    groups: dict[int, set[int]] = defaultdict(set)
    for node in list(parent):
        groups[find(node)].add(node)
    return list(groups.values())


@router.get("")
def list_campaigns(
    threshold: float = Query(default=0.95, ge=0.5, le=0.999),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Campaign clusters: findings whose documents carry (nearly) the same content, found by
    embedding similarity. One cluster is the same message spread over several authors or sites."""
    pairs = [(a, b) for a, b in db.execute(PAIRS_SQL, {"distance": 1 - threshold}).all()]
    clusters = []
    for members in _components(pairs):
        documents = db.query(Document).filter(Document.id.in_(members)).order_by(Document.fetched_at).all()
        findings_by_doc: dict[int, list[Finding]] = defaultdict(list)
        for finding in db.query(Finding).filter(Finding.document_id.in_(members)).all():
            findings_by_doc[finding.document_id].append(finding)

        items, promo_codes = [], set()
        for doc in documents:
            findings = sorted(findings_by_doc[doc.id], key=lambda f: f.score or 0, reverse=True)
            promo_codes |= {f.details["promo_code"] for f in findings if (f.details or {}).get("promo_code")}
            items.append(
                {
                    "document_id": doc.id,
                    "title": doc.title,
                    "url": doc.url,
                    "domain": urlparse(doc.url).hostname,
                    "author": doc.author,
                    "platform": doc.platform,
                    "fetched_at": doc.fetched_at,
                    "findings": [{"id": f.id, "module": f.module, "score": f.score} for f in findings],
                }
            )
        scores = [f["score"] or 0 for item in items for f in item["findings"]]
        clusters.append(
            {
                "id": min(members),
                "size": len(items),
                "authors": sorted({i["author"] for i in items if i["author"]}),
                "domains": sorted({i["domain"] for i in items if i["domain"]}),
                "promo_codes": sorted(promo_codes),
                "modules": sorted({f["module"] for item in items for f in item["findings"]}),
                "max_score": max(scores, default=0),
                "first_seen": items[0]["fetched_at"],
                "last_seen": items[-1]["fetched_at"],
                "documents": items,
            }
        )
    clusters.sort(key=lambda c: (len(c["authors"]), c["size"], c["max_score"]), reverse=True)
    return clusters[:50]
