"""Registry sync: pulls every provider, falls back to the committed snapshot for a
provider that is unreachable, and upserts entities, aliases and identifiers."""
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
from investwatch_common.logging import get_logger
from investwatch_common.models import AppSetting, Entity, EntityAlias
from sqlalchemy.orm import Session

from .knf import PROVIDERS
from .names import normalize

logger = get_logger(__name__)

DATA_DIR = Path("/app/data")
CURATED_PATH = DATA_DIR / "registry_seed.json"
SNAPSHOT_PATH = DATA_DIR / "registry_knf.json"
LAST_SYNC_KEY = "registry_last_sync"
NAME_MAX = 255


def _load_snapshot() -> dict[str, list[dict]]:
    if not SNAPSHOT_PATH.exists():
        return {}
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8")).get("providers", {})


def collect(live: bool = True) -> tuple[dict[str, list[dict]], dict[str, str]]:
    """Returns records per provider and the origin ("live" or "snapshot") of each."""
    snapshot = _load_snapshot()
    records: dict[str, list[dict]] = {}
    origin: dict[str, str] = {}
    with httpx.Client() as client:
        for name, fetch in PROVIDERS.items():
            if live:
                try:
                    records[name] = fetch(client)
                    origin[name] = "live"
                    continue
                except Exception as exc:
                    logger.warning("registry_provider_failed", provider=name, error=str(exc))
            records[name] = snapshot.get(name, [])
            origin[name] = "snapshot"
    return records, origin


class _Index:
    def __init__(self, db: Session):
        self.db = db
        self.by_key: dict[str, Entity] = {}
        for entity in db.query(Entity).all():
            self._add(entity.name, entity)
            for alias in entity.aliases:
                self._add(alias.alias, entity)

    def _add(self, name: str, entity: Entity) -> None:
        key = normalize(name)
        if key:
            self.by_key.setdefault(key, entity)

    def find(self, record: dict) -> Entity | None:
        for name in [record["name"], *record.get("aliases", [])]:
            if (entity := self.by_key.get(normalize(name))) is not None:
                return entity
        return None

    def register(self, entity: Entity, names: list[str]) -> None:
        for name in names:
            self._add(name, entity)


def _merge_list(current: list[str] | None, extra: list[str]) -> list[str]:
    return sorted({*(current or []), *extra})


def apply_records(db: Session, records: list[dict], index: _Index) -> tuple[int, int]:
    created = updated = 0
    for record in records:
        record = {**record, "name": record["name"][:NAME_MAX], "aliases": [a[:NAME_MAX] for a in record.get("aliases", [])]}
        entity = index.find(record)
        if entity is None:
            entity = Entity(
                name=record["name"],
                type=record.get("type"),
                authorized=record.get("authorized"),
                source=record.get("source"),
                nip=record.get("nip"),
                krs=record.get("krs"),
                domains=record.get("domains", []),
            )
            db.add(entity)
            db.flush()
            created += 1
        else:
            if record.get("authorized") is False and entity.authorized:
                continue  # a warning-list name collision never flips an authorized firm
            entity.nip = entity.nip or record.get("nip")
            entity.krs = entity.krs or record.get("krs")
            entity.domains = _merge_list(entity.domains, record.get("domains", []))
            if record.get("authorized") and not entity.authorized:
                entity.authorized = True
                entity.type = record.get("type") or entity.type
            updated += 1

        known = {a.alias for a in entity.aliases}
        for alias in record.get("aliases", []):
            if alias not in known and alias != entity.name:
                db.add(EntityAlias(entity_id=entity.id, alias=alias))
        index.register(entity, [record["name"], *record.get("aliases", [])])
    db.commit()
    return created, updated


def run(db: Session, live: bool = True) -> dict:
    curated = []
    if CURATED_PATH.exists():
        curated = json.loads(CURATED_PATH.read_text(encoding="utf-8")).get("entities", [])
    records, origin = collect(live)

    index = _Index(db)
    created = updated = 0
    for batch in [curated, *records.values()]:
        try:
            c, u = apply_records(db, batch, index)
        except Exception:
            db.rollback()
            logger.exception("registry_batch_failed")
            continue
        created, updated = created + c, updated + u

    summary = {
        "at": datetime.now(UTC).isoformat(),
        "created": created,
        "updated": updated,
        "providers": {name: {"records": len(items), "origin": origin[name]} for name, items in records.items()},
    }
    row = db.get(AppSetting, LAST_SYNC_KEY)
    if row is None:
        db.add(AppSetting(key=LAST_SYNC_KEY, value=summary))
    else:
        row.value = summary
    db.commit()
    logger.info("registry_sync_complete", **{k: v for k, v in summary.items() if k != "providers"})
    return summary
