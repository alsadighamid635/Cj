"""
RSS and webpage scraper for automatic knowledge acquisition.
Fetches articles from configured sources, splits them into chunks,
and stores them in the Qdrant 'cybersec_sources' collection.
"""

import hashlib
import ipaddress
import re
import requests
import feedparser
from datetime import datetime
from urllib.parse import urlparse
from utils.logger import get_logger
from utils.text import clean_html, chunk_text
from core import vectorstore
import config

logger = get_logger()

_HEADERS = {"User-Agent": "CJ-AI/1.0 (cybersecurity research assistant)"}
_TIMEOUT = 15

# SSRF protection — schemes and hosts that must never be fetched
_ALLOWED_SCHEMES = {"http", "https"}
_BLOCKED_HOSTS = re.compile(
    r"^(localhost|127\.|0\.|169\.254\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|::1|fd[0-9a-f]{2}:)",
    re.IGNORECASE,
)


def _is_safe_url(url: str) -> bool:
    """Return True only for public HTTP/HTTPS URLs (no SSRF targets)."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in _ALLOWED_SCHEMES:
            return False
        host = parsed.hostname or ""
        if _BLOCKED_HOSTS.match(host):
            return False
        # Also block raw private IP addresses
        try:
            addr = ipaddress.ip_address(host)
            if addr.is_private or addr.is_loopback or addr.is_link_local:
                return False
        except ValueError:
            pass  # hostname, not an IP — already checked by regex above
        return True
    except Exception:
        return False


def _short_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


def fetch_rss(source_id: int, source_name: str, url: str) -> int:
    """Fetch an RSS feed and store new articles. Returns item count added."""
    if not _is_safe_url(url):
        logger.warning("Blocked unsafe RSS URL: %s", url)
        return 0
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        logger.warning("RSS fetch failed for %s: %s", url, e)
        return 0

    entries = feed.get("entries", [])[:30]  # latest 30 items
    ids, docs, metas = [], [], []

    for entry in entries:
        title   = entry.get("title", "")
        summary = clean_html(entry.get("summary", entry.get("description", "")))
        link    = entry.get("link", "")
        published = ""
        if hasattr(entry, "published"):
            published = entry.get("published", "")

        if not summary or len(summary) < 60:
            continue

        # Build a readable document
        full_text = f"{title}\n\n{summary}"
        chunks = chunk_text(full_text, max_chars=600)

        for i, chunk in enumerate(chunks):
            doc_id = f"src_{source_id}_{_short_hash(link + str(i))}"
            ids.append(doc_id)
            docs.append(chunk)
            metas.append({
                "type":        "article",
                "source_id":   source_id,
                "source_name": source_name,
                "title":       title,
                "url":         link,
                "published":   published,
            })

    if ids:
        vectorstore.add_documents(config.COLLECTION_SOURCES, ids, docs, metas)
        logger.info("Stored %d chunks from '%s'", len(ids), source_name)

    return len(entries)


def fetch_webpage(source_id: int, source_name: str, url: str) -> int:
    """Scrape a plain web page and store its content."""
    if not _is_safe_url(url):
        logger.warning("Blocked unsafe page URL: %s", url)
        return 0
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        text = clean_html(resp.text)
    except Exception as e:
        logger.warning("Page fetch failed for %s: %s", url, e)
        return 0

    chunks = chunk_text(text, max_chars=600)
    if not chunks:
        return 0

    ids   = [f"page_{source_id}_{_short_hash(url + str(i))}" for i in range(len(chunks))]
    metas = [{"type": "article", "source_id": source_id,
              "source_name": source_name, "title": source_name,
              "url": url, "published": datetime.utcnow().date().isoformat()}
             for _ in chunks]

    vectorstore.add_documents(config.COLLECTION_SOURCES, ids, chunks, metas)
    logger.info("Stored %d chunks from page '%s'", len(chunks), source_name)
    return len(chunks)


def learn_from_source(source: dict) -> int:
    """Dispatch to the right fetcher based on source type."""
    src_type = source.get("type", "rss")
    if src_type == "rss":
        return fetch_rss(source["id"], source["name"], source["url"])
    return fetch_webpage(source["id"], source["name"], source["url"])
