import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "WhatsApp Tracker")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    WEBHOOK_PREFIX: str = os.getenv("WEBHOOK_PREFIX", "/webhook")
    WEBHOOK_TAG: str = os.getenv("WEBHOOK_TAG", "WhatsApp Webhook")

settings = Settings()