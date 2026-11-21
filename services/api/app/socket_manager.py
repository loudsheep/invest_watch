import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


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
