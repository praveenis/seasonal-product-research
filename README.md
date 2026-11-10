# SBRP public website

This repository contains the static SBRP website for `https://sbrp.app/`. It is separate from the Python research engine. Pages render as static HTML and remain available independently of the local engine.

## Preview locally

Open `index.html` in a browser, or serve this folder with any static file server. The catalog's search and filters use `catalog.js`; no build step or package installation is required.

## Current public content

- `index.html`: SBRP overview.
- `catalog.html`: searchable five-record illustrative demo catalog.
- `products/`: crawlable static demo product detail pages. Demo pages contain no retailer links, prices, reviews, or availability claims.
- `guides/`: six original general buying guides and an index. General content is not product testing; product-specific material requires sourced editorial review before publication.
- `seasons/`: shared seasonal editorial site for `https://seasons.sbrp.app/`. Each occasion has its own folder (currently `thanksgiving/`), with gift guides, family games, movie night, recipe discovery, and gratitude pages. The site root owns shared navigation, `robots.txt`, and a sitemap spanning all published seasons. The root-site `CNAME` and root sitemap remain dedicated to `sbrp.app`.
- `about.html`, `contact.html`, `affiliate-disclosure.html`: public information and disclosures.
- Existing `google-ads.html`, `privacy-policy.html`, and `terms-of-service.html` are retained.
- `sitemap.xml` and `robots.txt`: static crawl metadata.

## Data and publishing boundary

Public demo content remains maintained in HTML. The Python SQLite database, credentials, private draft files, research history, and generated reports do not belong in this repository. Never export raw engine output or live records without checking their sources and obtaining editorial approval.

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

### Create an approved affiliate recommendation page

Affiliate comparison pages use a separate package and exporter from the non-commercial research briefs above. The app's affiliate-page workflow accepts owner-supplied product evidence and only offers an approved package for download after the owner records approval. That package is a handoff; it does not publish or deploy a page.

1. Review the downloaded JSON package, its product sources, ratings, review counts, authorization status, and approval record.
2. From this repository, validate it without writing public files. The command lists each planned create/update target for review:

   ```powershell
   python tools/export_affiliate_page.py C:\path\to\approved-affiliate-page.json
   ```

3. After the page and evidence are approved, explicitly create the local static artifacts:

   ```powershell
   python tools/export_affiliate_page.py C:\path\to\approved-affiliate-page.json --publish
   ```

   This writes the approved article page, generated comparison index/manifest, and sitemap entries. It does not deploy the site. Review every changed file and run the static preflight before a separate production release. Private drafts must remain outside this repository and its deploy root.

The first workflow does not fetch retailer ratings or independently verify owner-entered evidence. Every included candidate needs a source-supported reason for consideration; optional considerations/trade-offs must also be supported by the linked source. Do not use Etsy favorites or search/listing popularity as ratings. Automated research requires a separately selected and authorized source.

There are currently no retailer offers or affiliate links. If approved links are introduced later, verify the relevant retailer and affiliate program requirements first, label monetized links near the link, use appropriate `rel="sponsored nofollow"`, and use `target="_blank"` only with `rel="noopener noreferrer"`.

## Preview deployment and rollback

Pull requests and pushes to `main` run a static preflight that checks required pages, local links/assets, `CNAME`, and sitemap targets. To create a hosted preview, connect this GitHub repository to a **separate Cloudflare Pages preview project** using Cloudflare's Git integration. Keep `sbrp.app` and all custom domains disconnected from that project. Configure branch controls to deploy review branches as previews, and protect the preview project's `pages.dev` hostname with Cloudflare Access if it should be private. Cloudflare's PR preview URL should be checked for static assets, legal pages, sitemap, and navigation before any production project or domain is considered.

Cloudflare account access is required for the one-time project connection and preview URL verification. The repository workflow does not contain Cloudflare credentials and does not deploy or modify DNS. `CNAME` remains `sbrp.app` for the existing production site.

For rollback after a future deployment, restore the previously working Pages deployment/revision and preserve the existing production DNS and custom-domain configuration. Do not change DNS as part of preview setup.

### Seasonal gift-guide deployment

The `seasons/` directory is the output root for a separate static hosting project at `seasons.sbrp.app`. Each season is an independent folder under it (for example, `seasons/thanksgiving/`); shared site navigation and the site-level sitemap and robots file live at the `seasons/` root. Add the hostname to that hosting project's custom-domain settings and apply only the DNS records the provider specifies. Do not point the root SBRP project at this directory or change the root `CNAME`. Verify the seasonal hub, every published season page, and the existing root domain after deployment. Keep retailer ratings dated and recheck product details before publication.

## SEO and accessibility notes

Public pages include descriptive titles, descriptions, canonical URLs, Open Graph metadata, semantic headings, navigation labels, and responsive layouts. The catalog provides labelled native search and filter controls and announces result counts. No product structured data is emitted because these demo records are not real offers. No analytics, advertising, or tracking scripts are included.
