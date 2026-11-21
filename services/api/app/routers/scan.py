import uuid

from fastapi import APIRouter, Depends
from investwatch_common.models import User
from investwatch_common.schemas import ScanRequest

from ..auth import get_current_user
from ..celery_app import celery_app

router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.post("")
def scan_url(payload: ScanRequest, _user: User = Depends(get_current_user)):
    """Trigger an on-demand scan. Pipeline stages are streamed over Socket.io
    on a room named after the returned scan_id."""
    scan_id = str(uuid.uuid4())
    celery_app.send_task(
        "scraper_worker.tasks.scan_url_now",
        args=[payload.url, scan_id],
    )
    return {"scan_id": scan_id}
