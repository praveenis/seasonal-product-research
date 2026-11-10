#!/usr/bin/env python3
"""Check local website links and deployment-critical static files."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
AFFILIATE_ARTICLE_DIR = ROOT / "articles" / "affiliate"
AFFILIATE_EXPORT_MARKER = "<!-- SBRP APPROVED AFFILIATE EXPORT -->"
SEASONS_DIR = ROOT / "seasons"
SEASONS_HOST = "seasons.sbrp.app"
SEASONS_REQUIRED_FILES = ("index.html", "robots.txt", "sitemap.xml")
THANKSGIVING_DIR = SEASONS_DIR / "thanksgiving"
THANKSGIVING_REQUIRED_FILES = (
    "index.html", "host-gifts.html", "spouse-gifts.html", "grandparents-gifts.html",
    "kids-gifts-boys-5-10.html", "kids-gifts-girls-5-10.html", "styles.css",
    "games/index.html", "movie-night/index.html", "recipes/index.html", "gratitude/index.html",
)
REQUIRED_FILES = (
    "index.html", "catalog.html", "about.html", "contact.html",
    "affiliate-disclosure.html", "google-ads.html", "privacy-policy.html",
    "terms-of-service.html", "robots.txt", "sitemap.xml", "CNAME",
)


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.affiliate_links: list[tuple[str, set[str]]] = []
        self.canonical: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        for name, value in attr_map.items():
            if name in {"href", "src"} and value:
                self.links.append(value)
        if tag == "link" and "canonical" in (attr_map.get("rel") or "").lower().split():
            self.canonical = attr_map.get("href")
        if attr_map.get("data-affiliate-link") == "true":
            self.affiliate_links.append((attr_map.get("href") or "", set((attr_map.get("rel") or "").lower().split())))


def local_target(page: Path, raw_url: str) -> Path | None:
    parts = urlsplit(raw_url)
    if raw_url.startswith("//"):
        return None
    if parts.scheme and (parts.scheme != "https" or parts.netloc != "sbrp.app"):
        return None
    if parts.netloc and parts.netloc != "sbrp.app":
        return None
    path = unquote(parts.path)
    if not path:
        return None
    target = ((ROOT / path.lstrip("/")) if parts.netloc else (page.parent / path)).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        raise ValueError(f"link escapes site root: {raw_url}") from None
    if target.is_dir():
        target /= "index.html"
    return target


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    if (AFFILIATE_ARTICLE_DIR / "drafts").exists():
        errors.append("private affiliate drafts must not be stored under the public site root: articles/affiliate/drafts")

    pages = sorted(ROOT.rglob("*.html"))
    for page in pages:
        collector = LinkCollector()
        try:
            page_html = page.read_text(encoding="utf-8")
            collector.feed(page_html)
        except (OSError, UnicodeError) as exc:
            errors.append(f"cannot read {page.relative_to(ROOT)}: {exc}")
            continue
        try:
            page.relative_to(AFFILIATE_ARTICLE_DIR)
            is_affiliate_article = page.name != "index.html"
        except ValueError:
            is_affiliate_article = False
        if is_affiliate_article and AFFILIATE_EXPORT_MARKER not in page_html:
            errors.append(f"affiliate page lacks the approved-export marker: {page.relative_to(ROOT)}")
        if collector.affiliate_links:
            if not is_affiliate_article:
                errors.append(f"affiliate destination appears outside the affiliate article area: {page.relative_to(ROOT)}")
            if "affiliate-note" not in page_html or "affiliate-disclosure.html" not in page_html:
                errors.append(f"affiliate links need a nearby disclosure and a link to the disclosure page: {page.relative_to(ROOT)}")
            for href, rel_values in collector.affiliate_links:
                required_rel = {"sponsored", "nofollow", "noopener", "noreferrer"}
                if not href or not required_rel.issubset(rel_values):
                    errors.append(f"affiliate link is missing its destination or required rel values: {page.relative_to(ROOT)}")
        for url in collector.links:
            try:
                target = local_target(page, url)
            except ValueError as exc:
                errors.append(f"{page.relative_to(ROOT)}: {exc}")
                continue
            if target is not None and not target.is_file():
                errors.append(f"{page.relative_to(ROOT)}: missing local target {url}")

    cname_path = ROOT / "CNAME"
    if cname_path.is_file() and cname_path.read_text(encoding="utf-8").strip() != "sbrp.app":
        errors.append("CNAME must remain sbrp.app; preview setup must not change production DNS")

    sitemap_path = ROOT / "sitemap.xml"
    if sitemap_path.is_file():
        try:
            sitemap = ET.parse(sitemap_path).getroot()
            namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
            locations = [node.text for node in sitemap.findall(f"{namespace}url/{namespace}loc")]
            if not locations:
                errors.append("sitemap.xml has no URL entries")
            for location in locations:
                if not location:
                    errors.append("sitemap.xml contains an empty URL")
                    continue
                parts = urlsplit(location)
                if parts.scheme != "https" or parts.netloc != "sbrp.app":
                    errors.append(f"unexpected sitemap URL: {location}")
                    continue
                target = (ROOT / unquote(parts.path.lstrip("/"))).resolve()
                if target.is_dir():
                    target /= "index.html"
                if not target.is_file():
                    errors.append(f"sitemap URL has no local page: {location}")
        except ET.ParseError as exc:
            errors.append(f"invalid sitemap.xml: {exc}")

    for relative in SEASONS_REQUIRED_FILES:
        if not (SEASONS_DIR / relative).is_file():
            errors.append(f"missing seasonal site file: seasons/{relative}")
    for relative in THANKSGIVING_REQUIRED_FILES:
        if not (THANKSGIVING_DIR / relative).is_file():
            errors.append(f"missing Thanksgiving season file: seasons/thanksgiving/{relative}")
    seasons_sitemap = SEASONS_DIR / "sitemap.xml"
    if seasons_sitemap.is_file():
        try:
            sitemap = ET.parse(seasons_sitemap).getroot()
            namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
            locations = [node.text for node in sitemap.findall(f"{namespace}url/{namespace}loc")]
            seasons_pages = sorted(SEASONS_DIR.rglob("*.html"))
            expected: set[str] = set()
            for page in seasons_pages:
                relative = page.relative_to(SEASONS_DIR).as_posix()
                if relative == "index.html":
                    url_path = ""
                elif relative.endswith("/index.html"):
                    url_path = relative[: -len("index.html")]
                else:
                    url_path = relative
                expected_url = f"https://{SEASONS_HOST}/{url_path}"
                expected.add(expected_url)
                collector = LinkCollector()
                collector.feed(page.read_text(encoding="utf-8"))
                expected_canonical = expected_url
                if collector.canonical != expected_canonical:
                    errors.append(f"Seasonal page has incorrect canonical URL: {page.relative_to(ROOT)}")
            if set(locations) != expected:
                errors.append("Seasons sitemap must list exactly the seasonal site's canonical HTML pages")
            robots_text = (SEASONS_DIR / "robots.txt").read_text(encoding="utf-8")
            if f"Sitemap: https://{SEASONS_HOST}/sitemap.xml" not in robots_text:
                errors.append("Seasons robots.txt must reference its site-level sitemap")
            for location in locations:
                if not location:
                    errors.append("Seasons sitemap.xml contains an empty URL")
                    continue
                parts = urlsplit(location)
                if parts.scheme != "https" or parts.netloc != SEASONS_HOST:
                    errors.append(f"unexpected seasonal sitemap URL: {location}")
                    continue
                target_path = unquote(parts.path).lstrip("/") or "index.html"
                target = (SEASONS_DIR / target_path).resolve()
                if target.is_dir():
                    target /= "index.html"
                if not target.is_file():
                    errors.append(f"Seasonal sitemap URL has no local page: {location}")
        except (ET.ParseError, OSError, UnicodeError) as exc:
            errors.append(f"invalid seasonal sitemap or site metadata: {exc}")

    if errors:
        print("Static site preflight failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Static site preflight passed: {len(pages)} HTML pages, required files, local links, and sitemap verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
