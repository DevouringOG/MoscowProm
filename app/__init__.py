"""Application package."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.db import engine, Base
from app.api import router
from app.logger import setup_logging, get_logger
from app.redis_client import redis_client
from config import settings, ensure_directories

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Ensure required directories exist
ensure_directories()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("application_starting", version=settings.app_version)
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("database_tables_created")
    except Exception as e:
        logger.error("database_tables_creation_failed", error=str(e))
    
    # Check Redis connection
    try:
        if redis_client.ping():
            logger.info("redis_connected")
        else:
            logger.warning("redis_connection_failed")
    except Exception as e:
        logger.error("redis_connection_error", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Web application for analyzing industrial enterprises in Moscow",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Include API routes
app.include_router(router, prefix="/api", tags=["API"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Root endpoint - serves the main HTML page.
    
    Args:
        request: FastAPI request object
    
    Returns:
        HTML response with the main page
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/ping")
async def ping():
    """
    Simple ping endpoint.
    
    Returns:
        Simple pong response
    """
    return {"message": "pong"}
