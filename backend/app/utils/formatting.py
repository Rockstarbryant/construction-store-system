from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings

DISPLAY_TZ = ZoneInfo(settings.DISPLAY_TIMEZONE)


def mask_national_id(national_id: str) -> str:
    """
    Masks all but the last 3 characters, e.g. "12345678" -> "*****678".
    Never expose the full National ID in list/search views.
    """
    if len(national_id) <= 3:
        return "*" * len(national_id)
    return "*" * (len(national_id) - 3) + national_id[-3:]


def to_display_tz(dt: datetime) -> datetime:
    """Converts a timezone-aware UTC datetime to Africa/Nairobi for presentation."""
    return dt.astimezone(DISPLAY_TZ)


def next_store_number(last_number: int) -> tuple[int, str]:
    """Returns (new_number, zero_padded_string) for the next store number."""
    new_number = last_number + 1
    return new_number, f"{new_number:04d}"
