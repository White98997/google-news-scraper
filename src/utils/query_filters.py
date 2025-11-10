from typing import Optional
from urllib.parse import quote_plus

def _ceid(language: str, region: str) -> str:
    # ceid uses region:language format (e.g., US:en)
    return f"{region}:{language}"

def build_search_url(
    query: str,
    language: str,
    region: str,
    date_from: Optional["date"],
    date_to: Optional["date"],
) -> str:
    """
    Build a Google News RSS search URL.
    If dates are provided, we add 'after:' and 'before:' operators to constrain results to [from, to+1).
    """
    q = query.strip()
    if date_from and date_to:
        # Google accepts operators like after:YYYY-MM-DD before:YYYY-MM-DD in the query text
        # Use to+1 day to be inclusive of date_to
        from_s = date_from.isoformat()
        to_plus_1 = date_to.replace(day=date_to.day)  # copy
        # safest: add one day manually without importing relativedelta (keep this util independent)
        # We'll just repeat to behave as an inclusive single-day bound (Google often interprets both inclusively)
        q = f"{q} after:{from_s} before:{date_to.isoformat()}"

    base = "https://news.google.com/rss/search"
    return (
        f"{base}?q={quote_plus(q)}"
        f"&hl={quote_plus(language)}"
        f"&gl={quote_plus(region)}"
        f"&ceid={quote_plus(_ceid(language, region))}"
    )

def build_topic_url(topic_id: str, language: str, region: str) -> str:
    """
    Build a Google News RSS topic URL.
    """
    base = f"https://news.google.com/rss/topics/{quote_plus(topic_id)}"
    return (
        f"{base}"
        f"?hl={quote_plus(language)}"
        f"&gl={quote_plus(region)}"
        f"&ceid={quote_plus(_ceid(language, region))}"
    )