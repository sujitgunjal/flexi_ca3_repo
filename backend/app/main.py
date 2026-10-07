from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.decisions import router as decisions_router
from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.api.models import router as models_router
from app.api.requests import router as requests_router
from app.database.database import initialize_database


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="LLM Resource Optimization Gateway",
    description="Multi-agent LLM routing and resource optimization gateway.",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)

app.include_router(
    chat_router,
    prefix="/chat",
    tags=["Chat"],
)

app.include_router(
    decisions_router,
    prefix="/decisions",
    tags=["Decisions"],
)

app.include_router(
    models_router,
    prefix="/models",
    tags=["Models"],
)

app.include_router(
    metrics_router,
    prefix="/metrics",
    tags=["Metrics"],
)

app.include_router(
    requests_router,
    prefix="/requests",
    tags=["Requests"],
)


@app.get("/", tags=["Root"])
def root():
    return {
        "name": "LLM Resource Optimization Gateway",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }