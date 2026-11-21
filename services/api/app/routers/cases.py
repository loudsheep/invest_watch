from fastapi import APIRouter, Depends, HTTPException, status
from investwatch_common.db import get_db
from investwatch_common.models import Case, Finding, User
from investwatch_common.schemas import CaseOut
from sqlalchemy.orm import Session

from ..auth import get_current_user

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("", response_model=list[CaseOut])
def list_cases(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.query(Case).order_by(Case.updated_at.desc()).limit(200).all()


@router.get("/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")
    findings = []
    if case.finding_ids:
        findings = db.query(Finding).filter(Finding.id.in_(case.finding_ids)).all()
    return {
        "id": case.id,
        "primary_entity_id": case.primary_entity_id,
        "status": case.status,
        "description": case.description,
        "findings": [
            {"id": f.id, "module": f.module, "score": f.score, "document_id": f.document_id}
            for f in findings
        ],
    }


@router.get("/{case_id}/graph")
def case_graph(case_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    """Nodes/edges for the relationship graph: finfluencer - firm - domain - promo code."""
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Case not found")

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def add_node(node_id: str, label: str, node_type: str):
        nodes[node_id] = {"id": node_id, "label": label, "type": node_type}

    primary = case.primary_entity
    add_node(f"entity:{primary.id}", primary.name, "entity")

    findings = db.query(Finding).filter(Finding.id.in_(case.finding_ids or [])).all()
    for f in findings:
        doc = f.document
        doc_node = f"document:{doc.id}"
        add_node(doc_node, doc.title or doc.url, "document")
        edges.append({"source": f"entity:{primary.id}", "target": doc_node, "label": f.module})

        promo = (f.details or {}).get("promo_code")
        if promo:
            promo_node = f"promo:{promo}"
            add_node(promo_node, promo, "promo_code")
            edges.append({"source": doc_node, "target": promo_node, "label": "uses_code"})

        domain = (f.details or {}).get("domain")
        if domain:
            domain_node = f"domain:{domain}"
            add_node(domain_node, domain, "domain")
            edges.append({"source": doc_node, "target": domain_node, "label": "hosted_on"})

    return {"nodes": list(nodes.values()), "edges": edges}
