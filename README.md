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

Public demo content remains maintained in HTML. Phase 2 adds a separate, manually run exporter for records that have passed source and editorial review. The Python SQLite database, credentials, research history, and generated reports do not belong in this repository. Never export raw engine output or live records without checking their sources and obtaining editorial approval.

### Export approved research records

1. Copy `tools/approved-products.example.json` to a private working location and replace the example with reviewed records. The exporter requires explicit editorial approval, a named approver, approval date, source URLs and access dates, a summary, research scope, and buying criteria.
2. Validate without writing files:

   ```powershell
   python tools/export_approved_products.py C:\path\to\approved-products.json
   ```

3. After reviewing the input and approval, explicitly publish the public artifacts:

   ```powershell
   python tools/export_approved_products.py C:\path\to\approved-products.json --publish
   ```

   This writes `data/approved-products.json`, generates crawlable pages under `products/approved/`, and adds their canonical URLs to `sitemap.xml`. The exporter refuses to replace an unowned existing page. It does not add records to the demo catalog or publish prices, retailer offers, affiliate links, sales claims, or availability.
4. Inspect the JSON, each generated page, and sitemap changes before deployment. Remove or correct rejected records in the reviewed input and rerun the exporter; delete obsolete generated pages and their sitemap URLs manually after editorial review.

The schema is intentionally narrow. Every source URL must use HTTPS. All generated content is HTML-escaped, and outbound source links use `rel="noopener noreferrer"`. Search demand, listing counts, favorites, and social engagement must not be described as sales evidence. Prices, offers, product testing claims, and structured offer data remain out of scope until separately verified and editorially approved.

There are currently no retailer offers or affiliate links. If approved links are introduced later, verify the relevant retailer and affiliate program requirements first, label monetized links near the link, use appropriate `rel="sponsored nofollow"`, and use `target="_blank"` only with `rel="noopener noreferrer"`.

## Preview deployment and rollback

No Cloudflare Pages configuration or deployment workflow is included yet. Configure a Pages preview from this repository and verify the preview URL, static asset paths, existing legal pages, `CNAME`, sitemap, and navigation before considering a production connection. This change does not switch DNS, connect a production deployment, or remove `CNAME`.

For rollback after a future deployment, restore the previously working Pages deployment/revision and preserve the existing production DNS and custom-domain configuration. Do not change DNS as part of preview setup.

## SEO and accessibility notes

Public pages include descriptive titles, descriptions, canonical URLs, Open Graph metadata, semantic headings, navigation labels, and responsive layouts. The catalog provides labelled native search and filter controls and announces result counts. No product structured data is emitted because these demo records are not real offers. No analytics, advertising, or tracking scripts are included.
