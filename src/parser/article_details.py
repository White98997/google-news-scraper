from typing import Dict, Any, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

def _headers(user_agent: Optional[str]) -> Dict[str, str]:
    return {
        "User-Agent": user_agent
        or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    }

def _extract_og(soup: BeautifulSoup, prop: str) -> Optional[str]:
    tag = soup.find("meta", attrs={"property": prop})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None

def enrich_article_details(item: Dict[str, Any], user_agent: Optional[str] = None) -> Dict[str, Any]:
    """
    Resolve redirects to get the final article URL and try to extract a better image from OG tags.
    Non-fatal: returns the original item on any failure.
    """
    link = item.get("link")
    if not link:
        return item

    try:
        resp = requests.get(link, headers=_headers(user_agent), timeout=20, allow_redirects=True)
        resp.raise_for_status()
        final_url = str(resp.url)
        item["loadedUrl"] = final_url

        # Try to extract OG meta for improved image/title
        soup = BeautifulSoup(resp.text, "html.parser")
        og_image = _extract_og(soup, "og:image")
        if og_image:
            item["image"] = og_image

        # Sometimes source domain is more accurate from the final URL
        parsed = urlparse(final_url)
        item["sourceUrl"] = f"{parsed.scheme}://{parsed.netloc}"
        return item
    except Exception:
        # Best-effort: keep original item intact on errors
        return item