"""Background task bridging Redis pub/sub (ai-worker -> api) to Socket.io clients."""
import asyncio
import json

from investwatch_common.logging import get_logger
from investwatch_common.redis_client import HIGH_RISK_CHANNEL, get_redis

from .socket_manager import emit_high_risk_finding, emit_scan_stage

logger = get_logger(__name__)

SCAN_STAGE_CHANNEL = "scan:stages"


async def listen_pubsub() -> None:
    redis_client = get_redis()
    pubsub = redis_client.pubsub()
    pubsub.subscribe(HIGH_RISK_CHANNEL, SCAN_STAGE_CHANNEL)

    loop = asyncio.get_event_loop()
    while True:
        message = await loop.run_in_executor(None, pubsub.get_message, True, 1.0)
        if message is None or message.get("type") != "message":
            await asyncio.sleep(0.05)
            continue
        try:
            payload = json.loads(message["data"])
        except (TypeError, ValueError):
            continue

        if message["channel"] == HIGH_RISK_CHANNEL:
            await emit_high_risk_finding(payload)
        elif message["channel"] == SCAN_STAGE_CHANNEL:
            await emit_scan_stage(
                payload["scan_id"],
                payload["stage"],
                payload["status"],
                payload.get("message"),
                payload.get("data"),
            )
