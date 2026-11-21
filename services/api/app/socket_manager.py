from http.cookies import SimpleCookie

import socketio
from investwatch_common.config import settings
from investwatch_common.db import SessionLocal
from investwatch_common.models import User

from .auth import COOKIE_NAME, user_id_from_token

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=settings.cors_origins)


def _session_user_exists(environ: dict) -> bool:
    cookies = SimpleCookie(environ.get("HTTP_COOKIE", ""))
    if COOKIE_NAME not in cookies:
        return False
    user_id = user_id_from_token(cookies[COOKIE_NAME].value)
    if user_id is None:
        return False
    with SessionLocal() as db:
        return db.get(User, user_id) is not None


@sio.event
async def connect(sid, environ, auth=None):
    if not _session_user_exists(environ):
        raise socketio.exceptions.ConnectionRefusedError("Not authenticated")


async def emit_finding_status_changed(finding_id: int, new_status: str) -> None:
    await sio.emit("finding_status_changed", {"finding_id": finding_id, "status": new_status})


async def emit_high_risk_finding(finding: dict) -> None:
    await sio.emit("high_risk_finding", finding)


async def emit_scan_stage(
    scan_id: str, stage: str, status: str, message: str | None = None, data: dict | None = None
) -> None:
    await sio.emit(
        "scan_stage",
        {"scan_id": scan_id, "stage": stage, "status": status, "message": message, "data": data or {}},
        room=scan_id,
    )


@sio.event
async def subscribe_scan(sid, data):
    scan_id = data.get("scan_id")
    if scan_id:
        await sio.enter_room(sid, scan_id)
