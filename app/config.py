import os
import logging
from pathlib import Path
import cloudinary
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# --- CARI FILE .env DENGAN MENGUJIKAN BEBERAPA PATH POTENSIAL ---
current_file = Path(__file__).resolve()
possible_env_paths = [
    current_file.parent / ".env",          # Jika .env ada di folder yang sama dengan config.py
    current_file.parent.parent / ".env",   # Jika .env ada di root project (misal: app/config.py -> root/.env)
    Path.cwd() / ".env"                    # Jika .env ada di current working directory saat uvicorn dijalankan
]

env_found = False
for env_path in possible_env_paths:
    if env_path.exists():
        print(f"🔍 Ditemukan file .env di: {env_path}")
        load_dotenv(dotenv_path=env_path, override=True)
        env_found = True
        break

if not env_found:
    print(f"❌ File .env TIDAK DITEMUKAN di lokasi manapun!")
    print(f"   Current working directory saat ini: {Path.cwd()}")

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "WhatsApp Tracker")
    
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "")
    DB_PORT: str = os.getenv("DB_PORT", "")
    DB_NAME: str = os.getenv("DB_NAME", "")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    WEBHOOK_PREFIX: str = os.getenv("WEBHOOK_PREFIX", "/webhook")
    WEBHOOK_TAG: str = os.getenv("WEBHOOK_TAG", "WhatsApp Webhook")

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")

settings = Settings()

# Konfigurasi Cloudinary SDK
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

if not settings.CLOUDINARY_API_KEY:
    print("⚠️ WARNING: CLOUDINARY_API_KEY tidak terdeteksi dari .env!")
else:
    print(f"✅ Cloudinary Configured for Cloud: {settings.CLOUDINARY_CLOUD_NAME}")