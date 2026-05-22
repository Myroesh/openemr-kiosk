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
    OPENEMR_DEFAULT_FACILITY = os.getenv(
        "OPENEMR_DEFAULT_FACILITY",
        "Centro Neuropsicologico Saavedra",
    )
    OPENEMR_DEFAULT_PC_CATID = os.getenv("OPENEMR_DEFAULT_PC_CATID", "5")

    OPENEMR_VISIT_CATEGORY_MAP = {
        "Consulta Inicial": os.getenv(
            "OPENEMR_CAT_CONSULTA_INICIAL",
            OPENEMR_DEFAULT_PC_CATID,
        ),
        "Sesión": os.getenv(
            "OPENEMR_CAT_SESION",
            OPENEMR_DEFAULT_PC_CATID,
        ),
        "Revisión de resultados": os.getenv(
            "OPENEMR_CAT_REVISION_RESULTADOS",
            OPENEMR_DEFAULT_PC_CATID,
        ),
        "Test": os.getenv(
            "OPENEMR_CAT_TEST",
            OPENEMR_DEFAULT_PC_CATID,
        ),
        "Entrevista con los padres": os.getenv(
            "OPENEMR_CAT_ENTREVISTA_PADRES",
            OPENEMR_DEFAULT_PC_CATID,
        ),
    }

    OPENEMR_DEFAULT_FACILITY_ID = os.getenv("OPENEMR_DEFAULT_FACILITY_ID", "3")
    OPENEMR_DEFAULT_BILLING_FACILITY = os.getenv(
        "OPENEMR_DEFAULT_BILLING_FACILITY",
        "3",
    )
    OPENEMR_DEFAULT_PROVIDER_ID = os.getenv("OPENEMR_DEFAULT_PROVIDER_ID", "1")
    OPENEMR_DEFAULT_POS_CODE = os.getenv("OPENEMR_DEFAULT_POS_CODE", "0")
    OPENEMR_DEFAULT_CLASS_CODE = os.getenv("OPENEMR_DEFAULT_CLASS_CODE", "AMB")
    OPENEMR_DEFAULT_SENSITIVITY = os.getenv(
        "OPENEMR_DEFAULT_SENSITIVITY",
        "normal",
    )
    OPENEMR_TOKEN_FILE = os.getenv(
        "OPENEMR_TOKEN_FILE",
        "data/openemr_tokens.json",
    )
    OPENEMR_OAUTH_REDIRECT_URI = os.getenv("OPENEMR_OAUTH_REDIRECT_URI")
    OPENEMR_OAUTH_SCOPES = os.getenv(
        "OPENEMR_OAUTH_SCOPES",
        "openid offline_access api:oemr user/patient.read user/patient.write user/encounter.read user/encounter.write user/practitioner.read user/facility.read user/user.read",
    )
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

    PROFESSIONALS = [
    "Dra. Ana Saavedra",
    "Dra. Evelyn Mejia Patiño",
    "Dra. Katherine Oliveira",
    "Dr. Jose Montaño",
    "Dr. Hernan Hinojosa",
    ]

    KIOSK_DB_PATH = os.getenv("KIOSK_DB_PATH", "data/kiosk.db")