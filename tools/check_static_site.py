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

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        for name, value in attr_map.items():
            if name in {"href", "src"} and value:
                self.links.append(value)
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

    if errors:
        print("Static site preflight failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Static site preflight passed: {len(pages)} HTML pages, required files, local links, and sitemap verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
