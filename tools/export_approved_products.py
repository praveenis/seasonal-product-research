#!/usr/bin/env python3
"""Validate editorially approved product research and export public static pages.

The exporter intentionally accepts a narrow, non-commercial schema. It does not
export prices, offers, sales claims, affiliate links, or private engine records.
Run without --publish to validate only; --publish is the explicit write step.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_JSON = ROOT / "data" / "approved-products.json"
PRODUCT_DIR = ROOT / "products" / "approved"
SEASONS = {"winter", "spring", "summer", "fall", "holiday", "year-round"}
REQUIRED = {
    "slug", "title", "category", "summary", "description", "seasons",
    "buying_criteria", "research_questions", "sources", "editorial_approved",
    "editorial_approved_by", "editorial_approved_on",
}


def fail(message: str) -> None:
    raise ValueError(message)


def validate_record(record: object, index: int) -> dict:
    where = f"records[{index}]"
    if not isinstance(record, dict):
        fail(f"{where} must be an object")
    missing = REQUIRED - record.keys()
    if missing:
        fail(f"{where} is missing: {', '.join(sorted(missing))}")
    if record["editorial_approved"] is not True:
        fail(f"{where} is not explicitly editorially approved")
    slug = record["slug"]
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        fail(f"{where}.slug must be lowercase kebab-case")
    for field in ("title", "category", "summary", "description", "editorial_approved_by"):
        if not isinstance(record[field], str) or not record[field].strip():
            fail(f"{where}.{field} must be a non-empty string")
    if len(record["summary"]) > 220:
        fail(f"{where}.summary must be 220 characters or fewer")
    for field in ("seasons", "buying_criteria", "research_questions", "sources"):
        if not isinstance(record[field], list) or not record[field]:
            fail(f"{where}.{field} must be a non-empty array")
    if any(not isinstance(s, str) or s not in SEASONS for s in record["seasons"]):
        fail(f"{where}.seasons may only contain: {', '.join(sorted(SEASONS))}")
    for field in ("buying_criteria", "research_questions"):
        if any(not isinstance(value, str) or not value.strip() for value in record[field]):
            fail(f"{where}.{field} entries must be non-empty strings")
    for source in record["sources"]:
        if not isinstance(source, dict) or not {"name", "url", "accessed_on"} <= source.keys():
            fail(f"{where}.sources entries require name, url, and accessed_on")
        if (not isinstance(source["name"], str) or not source["name"].strip()
                or not isinstance(source["url"], str)
                or urlparse(source["url"]).scheme != "https"
                or not urlparse(source["url"]).netloc):
            fail(f"{where}.sources require a name and HTTPS URL")
        try:
            date.fromisoformat(source["accessed_on"])
        except (TypeError, ValueError):
            fail(f"{where}.sources accessed_on must be YYYY-MM-DD")
    try:
        date.fromisoformat(record["editorial_approved_on"])
    except (TypeError, ValueError):
        fail(f"{where}.editorial_approved_on must be YYYY-MM-DD")
    return {key: record[key] for key in sorted(record) if key in REQUIRED | {"updated_on"}}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_page(record: dict) -> str:
    title = esc(record["title"])
    summary = esc(record["summary"])
    slug = esc(record["slug"])
    category = esc(record["category"])
    criteria = "\n".join(f"<li>{esc(item)}</li>" for item in record["buying_criteria"])
    questions = "\n".join(f"<li>{esc(item)}</li>" for item in record["research_questions"])
    sources = "\n".join(
        f'<li><a href="{esc(source["url"])}" rel="noopener noreferrer">{esc(source["name"])}</a> '
        f'(accessed {esc(source["accessed_on"])})</li>' for source in record["sources"]
    )
    description = esc(record["description"])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{summary}"><meta name="theme-color" content="#0c1715">
<link rel="canonical" href="https://sbrp.app/products/approved/{slug}.html"><meta property="og:type" content="article">
<meta property="og:title" content="{title} research | SBRP"><meta property="og:description" content="{summary}">
<meta property="og:url" content="https://sbrp.app/products/approved/{slug}.html"><title>{title} research | SBRP</title>
<link rel="stylesheet" href="../styles.css"><link rel="stylesheet" href="../catalog.css"></head><body>
<header class="site-header"><a class="brand" href="../index.html" aria-label="SBRP home"><span class="brand-mark">S</span><span>SBRP</span></a>
<nav class="nav" aria-label="Main navigation"><a href="../catalog.html">Product ideas</a><a href="../guides/index.html">Guides</a><a href="../affiliate-disclosure.html">Disclosure</a></nav></header>
<main><section class="sub-hero product-hero"><div class="sub-hero-copy"><p class="eyebrow">Research brief · {category}</p><h1>{title}</h1><p class="hero-lede">{summary}</p></div></section>
<section class="container product-content"><article><p class="demo-stamp">EDITORIALLY REVIEWED RESEARCH · This page is not a product listing, sales forecast, or endorsement.</p>
<p>{description}</p><h2>What to compare</h2><ul>{criteria}</ul><h2>Research questions</h2><ul>{questions}</ul>
<h2>Sources</h2><ul>{sources}</ul><p class="availability-note">No retailer offer, price, inventory, or sales claim is published on this page.</p></article>
<aside class="product-aside"><h2>Research context</h2><p>Category: {category}<br>Seasonality: {esc(", ".join(record["seasons"]))}</p>
<p>Evidence supports investigation only. Verify any specific product, supplier, claims, and marketplace rules before listing.</p>
<a class="text-link dark-link" href="../catalog.html">← Back to product ideas</a></aside></section></main>
<footer class="site-footer container"><div><a class="brand footer-brand" href="../index.html"><span class="brand-mark">S</span><span>SBRP</span></a><p>Discover Trends. Validate Products. Grow Smarter.</p></div>
<div class="footer-links"><a href="../about.html">About</a><a href="../contact.html">Contact</a><a href="../affiliate-disclosure.html">Affiliate disclosure</a><a href="../privacy-policy.html">Privacy</a><a href="../terms-of-service.html">Terms</a></div><p class="copyright">© 2026 SBRP</p></footer></body></html>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON file containing an object with a records array")
    parser.add_argument("--publish", action="store_true", help="write approved JSON and crawlable product pages")
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("records"), list) or not payload["records"]:
            fail("input must be an object containing a non-empty records array")
        records = [validate_record(record, index) for index, record in enumerate(payload["records"])]
        slugs = [record["slug"] for record in records]
        if len(slugs) != len(set(slugs)):
            fail("record slugs must be unique")
        if not args.publish:
            print(f"Validated {len(records)} approved records. No files written; pass --publish to export.")
            return 0
        sitemap = ROOT / "sitemap.xml"
        tree = None
        urlset = None
        namespace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        known = set()
        if sitemap.exists():
            import xml.etree.ElementTree as ET
            tree = ET.parse(sitemap)
            urlset = tree.getroot()
            known = {node.findtext(f"{namespace}loc") for node in urlset.findall(f"{namespace}url")}
        PUBLIC_JSON.parent.mkdir(parents=True, exist_ok=True)
        PRODUCT_DIR.mkdir(parents=True, exist_ok=True)
        destinations = [PRODUCT_DIR / f"{record['slug']}.html" for record in records]
        for destination in destinations:
            if destination.exists() and "<!-- SBRP APPROVED EXPORT -->" not in destination.read_text(encoding="utf-8"):
                fail(f"refusing to overwrite unowned page: {destination.relative_to(ROOT)}")
        PUBLIC_JSON.write_text(json.dumps({"schema_version": 1, "records": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for record in records:
            (PRODUCT_DIR / f"{record['slug']}.html").write_text("<!-- SBRP APPROVED EXPORT -->\n" + render_page(record), encoding="utf-8")
        if tree is not None and urlset is not None:
            for record in records:
                loc = f"https://sbrp.app/products/approved/{record['slug']}.html"
                if loc not in known:
                    url = ET.SubElement(urlset, f"{namespace}url")
                    ET.SubElement(url, f"{namespace}loc").text = loc
            tree.write(sitemap, encoding="utf-8", xml_declaration=True)
        print(f"Exported {len(records)} approved records to {PUBLIC_JSON.relative_to(ROOT)} and {PRODUCT_DIR.relative_to(ROOT)}/*.html")
        print("Review generated pages, catalog links, and sitemap before deploying.")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Export stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
