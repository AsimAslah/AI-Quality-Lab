from __future__ import annotations

import logging
import re
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.api import router
from app.config import ROOT, get_settings
from app.database import Base, SessionLocal, engine
from app.models import EvaluationRun
from app.pipeline import process_evaluation
from app.security import hash_owner_token, new_owner_token


settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("ai-quality-lab")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        interrupted = db.scalars(
            select(EvaluationRun).where(EvaluationRun.status.in_(["queued", "running"]))
        ).all()
        for run in interrupted:
            threading.Thread(target=process_evaluation, args=(run.id, True), daemon=True).start()
    yield


app = FastAPI(
    title="AI Quality Lab API", version="1.0.0", docs_url="/api/docs" if not settings.is_production else None,
    redoc_url=None, lifespan=lifespan,
)


@app.middleware("http")
async def session_and_security(request: Request, call_next):
    workspace_key = request.headers.get("X-Workspace-Key")
    if workspace_key and not re.fullmatch(r"[A-Za-z0-9_-]{24,160}", workspace_key):
        return JSONResponse(status_code=400, content={"detail": "Invalid workspace access key"})
    cookie_token = request.cookies.get(settings.cookie_name)
    token = workspace_key or cookie_token
    created = bool(workspace_key and workspace_key != cookie_token)
    if not token or len(token) < 24:
        token = new_owner_token()
        created = True
    request.state.owner_hash = hash_owner_token(token)
    response = await call_next(request)
    if created:
        response.set_cookie(
            settings.cookie_name, token, httponly=True, secure=settings.is_production,
            samesite="lax", max_age=60 * 60 * 24 * 365, path="/",
        )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(_request: Request, exc: RequestValidationError):
    errors = [
        {"field": ".".join(str(item) for item in error["loc"] if item != "body"), "message": error["msg"]}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": "Please correct the highlighted fields.", "errors": errors})


app.include_router(router)

dist = ROOT / "dist"
assets = dist / "assets"
if assets.exists():
    app.mount("/assets", StaticFiles(directory=assets), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
def serve_spa(full_path: str):
    index = dist / "index.html"
    candidate = (dist / full_path).resolve()
    if candidate.is_file() and dist.resolve() in candidate.parents:
        return FileResponse(candidate)
    if index.exists():
        return FileResponse(index)
    return JSONResponse(
        status_code=503,
        content={"detail": "Frontend build is unavailable. Run npm install && npm run build."},
    )
