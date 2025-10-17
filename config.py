"""Configuration management using Dynaconf."""
from pathlib import Path
from dynaconf import Dynaconf

# Base directory of the project
BASE_DIR = Path(__file__).parent

# Initialize Dynaconf
settings = Dynaconf(
    envvar_prefix="MOSPROM",
    settings_files=["settings.toml"],
    environments=True,
    load_dotenv=True,
    env_switcher="MOSPROM_ENV",
    merge_enabled=True,
)


def get_database_url() -> str:
    """Generate database URL from settings."""
    db = settings.database
    return f"postgresql://{db.user}:{db.password}@{db.host}:{db.port}/{db.name}"


def get_redis_url() -> str:
    """Generate Redis URL from settings."""
    r = settings.redis
    return f"redis://{r.host}:{r.port}/{r.db}"


def ensure_directories() -> None:
    """Ensure required directories exist."""
    directories = [
        BASE_DIR / settings.logging.log_dir,
        BASE_DIR / settings.upload.upload_dir,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
