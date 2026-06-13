from datetime import datetime
import pytz

_UTC = pytz.utc
_ART = pytz.timezone("America/Argentina/Buenos_Aires")

DAYS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MONTHS_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def utc_to_art(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = _UTC.localize(dt)
    return dt.astimezone(_ART)


def parse_iso(iso_str: str) -> datetime:
    """Parse ISO 8601 string (with or without tz) to UTC-aware datetime."""
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(iso_str, fmt)
            if dt.tzinfo is None:
                dt = _UTC.localize(dt)
            return dt
        except ValueError:
            continue
    raise ValueError(f"No se pudo parsear la fecha: {iso_str!r}")


def format_time(iso_str: str) -> str:
    """Return 'HH:MM' in Argentina time."""
    return utc_to_art(parse_iso(iso_str)).strftime("%H:%M")


def format_date_short(iso_str: str) -> str:
    """Return 'DD/MM' in Argentina time."""
    return utc_to_art(parse_iso(iso_str)).strftime("%d/%m")


def format_datetime(iso_str: str) -> str:
    """Return 'lunes 12/06 a las 18:00 hs' in Argentina time."""
    dt = utc_to_art(parse_iso(iso_str))
    day_name = DAYS_ES[dt.weekday()]
    return f"{day_name} {dt.strftime('%d/%m')} a las {dt.strftime('%H:%M')} hs"


def today_str_art() -> str:
    """Current date in Argentina as 'YYYY-MM-DD'."""
    return datetime.now(_ART).strftime("%Y-%m-%d")
