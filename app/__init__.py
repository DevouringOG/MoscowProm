"""Application package."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.logger import setup_logging, get_logger
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
    
    yield
    
    # Shutdown
    logger.info("application_shutting_down")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Web application for analyzing industrial enterprises in Moscow",
    docs_url=None,  # Disable API docs
    redoc_url=None,  # Disable ReDoc
    lifespan=lifespan,
)

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


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
