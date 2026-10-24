"""Configuration and credentials helper with safe fallback mechanisms."""
import os
from pathlib import Path
try:
    import tomllib
except ImportError:
    import toml as tomllib  # type: ignore

BASE_DIR = Path(__file__).resolve().parent.parent
SECRETS_FILE = BASE_DIR / ".streamlit" / "secrets.toml"


def get_serpapi_key() -> str:
    """Retrieve SerpApi key safely from environment, secrets.toml, or empty string."""
    env_key = os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_KEY")
    if env_key:
        return env_key.strip()

    if SECRETS_FILE.exists():
        try:
            with open(SECRETS_FILE, "rb") as f:
                data = tomllib.load(f)
                return str(data.get("SERPAPI_KEY") or data.get("SERPAPI_API_KEY") or "").strip()
        except Exception:
            pass
    return ""


def save_serpapi_key(key: str) -> None:
    """Persist SerpApi key into .streamlit/secrets.toml for future sessions."""
    SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    clean_key = key.strip()
    with open(SECRETS_FILE, "w", encoding="utf-8") as f:
        f.write(f'SERPAPI_KEY = "{clean_key}"\n')
