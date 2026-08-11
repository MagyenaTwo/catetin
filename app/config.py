import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "WhatsApp Tracker")
    
    # Ambil komponen dari .env
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT")
    DB_NAME: str = os.getenv("DB_NAME")
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # Buat DATABASE_URL otomatis untuk Supabase / PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    WEBHOOK_PREFIX: str = os.getenv("WEBHOOK_PREFIX", "/webhook")
    WEBHOOK_TAG: str = os.getenv("WEBHOOK_TAG", "WhatsApp Webhook")

settings = Settings()