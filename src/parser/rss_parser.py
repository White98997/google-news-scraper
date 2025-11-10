import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

import feedparser
import requests

def _headers(user_agent: Optional[str]) -> Dict[str, str]:
    return {
        "User-Agent": user_agent
        or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    }

def _guess_source_domain(link: Optional[str]) -> Optional[str]:
    if not link:
        return None
    try:
        return f"{urlparse(link).scheme}://{urlparse(link).netloc}"
    except Exception:
        return None

def fetch_rss_items(url: str, language: str, region: str, user_agent: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetches and parses a Google News RSS feed URL and normalizes entries.
    """
    # Some hosts dislike direct feedparser requests; prefetch bytes with requests for reliability.
    resp = requests.get(url, headers=_headers(user_agent), timeout=20)
    resp.raise_for_status()
    parsed = feedparser.parse(resp.content)

    items: List[Dict[str, Any]] = []
    for e in parsed.entries:
        # Common fields from Google News RSS
        title = getattr(e, "title", None)
        link = getattr(e, "link", None)
        guid = getattr(e, "id", None) or getattr(e, "guid", None)
        published = getattr(e, "published", None) or getattr(e, "updated", None)

        # Source sometimes appears in 'source' or 'source' dict
        source_name = None
        try:
            # Some feeds have e.source.title
            source_name = getattr(getattr(e, "source", None), "title", None)
        except Exception:
            source_name = None

        # Thumbnail / media content if available
        image_url = None
        media_content = getattr(e, "media_content", None)
        if isinstance(media_content, list) and media_content:
            image_url = media_content[0].get("url")

        # Fallback from links with rel="enclosure" or 'media_thumbnail'
        if not image_url:
            thumbs = getattr(e, "media_thumbnail", None)
            if isinstance(thumbs, list) and thumbs:
                image_url = thumbs[0].get("url")

        items.append(
            {
                "title": title,
                "link": link,
                "guid": guid,
                "source": source_name,
                "sourceUrl": _guess_source_domain(link),
                "publishedAt": published,
                "loadedUrl": None,  # to be filled by enrichment
                "rssLink": url,
                "image": image_url,
                "_fetchedAt": int(time.time()),
            }
        )
    return items