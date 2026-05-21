import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import Config


def get_token_file_path():
    path = Path(getattr(Config, "OPENEMR_TOKEN_FILE", "data/openemr_tokens.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def utc_now():
    return datetime.now(timezone.utc)


def iso_now():
    return utc_now().isoformat(timespec="seconds")


def calculate_expires_at(expires_in):
    try:
        seconds = int(expires_in)
    except (TypeError, ValueError):
        return ""

    if seconds <= 0:
        return ""

    return (utc_now() + timedelta(seconds=seconds)).isoformat(timespec="seconds")


def load_openemr_tokens():
    path = get_token_file_path()

    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def save_openemr_tokens(token_data):
    existing = load_openemr_tokens()

    data = {
        **existing,
        **(token_data or {}),
        "updated_at": iso_now(),
    }

    path = get_token_file_path()

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    return data


def get_access_token():
    return str(load_openemr_tokens().get("access_token") or "").strip()


def get_refresh_token():
    return str(load_openemr_tokens().get("refresh_token") or "").strip()


def token_expires_at():
    data = load_openemr_tokens()

    if "expires_at" not in data:
        return ""

    value = data.get("expires_at")

    if value is None:
        return ""

    return str(value).strip()


def is_access_token_expired(buffer_seconds=120):
    expires_at = token_expires_at()

    if not expires_at:
        return False

    if expires_at in ("0", "expired", "EXPIRED"):
        return True

    try:
        parsed = datetime.fromisoformat(expires_at)
    except ValueError:
        return True

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return utc_now() >= (parsed - timedelta(seconds=buffer_seconds))


def public_token_status():
    data = load_openemr_tokens()

    access_token = str(data.get("access_token") or "")
    refresh_token = str(data.get("refresh_token") or "")
    expires_at = str(data.get("expires_at") or "")

    status = {
        "token_file": str(get_token_file_path()),
        "access_token_present": bool(access_token),
        "access_token_length": len(access_token),
        "access_token_start": access_token[:20] if access_token else "",
        "refresh_token_present": bool(refresh_token),
        "refresh_token_length": len(refresh_token),
        "expires_at": expires_at,
        "is_expired_or_near_expiry": is_access_token_expired(),
        "updated_at": data.get("updated_at"),
        "source": data.get("source"),
        "scope": data.get("scope"),
    }

    return status