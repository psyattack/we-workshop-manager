from datetime import datetime
from time import localtime, strftime


WORKSHOP_DATE_FORMATS = [
    "%d %b, %Y @ %I:%M%p",
    "%d %b @ %I:%M%p",
    "%b %d, %Y @ %I:%M%p",
    "%b %d @ %I:%M%p",
    "%Y-%m-%d",
    "%d.%m.%Y",
]


def parse_workshop_date_to_timestamp(date_str: str) -> int:
    if not date_str:
        return 0

    cleaned = date_str.strip()
    for fmt in WORKSHOP_DATE_FORMATS:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            if parsed.year == 1900:
                parsed = parsed.replace(year=datetime.now().year)
            return int(parsed.timestamp())
        except ValueError:
            continue
    return 0


def format_timestamp(timestamp: float, fmt: str = "%Y-%m-%d %H:%M") -> str:
    try:
        return strftime(fmt, localtime(timestamp))
    except Exception:
        return "Unknown"