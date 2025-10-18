from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.logger import setup_logging, get_logger
from app.db import engine, Base
from app.routers import (
    organizations,
    upload,
    analytics,
    organization_analytics,
    fns,
)
from config import settings, ensure_directories

setup_logging()
logger = get_logger(__name__)
ensure_directories()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Web application for analyzing industrial enterprises in Moscow",
    docs_url=None,
    redoc_url=None,
)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(upload.router)
app.include_router(organizations.router)
app.include_router(organization_analytics.router)
app.include_router(analytics.router)
app.include_router(fns.router)


@app.get("/")
async def root_redirect():
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/analytics")
