"""Vercel Serverless Function entry point for FastAPI."""
import sys
from pathlib import Path

# Add root of scholar_dashboard to sys.path so core and server modules resolve
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from server import app
