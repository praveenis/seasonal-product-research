# SBRP public website

This repository contains the static SBRP website for `https://sbrp.app/`. It is separate from the Python research engine. Pages render as static HTML and remain available independently of the local engine.

## Preview locally

Open `index.html` in a browser, or serve this folder with any static file server. The catalog's search and filters use `catalog.js`; no build step or package installation is required.

## Current public content

- `index.html`: SBRP overview.
- `catalog.html`: searchable five-record illustrative demo catalog.
- `products/`: crawlable static demo product detail pages. Demo pages contain no retailer links, prices, reviews, or availability claims.
- `guides/`: six original general buying guides and an index. General content is not product testing; product-specific material requires sourced editorial review before publication.
- `about.html`, `contact.html`, `affiliate-disclosure.html`: public information and disclosures.
- Existing `google-ads.html`, `privacy-policy.html`, and `terms-of-service.html` are retained.
- `sitemap.xml` and `robots.txt`: static crawl metadata.

## Data and publishing boundary

Public demo content is maintained in HTML for this phase. The Python SQLite database, credentials, research history, and generated reports do not belong in this repository. Phase 2 is expected to add a validated, manually run exporter that writes approved public JSON and crawlable static pages. Do not publish generated or live records until their sources and editorial approval are checked.

There are currently no retailer offers or affiliate links. If approved links are introduced later, verify the relevant retailer and affiliate program requirements first, label monetized links near the link, use appropriate `rel="sponsored nofollow"`, and use `target="_blank"` only with `rel="noopener noreferrer"`.

## Preview deployment and rollback

No Cloudflare Pages configuration or deployment workflow is included yet. Configure a Pages preview from this repository and verify the preview URL, static asset paths, existing legal pages, `CNAME`, sitemap, and navigation before considering a production connection. This change does not switch DNS, connect a production deployment, or remove `CNAME`.

For rollback after a future deployment, restore the previously working Pages deployment/revision and preserve the existing production DNS and custom-domain configuration. Do not change DNS as part of preview setup.

## SEO and accessibility notes

Public pages include descriptive titles, descriptions, canonical URLs, Open Graph metadata, semantic headings, navigation labels, and responsive layouts. The catalog provides labelled native search and filter controls and announces result counts. No product structured data is emitted because these demo records are not real offers. No analytics, advertising, or tracking scripts are included.
