#!/usr/bin/env python3
"""Fetch writing from LessWrong + Substack and bake it into index.html at build time.

Dependency-free (stdlib only). Defensive by design: any network or parse failure
leaves index.html untouched, so the page falls back to its "no posts yet" state.
Run from the repo root (the Dockerfile does this), or: python build/fetch_posts.py
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

# Each feed: (source label shown on the page, feed URL).
# Substack: replace the subdomain once the publication exists; until then it 404s
# or returns HTML and is skipped automatically.
FEEDS = [
    ("LessWrong", "https://www.lesswrong.com/feed.xml?view=userPosts&userId=K2FpDCGQYgupb8JC8"),
    ("Substack", "https://evcode.substack.com/feed"),
]

MAX_POSTS = 6
TIMEOUT = 15
HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, os.pardir, "index.html")
UA = "evcode-site-build/1.0 (+https://evcode.dev)"


def _text(el):
    return (el.text or "").strip() if el is not None else ""


def _strip_ns(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _parse_date(raw):
    """Return (iso_yyyy_mm_dd, epoch) from an RSS/Atom date string; ("", 0) on failure."""
    raw = (raw or "").strip()
    if not raw:
        return "", 0.0
    dt = None
    try:
        dt = parsedate_to_datetime(raw)  # RFC 822 (RSS)
    except (TypeError, ValueError, IndexError):
        dt = None
    if dt is None:
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))  # ISO 8601 (Atom)
        except ValueError:
            return "", 0.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.date().isoformat(), dt.timestamp()


def _items_from(root, source):
    posts = []
    for item in root.iter():
        tag = _strip_ns(item.tag)
        if tag not in ("item", "entry"):
            continue
        title = link = date_raw = ""
        for child in item:
            ctag = _strip_ns(child.tag)
            if ctag == "title":
                title = _text(child)
            elif ctag == "link":
                # RSS: text content. Atom: href attribute (prefer rel=alternate).
                href = child.get("href")
                if href and (child.get("rel") in (None, "alternate")):
                    link = href
                elif not link:
                    link = _text(child) or href or ""
            elif ctag in ("pubDate", "published", "updated", "date") and not date_raw:
                date_raw = _text(child)
        if not title or not link:
            continue
        iso, epoch = _parse_date(date_raw)
        posts.append({"date": iso, "title": title, "url": link, "source": source, "_epoch": epoch})
    return posts


def _fetch(url):
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    with urlopen(req, timeout=TIMEOUT) as resp:
        ctype = (resp.headers.get("Content-Type") or "").lower()
        body = resp.read()
    if "xml" not in ctype and b"<rss" not in body[:200] and b"<feed" not in body[:200]:
        raise ValueError(f"not a feed (content-type: {ctype or 'unknown'})")
    return ET.fromstring(body)


def collect():
    all_posts = []
    for source, url in FEEDS:
        try:
            root = _fetch(url)
            got = _items_from(root, source)
            all_posts.extend(got)
            print(f"[fetch_posts] {source}: {len(got)} item(s)")
        except Exception as e:  # noqa: BLE001 - any failure just means skip this feed
            print(f"[fetch_posts] {source}: skipped ({e})")
    all_posts.sort(key=lambda p: p["_epoch"], reverse=True)
    for p in all_posts:
        p.pop("_epoch", None)
    return all_posts[:MAX_POSTS]


def inject(posts):
    with open(INDEX, "r", encoding="utf-8") as f:
        html = f.read()
    payload = json.dumps(posts, ensure_ascii=False)
    new_html, n = re.subn(
        r"/\*BUILD:POSTS\*/.*?/\*:BUILD\*/",
        "/*BUILD:POSTS*/" + payload.replace("\\", "\\\\") + "/*:BUILD*/",
        html,
        count=1,
        flags=re.DOTALL,
    )
    if n != 1:
        print("[fetch_posts] BUILD markers not found; leaving index.html unchanged")
        return
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"[fetch_posts] baked {len(posts)} post(s) into index.html")


def main():
    try:
        posts = collect()
    except Exception as e:  # noqa: BLE001
        print(f"[fetch_posts] collect failed, leaving page as-is ({e})")
        return 0
    try:
        inject(posts)
    except Exception as e:  # noqa: BLE001
        print(f"[fetch_posts] inject failed, leaving page as-is ({e})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
