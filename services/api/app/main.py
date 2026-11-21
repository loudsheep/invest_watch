import asyncio
from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from investwatch_common.logging import configure_logging

from .pubsub_bridge import listen_pubsub
from .routers import auth, calibration, cases, documents, entities, findings, health, scan, settings, system
from .socket_manager import sio

configure_logging("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(listen_pubsub())
    yield
    task.cancel()


app = FastAPI(title="InvestWatch API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:47173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(findings.router)
app.include_router(cases.router)
app.include_router(entities.router)
app.include_router(calibration.router)
app.include_router(scan.router)
app.include_router(documents.router)
app.include_router(system.router)
app.include_router(settings.router)

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
