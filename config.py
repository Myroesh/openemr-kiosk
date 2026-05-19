import os
from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    OPENEMR_BASE_URL = os.getenv("OPENEMR_BASE_URL")
    OPENEMR_SITE = os.getenv("OPENEMR_SITE", "default")
    OPENEMR_CLIENT_ID = os.getenv("OPENEMR_CLIENT_ID")
    OPENEMR_CLIENT_SECRET = os.getenv("OPENEMR_CLIENT_SECRET")
    OPENEMR_USERNAME = os.getenv("OPENEMR_USERNAME")
    OPENEMR_PASSWORD = os.getenv("OPENEMR_PASSWORD")
    OPENEMR_ACCESS_TOKEN = os.getenv("OPENEMR_ACCESS_TOKEN")
    OPENEMR_REFRESH_TOKEN = os.getenv("OPENEMR_REFRESH_TOKEN")
    OPENEMR_VERIFY_SSL = os.getenv("OPENEMR_VERIFY_SSL", "true").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

    PROFESSIONALS = [
        "Dra. Ana Maria Saavedra",
        "Dra. Evelyn vidal",
        "Dra. Katherine",
        "Dr. Luis",
    ]

    KIOSK_DB_PATH = os.getenv("KIOSK_DB_PATH", "data/kiosk.db")