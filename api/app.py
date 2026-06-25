from __future__ import annotations

import os
import time
import uuid
import logging
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from data.database import make_engine, make_session_factory, session_scope
from data.models import Base
from engine.orchestrator import RecommendationOrchestrator

logger = logging.getLogger("learning-reco")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


API_KEY = os.getenv("API_KEY", "change-me")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./learning_reco.db")


engine = make_engine(DATABASE_URL)
SessionFactory = make_session_factory(engine)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

orchestrator = RecommendationOrchestrator(cache_ttl_seconds=30)

app = FastAPI(title="Learning Recommendation Service", version="1.0.0")

# Basic in-memory metrics
METRICS = {
    "requests_total": 0,
    "errors_total": 0,
    "recommend_requests": 0,
    "feedback_requests": 0,
    "latency_ms_sum": 0.0,
}


def get_db():
    yield from session_scope(SessionFactory)


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    if x_api_key is None or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start = time.time()
    METRICS["requests_total"] += 1

    try:
        response = await call_next(request)
        return response
    except Exception as e:
        METRICS["errors_total"] += 1
        logger.exception("Unhandled error request_id=%s path=%s", request_id, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "request_id": request_id},
        )
    finally:
        elapsed_ms = (time.time() - start) * 1000.0
        METRICS["latency_ms_sum"] += elapsed_ms
        logger.info(
            "request_id=%s method=%s path=%s status=%s latency_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            getattr(locals().get("response", None), "status_code", "NA"),
            elapsed_ms,
        )


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/metrics")
def metrics():
    avg = METRICS["latency_ms_sum"] / max(1, METRICS["requests_total"])
    return {**METRICS, "latency_ms_avg": avg}


@app.get("/recommend/{user_id}")
def recommend(
    user_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_api_key),
):
    METRICS["recommend_requests"] += 1
    try:
        return orchestrator.get_recommendations(db=db, user_id=user_id, limit=limit)
    except KeyError as e:
        METRICS["errors_total"] += 1
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        METRICS["errors_total"] += 1
        raise HTTPException(status_code=400, detail=f"Bad request: {e}")


class FeedbackIn(BaseModel):
    user_id: int = Field(..., ge=1)
    content_id: int = Field(..., ge=1)
    type: str = Field(..., pattern="^(view|like|complete|dislike)$")
    rating: Optional[float] = Field(default=None, ge=1, le=5)


@app.post("/feedback")
def feedback(
    body: FeedbackIn,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_api_key),
):
    METRICS["feedback_requests"] += 1
    try:
        return orchestrator.record_feedback(
            db=db,
            user_id=body.user_id,
            content_id=body.content_id,
            interaction_type=body.type,
            rating=body.rating,
        )
    except KeyError as e:
        METRICS["errors_total"] += 1
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        METRICS["errors_total"] += 1
        raise HTTPException(status_code=400, detail=f"Bad request: {e}")