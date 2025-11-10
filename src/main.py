import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.date_helpers import (
    parse_date,
    daterange_inclusive,
    utc_iso,
)
from utils.topic_resolver import resolve_topic_id
from utils.query_filters import build_search_url, build_topic_url
from parser.rss_parser import fetch_rss_items
from parser.article_details import enrich_article_details

def load_settings(settings_path: Path) -> Dict[str, Any]:
    if not settings_path.exists():
        raise FileNotFoundError(f"Config not found: {settings_path}")
    with settings_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def read_inputs_file(path: Optional[str]) -> List[str]:
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        print(f"[warn] inputs file not found: {path}", file=sys.stderr)
        return []
    lines = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines()]
    return [ln for ln in lines if ln]

def coalesce(*vals, default=None):
    for v in vals:
        if v is not None:
            return v
    return default

def build_tasks(cfg: Dict[str, Any], args: argparse.Namespace) -> List[Dict[str, str]]:
    """
    Creates a list of fetch tasks. Each task yields a Google News RSS URL.
    Supports:
      - query-based search (possibly day-by-day)
      - topic-based fetch
      - hashed topic fetch
    """
    language = coalesce(args.language, cfg.get("language"), "en")
    region = coalesce(args.region, cfg.get("region"), "US")
    max_items = int(coalesce(args.max_items, cfg.get("maxItems"), 200))
    fetch_details = bool(coalesce(args.fetch_details, cfg.get("fetchArticleDetails"), True))
    user_agent = coalesce(args.user_agent, cfg.get("userAgent"), None)

    # date bounds
    date_from_str = coalesce(args.date_from, cfg.get("dateFrom"))
    date_to_str = coalesce(args.date_to, cfg.get("dateTo"))
    date_from = parse_date(date_from_str) if date_from_str else None
    date_to = parse_date(date_to_str) if date_to_str else None

    # tasks holder
    tasks: List[Dict[str, str]] = []

    # Topic resolution takes precedence if provided
    topic = coalesce(args.topic, cfg.get("topic"))
    hashed_topic = coalesce(args.hashed_topic, cfg.get("hashedTopic"))

    if topic or hashed_topic:
        topic_id = resolve_topic_id(topic or hashed_topic)
        url = build_topic_url(topic_id, language, region)
        tasks.append({"type": "topic", "url": url})
        return tasks

    # query-based
    queries: List[str] = []
    if args.query:
        queries.append(args.query)
    if cfg.get("query"):
        queries.append(cfg["query"])
    # inputs file may add more queries
    queries += read_inputs_file(args.inputs)

    # Fallback if nothing specified
    if not queries:
        queries = ["technology"]

    # Day-by-day if date bounds provided; otherwise a single URL per query
    if date_from and date_to:
        for q in queries:
            for day in daterange_inclusive(date_from, date_to):
                url = build_search_url(q, language, region, day, day)
                tasks.append({"type": "search", "url": url, "query": q, "day": day.isoformat()})
    else:
        for q in queries:
            url = build_search_url(q, language, region, None, None)
            tasks.append({"type": "search", "url": url, "query": q})

    # Attach common flags
    for t in tasks:
        t["fetch_details"] = "1" if fetch_details else "0"
        t["user_agent"] = user_agent or ""
        t["language"] = language
        t["region"] = region
        t["max_items"] = str(max_items)
    return tasks

def main():
    parser = argparse.ArgumentParser(
        description="Google News Scraper - query & topic based RSS fetcher with optional article detail enrichment."
    )
    default_root = Path(__file__).resolve().parents[1]
    parser.add_argument("--config", default=str(default_root / "src" / "config" / "settings.json"), help="Path to settings.json")
    parser.add_argument("--query", help="Search query string (supports operators like intitle:, site:, after:, before:)")
    parser.add_argument("--topic", help="Predefined topic name (e.g., technology, business)")
    parser.add_argument("--hashed-topic", help="Full hashed topic id from Google News URL")
    parser.add_argument("--language", help="Language code, e.g., en")
    parser.add_argument("--region", help="Region code, e.g., US")
    parser.add_argument("--date-from", help="YYYY-MM-DD (inclusive)")
    parser.add_argument("--date-to", help="YYYY-MM-DD (inclusive)")
    parser.add_argument("--max-items", type=int, help="Maximum number of items to return")
    parser.add_argument("--no-details", dest="fetch_details", action="store_false", help="Disable article detail enrichment")
    parser.add_argument("--user-agent", help="Override HTTP User-Agent")
    parser.add_argument("--inputs", help="Path to inputs file with one query per line")
    parser.add_argument("--output", help="Output file path (JSON). If omitted, prints to stdout.")
    args = parser.parse_args()

    cfg = load_settings(Path(args.config))
    tasks = build_tasks(cfg, args)

    results: List[Dict[str, Any]] = []
    total_limit = int(tasks[0].get("max_items", "200")) if tasks else 200

    for t in tasks:
        try:
            items = fetch_rss_items(
                t["url"],
                language=t["language"],
                region=t["region"],
                user_agent=t.get("user_agent") or None,
            )
        except Exception as e:
            print(f"[error] Failed to fetch RSS: {t['url']}\n  -> {e}", file=sys.stderr)
            continue

        # Optional enrichment
        if t["fetch_details"] == "1":
            enriched: List[Dict[str, Any]] = []
            for it in items:
                try:
                    enriched.append(enrich_article_details(it, user_agent=t.get("user_agent") or None))
                except Exception as e:
                    # Keep original item on enrichment failure
                    print(f"[warn] enrich failed for {it.get('link')}: {e}", file=sys.stderr)
                    enriched.append(it)
            items = enriched

        # Append and stop if reached global limit
        for it in items:
            results.append(it)
            if len(results) >= total_limit:
                break
        if len(results) >= total_limit:
            break

    # Normalize and output
    # Ensure required fields exist
    normalized: List[Dict[str, Any]] = []
    for it in results:
        normalized.append({
            "title": it.get("title"),
            "link": it.get("link"),
            "guid": it.get("guid"),
            "source": it.get("source"),
            "sourceUrl": it.get("sourceUrl"),
            "publishedAt": it.get("publishedAt") or utc_iso(),
            "loadedUrl": it.get("loadedUrl"),
            "rssLink": it.get("rssLink"),
            "image": it.get("image"),
        })

    out_json = json.dumps(normalized, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(out_json, encoding="utf-8")
    else:
        print(out_json)

if __name__ == "__main__":
    main()