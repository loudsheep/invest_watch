from fastapi import APIRouter, Depends
from investwatch_common.db import get_db
from investwatch_common.models import Entity, User
from investwatch_common.schemas import EntityOut
from sqlalchemy.orm import Session

from ..auth import get_current_user

router = APIRouter(prefix="/api/entities", tags=["entities"])


@router.get("", response_model=list[EntityOut])
def list_entities(
    authorized: bool | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(Entity)
    if authorized is not None:
        query = query.filter(Entity.authorized == authorized)
    if q:
        query = query.filter(Entity.name.ilike(f"%{q}%"))
    return query.order_by(Entity.name).limit(500).all()
