"""Runtime settings editable from the admin page, stored in the app_settings table.
DEFAULTS is the single list of known keys."""
from typing import Any

from sqlalchemy.orm import Session

from .models import AppSetting

DEFAULTS: dict[str, Any] = {
    "m3_suppress_authorized_domains": True,
}


def get_setting(db: Session, key: str) -> Any:
    row = db.get(AppSetting, key)
    return DEFAULTS[key] if row is None else row.value


def get_all_settings(db: Session) -> dict[str, Any]:
    stored = {row.key: row.value for row in db.query(AppSetting).all()}
    return {key: stored.get(key, default) for key, default in DEFAULTS.items()}


def set_setting(db: Session, key: str, value: Any) -> None:
    if key not in DEFAULTS:
        raise KeyError(key)
    row = db.get(AppSetting, key)
    if row is None:
        db.add(AppSetting(key=key, value=value))
    else:
        row.value = value
    db.commit()
