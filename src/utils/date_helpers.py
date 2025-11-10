from datetime import datetime, timedelta, date, timezone
from typing import Iterator, Optional

def parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()

def daterange_inclusive(start: date, end: date) -> Iterator[date]:
    cur = start
    delta = timedelta(days=1)
    while cur <= end:
        yield cur
        cur += delta

def utc_iso(dt: Optional[datetime] = None) -> str:
    if dt is None:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()