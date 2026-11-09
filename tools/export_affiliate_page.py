#!/usr/bin/env python3
"""Validate and explicitly export an owner-approved affiliate page package."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import uuid
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ARTICLE_DIR = ROOT / "articles" / "affiliate"
MANIFEST_PATH = ROOT / "data" / "affiliate_pages" / "approved.json"
SITEMAP_PATH = ROOT / "sitemap.xml"
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
EXPORT_MARKER = "<!-- SBRP APPROVED AFFILIATE EXPORT -->"
MANIFEST_OWNER = "sbrp-affiliate-export-v1"


def fail(message: str) -> None:
    raise ValueError(message)


def require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string.")
    return value.strip()


def require_https(value: object, label: str, *, optional: bool = False) -> str | None:
    if optional and (value is None or value == ""):
        return None
    if not isinstance(value, str):
        fail(f"{label} must be an HTTPS URL.")
    parts = urlparse(value)
    if parts.scheme != "https" or not parts.netloc:
        fail(f"{label} must be an HTTPS URL.")
    return value


def require_iso_date(value: object, label: str) -> str:
    if not isinstance(value, str):
        fail(f"{label} must use YYYY-MM-DD.")
    try:
        date.fromisoformat(value)
    except ValueError:
        fail(f"{label} must use YYYY-MM-DD.")
    return value


def page_content_sha256(payload: dict) -> str:
    content = {
        key: value for key, value in payload.items()
        if key not in {"workflow_state", "approval"}
    }
    canonical = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_package(payload: object) -> dict:
    if not isinstance(payload, dict):
        fail("Input must be a JSON object.")
    if payload.get("schema_version") != 1:
        fail("Unsupported affiliate page schema_version.")
    allowed_fields = {
        "schema_version", "draft_id", "workflow_state", "created_at", "topic", "audience",
        "market", "retailer", "affiliate_program", "affiliate_links_authorized",
        "minimum_review_count", "ranking_method", "page_title", "slug", "summary", "intro",
        "methodology", "limitations", "recommendations", "excluded_candidates", "approval",
    }
    unexpected_fields = set(payload) - allowed_fields
    if unexpected_fields:
        fail("Unsupported package fields: " + ", ".join(sorted(unexpected_fields)))
    try:
        uuid.UUID(require_text(payload.get("draft_id"), "draft_id"))
    except ValueError:
        fail("draft_id must be a UUID.")
    created_at = payload.get("created_at")
    if not isinstance(created_at, str):
        fail("created_at must be an ISO timestamp.")
    try:
        datetime.fromisoformat(created_at)
    except ValueError:
        fail("created_at must be an ISO timestamp.")
    if payload.get("workflow_state") != "approved":
        fail("Only an explicitly approved package can be exported.")
    approval = payload.get("approval")
    if not isinstance(approval, dict) or approval.get("decision") != "approved":
        fail("Owner approval record is missing or incomplete.")
    require_text(approval.get("reviewer"), "approval.reviewer")
    approved_hash = approval.get("content_sha256")
    if not isinstance(approved_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", approved_hash):
        fail("approval.content_sha256 must be a SHA-256 fingerprint.")
    approval_date = approval.get("decided_at")
    if not isinstance(approval_date, str):
        fail("approval.decided_at must be an ISO timestamp.")
    try:
        datetime.fromisoformat(approval_date)
    except ValueError:
        fail("approval.decided_at must be an ISO timestamp.")
    if approved_hash != page_content_sha256(payload):
        fail("Page content changed after approval; request a new owner review.")

    require_text(payload.get("topic"), "topic")
    title = require_text(payload.get("page_title"), "page_title")
    slug = require_text(payload.get("slug"), "slug")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        fail("slug must use lowercase letters, numbers, and hyphens.")
    require_text(payload.get("audience"), "audience")
    require_text(payload.get("market"), "market")
    require_text(payload.get("retailer"), "retailer")
    require_text(payload.get("summary"), "summary")
    require_text(payload.get("intro"), "intro")
    require_text(payload.get("methodology"), "methodology")
    require_text(payload.get("limitations"), "limitations")
    require_text(payload.get("ranking_method"), "ranking_method")
    if not isinstance(payload.get("affiliate_links_authorized"), bool):
        fail("affiliate_links_authorized must be a boolean.")
    if payload.get("affiliate_program") is not None and not isinstance(payload.get("affiliate_program"), str):
        fail("affiliate_program must be a string or null.")
    excluded = payload.get("excluded_candidates")
    if not isinstance(excluded, list) or any(not isinstance(item, str) for item in excluded):
        fail("excluded_candidates must be an array of strings.")
    if len(payload["summary"]) > 220:
        fail("summary must be 220 characters or fewer.")
    minimum = payload.get("minimum_review_count")
    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 0:
        fail("minimum_review_count must be a whole number of zero or more.")

    recommendations = payload.get("recommendations")
    if not isinstance(recommendations, list) or not 1 <= len(recommendations) <= 5:
        fail("recommendations must contain between one and five products.")
    affiliate_links_present = False
    seen_brands = set()
    previous_key = None
    rating_scales = set()
    for index, item in enumerate(recommendations, start=1):
        where = f"recommendations[{index - 1}]"
        if not isinstance(item, dict):
            fail(f"{where} must be an object.")
        allowed_candidate_fields = {
            "brand", "product_name", "model", "retailer", "market", "rating", "rating_max",
            "review_count", "source_url", "checked_on", "affiliate_url", "evidence_status", "rank",
        }
        if set(item) - allowed_candidate_fields:
            fail(f"{where} contains unsupported fields.")
        for field in ("brand", "product_name", "model", "retailer", "market"):
            require_text(item.get(field), f"{where}.{field}")
        brand_key = item["brand"].strip().casefold()
        if brand_key in seen_brands:
            fail(f"{where} repeats a brand; include one representative model per brand.")
        seen_brands.add(brand_key)
        if item["retailer"].strip().casefold() != payload["retailer"].strip().casefold():
            fail(f"{where}.retailer differs from the page retailer.")
        if item["market"].strip().casefold() != payload["market"].strip().casefold():
            fail(f"{where}.market differs from the page market.")
        rating = item.get("rating")
        rating_max = item.get("rating_max")
        if (isinstance(rating, bool) or not isinstance(rating, (int, float))
                or isinstance(rating_max, bool) or not isinstance(rating_max, (int, float))
                or rating_max <= 0 or rating < 0 or rating > rating_max):
            fail(f"{where} must have a valid rating and positive rating_max.")
        rating_scales.add(float(rating_max))
        review_count = item.get("review_count")
        if isinstance(review_count, bool) or not isinstance(review_count, int) or review_count < 1:
            fail(f"{where}.review_count must be a whole number greater than zero.")
        if review_count < minimum:
            fail(f"{where}.review_count is below the configured minimum.")
        require_https(item.get("source_url"), f"{where}.source_url")
        require_iso_date(item.get("checked_on"), f"{where}.checked_on")
        affiliate_url = require_https(
            item.get("affiliate_url"), f"{where}.affiliate_url", optional=True
        )
        if affiliate_url:
            affiliate_links_present = True
        if item.get("evidence_status") != "owner_supplied_not_independently_verified":
            fail(f"{where}.evidence_status must preserve owner-supplied provenance.")
        expected_rank = index
        if item.get("rank") != expected_rank:
            fail(f"{where}.rank must match its position in the ranked list.")
        ordering_key = (float(rating), review_count)
        if previous_key is not None and ordering_key > previous_key:
            fail("recommendations must be ordered by rating, then review count, descending.")
        previous_key = ordering_key
    if len(rating_scales) > 1:
        fail("recommendations must use the same displayed rating scale.")
    if affiliate_links_present:
        if payload.get("affiliate_links_authorized") is not True:
            fail("Affiliate links require explicit authorization confirmation.")
        require_text(payload.get("affiliate_program"), "affiliate_program")
    approval_fields = {"decision", "reviewer", "decided_at", "notes", "content_sha256"}
    if set(approval) - approval_fields:
        fail("Approval record contains unsupported fields.")
    return payload


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_page(payload: dict) -> str:
    title = esc(payload["page_title"])
    summary = esc(payload["summary"])
    slug = esc(payload["slug"])
    canonical = f"https://sbrp.app/articles/affiliate/{slug}.html"
    has_affiliate = any(item.get("affiliate_url") for item in payload["recommendations"])
    cards = []
    for item in payload["recommendations"]:
        affiliate_url = item.get("affiliate_url")
        destination = affiliate_url or item["source_url"]
        link_label = "View at retailer" if affiliate_url else "Open retailer source"
        monetized = (
            '<p class="affiliate-note">SBRP may earn a commission if you buy through this link.</p>'
            if affiliate_url else ""
        )
        affiliate_attr = 'data-affiliate-link="true" ' if affiliate_url else ""
        cards.append(f'''<article class="product-card">
<p class="eyebrow">Option {int(item["rank"])} · {esc(item["brand"])}</p>
<h2>{esc(item["product_name"])}</h2><p>Model: {esc(item["model"])}</p>
<p><strong>Rating:</strong> {float(item["rating"]):g}/{float(item["rating_max"]):g} · 
{int(item["review_count"]):,} reviews</p>
<p class="availability-note">Rating source checked {esc(item["checked_on"])}. This is retailer-displayed evidence, not an SBRP product test.</p>
<p><a {affiliate_attr}href="{esc(destination)}" rel="{'sponsored nofollow noopener noreferrer' if affiliate_url else 'noopener noreferrer'}">{link_label}</a></p>
{monetized}<p><a href="{esc(item['source_url'])}" rel="noopener noreferrer">View rating source</a></p>
</article>''')
    disclosure = (
        '<div class="catalog-notice" role="note"><strong>Affiliate disclosure:</strong> '
        'SBRP may earn a commission if you buy through affiliate links on this page.</div>'
        if has_affiliate else ""
    )
    cards_html = "\n".join(cards)
    return f'''{EXPORT_MARKER}
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{summary}"><link rel="canonical" href="{canonical}">
<meta property="og:type" content="article"><meta property="og:title" content="{title} | SBRP">
<meta property="og:description" content="{summary}"><meta property="og:url" content="{canonical}">
<title>{title} | SBRP</title><link rel="stylesheet" href="../../styles.css"><link rel="stylesheet" href="../../catalog.css"></head>
<body><header class="site-header"><a class="brand" href="../../index.html" aria-label="SBRP home"><span class="brand-mark">S</span><span>SBRP</span></a>
<nav class="nav" aria-label="Main navigation"><a href="../../catalog.html">Product ideas</a><a href="../../guides/index.html">Guides</a><a href="index.html">Comparisons</a><a href="../../affiliate-disclosure.html">Disclosure</a></nav></header>
<main><section class="sub-hero"><div class="sub-hero-copy"><p class="eyebrow">Affiliate comparison · {esc(payload['market'])}</p>
<h1>{title}</h1><p class="hero-lede">{summary}</p></div></section>
<section class="container catalog-section">{disclosure}<p>{esc(payload['intro'])}</p>
<div class="product-grid">{cards_html}</div><h2>How we compared</h2><p>{esc(payload['methodology'])}</p>
<h2>Limitations</h2><p>{esc(payload['limitations'])}</p>
<p>We reviewed the candidates shown here; this is not a universal ranking or a hands-on product test.</p>
<p><a href="../../affiliate-disclosure.html">Read SBRP's affiliate disclosure</a></p></section></main>
<footer class="site-footer container"><div><a class="brand footer-brand" href="../../index.html"><span class="brand-mark">S</span><span>SBRP</span></a>
<p>Discover Trends. Validate Products. Grow Smarter.</p></div><div class="footer-links"><a href="../../about.html">About</a><a href="../../contact.html">Contact</a>
<a href="../../affiliate-disclosure.html">Affiliate disclosure</a><a href="../../privacy-policy.html">Privacy</a><a href="../../terms-of-service.html">Terms</a></div><p class="copyright">© 2026 SBRP</p></footer></body></html>
'''


def render_index(records: list[dict]) -> str:
    cards = "\n".join(
        f'<li><a href="{esc(item["slug"])}.html">{esc(item["title"])}</a> — {esc(item["summary"])}</li>'
        for item in sorted(records, key=lambda value: value["title"].casefold())
    )
    return f'''{EXPORT_MARKER}
<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="SBRP's sourced affiliate product comparisons and methodology."><link rel="canonical" href="https://sbrp.app/articles/affiliate/">
<title>Product comparisons | SBRP</title><link rel="stylesheet" href="../../styles.css"><link rel="stylesheet" href="../../catalog.css"></head>
<body><header class="site-header"><a class="brand" href="../../index.html" aria-label="SBRP home"><span class="brand-mark">S</span><span>SBRP</span></a>
<nav class="nav" aria-label="Main navigation"><a href="../../catalog.html">Product ideas</a><a href="../../guides/index.html">Guides</a><a href="../../affiliate-disclosure.html">Disclosure</a></nav></header>
<main><section class="sub-hero"><div class="sub-hero-copy"><p class="eyebrow">Sourced comparisons</p><h1>Product comparisons.</h1>
<p class="hero-lede">Research-backed comparisons with a stated method and source dates.</p></div></section>
<section class="container catalog-section"><ul>{cards}</ul></section></main>
<footer class="site-footer container"><a href="../../affiliate-disclosure.html">Affiliate disclosure</a></footer></body></html>
'''


def update_sitemap(slugs: list[str]) -> bytes:
    if not SITEMAP_PATH.is_file():
        fail("sitemap.xml is missing; refusing to publish without a sitemap.")
    tree = ET.parse(SITEMAP_PATH)
    root = tree.getroot()
    known = {node.findtext(f"{SITEMAP_NS}loc") for node in root.findall(f"{SITEMAP_NS}url")}
    for slug in slugs:
        loc = f"https://sbrp.app/articles/affiliate/{slug}.html"
        if loc not in known:
            url = ET.SubElement(root, f"{SITEMAP_NS}url")
            ET.SubElement(url, f"{SITEMAP_NS}loc").text = loc
    index_loc = "https://sbrp.app/articles/affiliate/"
    if index_loc not in known:
        url = ET.SubElement(root, f"{SITEMAP_NS}url")
        ET.SubElement(url, f"{SITEMAP_NS}loc").text = index_loc
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def publish_package(payload: dict) -> list[Path]:
    ARTICLE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"generated_by": MANIFEST_OWNER, "records": []}
    if MANIFEST_PATH.exists():
        existing = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if not isinstance(existing, dict) or existing.get("generated_by") != MANIFEST_OWNER:
            fail("Refusing to overwrite an unowned affiliate page manifest.")
        manifest = existing
    records = [item for item in manifest.get("records", []) if item.get("slug") != payload["slug"]]
    records.append({"slug": payload["slug"], "title": payload["page_title"], "summary": payload["summary"]})
    manifest["records"] = records

    page_path = ARTICLE_DIR / f"{payload['slug']}.html"
    if page_path.exists() and EXPORT_MARKER not in page_path.read_text(encoding="utf-8"):
        fail(f"Refusing to overwrite unowned page: {page_path.relative_to(ROOT)}")
    index_path = ARTICLE_DIR / "index.html"
    if index_path.exists() and EXPORT_MARKER not in index_path.read_text(encoding="utf-8"):
        fail("Refusing to overwrite unowned articles/affiliate/index.html.")

    sitemap_bytes = update_sitemap([item["slug"] for item in records])
    page_path.write_text(render_page(payload), encoding="utf-8")
    index_path.write_text(render_index(records), encoding="utf-8")
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SITEMAP_PATH.write_bytes(sitemap_bytes)
    return [page_path, index_path, MANIFEST_PATH, SITEMAP_PATH]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="approved affiliate page package JSON")
    parser.add_argument("--publish", action="store_true", help="write approved public-site files")
    args = parser.parse_args()
    try:
        payload = validate_package(json.loads(args.input.read_text(encoding="utf-8")))
        if not args.publish:
            print("Approved package is valid. No files written; pass --publish to export.")
            return 0
        outputs = publish_package(payload)
        print("Exported approved affiliate page. Review before any deployment:")
        for path in outputs:
            print(f"- {path.relative_to(ROOT)}")
        return 0
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"Export stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
