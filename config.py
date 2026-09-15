import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DISABLE_DB = os.getenv("DISABLE_DB", "false").lower() == "true"

if os.getenv("VERCEL"):
    UPLOAD_FOLDER = Path("/tmp/uploads")
else:
    UPLOAD_FOLDER = Path(__file__).resolve().parent / "uploads"

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")