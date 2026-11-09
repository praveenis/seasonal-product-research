# Developer Task: Prepare the SBRP Website for Reviewed Affiliate Pages

**Type:** Website publishing workflow and static-site tooling  
**Assignee:** Developer persona  
**Status:** In progress — schema, exporter, preflight, and source-supported candidate copy implemented; static preflight and synthetic package validation passed
**Priority:** High for the first affiliate recommendation page  
**Owner:** SBRP founder; final page approval required

## User outcome

Enable an AI-assisted workflow to prepare a complete affiliate recommendation page as a private draft for the founder to review. The founder can approve, reject, or request changes. Only an explicitly approved draft can be exported into the public static website.

The site is informational and affiliate-supported: SBRP does not sell, stock, or fulfill listed products. The current illustrative demo catalog must remain clearly separate from real recommendations.

## Current site context

- The site is a static HTML website with no CMS or page-review interface.
- `catalog.html` contains five clearly labeled demo product ideas, without live offers, prices, ratings, reviews, or affiliate links.
- `guides/` contains general buying guides that require product-specific evidence before making recommendations.
- `affiliate-disclosure.html` explains how future affiliate links will be disclosed.
- `tools/export_approved_products.py` accepts a narrow research-brief schema and requires editorial approval before writing public files. It does not support product ratings, review counts, retailer/affiliate destinations, or article drafts.
- `tools/check_static_site.py` and the static preflight workflow check site files and links.
- The separate agent feature is defined in [the affiliate content agent task](../seasonal_product_engine_mvp/seasonal_product_engine/TASK_affiliate_content_agent.md). Coordinate the page data contract with that task; do not assume the agent or its data source already exists.
- Use the sequenced [affiliate page agent implementation plan](../seasonal_product_engine_mvp/seasonal_product_engine/PLAN_affiliate_page_agent_implementation.md) for task order, shared dependencies, and the MVP exit check.

## Scope

### 1. Define and validate a page data contract

Extend or replace the approved-record schema to support an affiliate comparison page with:

- Page title, slug, topic, audience, market, summary, article body/sections, methodology, buying criteria, and limitations
- Up to five eligible recommendations, each with brand, exact model/variant, retailer, market, average rating, review count, rating scale, source URL, access/check date, and inclusion/ranking rationale
- Affiliate link and affiliate-program status, kept separate from the ordinary source URL
- Evidence/source records for claims, including source name, URL, access date, and claims supported
- Explicit editorial approval, approver, approval date, and draft status
- A clear marker for manually provided, verified, unavailable, or conflicting evidence

Reject malformed dates, unsupported/non-HTTPS source URLs, duplicate slugs, missing approval fields on public export, unsupported affiliate fields, and unsafe or unescaped content. Do not accept generated or inferred rating/review values as evidence.

### 2. Generate a private review draft

- Provide a local preview or other non-public review method using the production page template and CSS.
- Keep drafts and their data outside the public deploy root and out of the production sitemap, catalog, and navigation until approval.
- Show the full evidence and unresolved issues alongside the rendered draft, including model identity, rating, review count, source and date, affiliate-link status, disclosure text, and methodology.
- Allow the owner to approve, reject, or request revisions. Approval must be explicit and recorded; draft generation alone is not approval.
- Do not commit or deploy a draft to the public `main` site as a way to provide a preview. If a hosted preview is proposed, it must use an access-restricted preview project and must not use the production domain or DNS.

### 3. Export only after approval

Extend the approved export process so the explicit publish operation:

- Requires the recorded owner approval and validates the complete page package before writing public files
- Generates a crawlable static HTML page with canonical/meta/social metadata, accessible headings and links, and the approved site styling
- Adds authorized affiliate links only when present in the approved record; use `rel="sponsored nofollow"` and safe external-link behavior
- Places a plain-language affiliate disclosure near monetized recommendations/links and links to the site's disclosure page
- Displays ratings with review counts, retailer/market, source date, and ranking methodology; never implies that search interest or popularity proves sales
- Adds the approved page URL to the sitemap and an appropriate index/category page without adding recommendations to the demo catalog
- Refuses to overwrite unowned pages and reports exactly which public files changed

### 4. Strengthen static preflight

Update the static-site checker and CI preflight to verify, as applicable:

- Draft or review-only artifacts are not in the public deploy set or sitemap
- Every approved affiliate recommendation has required source, date, product identity, rating, and review-count fields
- Affiliate links have the required disclosure nearby and appropriate `rel` values
- Local links, canonical URLs, sitemap entries, and page metadata are valid
- Demo catalog labeling remains intact and demos are not mixed with approved affiliate records

## Approval and publishing boundary

The agent can prepare and render drafts. It cannot publish, deploy, change DNS, create or activate affiliate links, apply to an affiliate program, purchase products, or spend money. The founder's explicit approval is required before export; deployment remains a separate, deliberate release action.

## Acceptance criteria

- A developer can create a draft package from the agreed schema and view a private preview that does not appear on the public site or sitemap.
- The founder can inspect the article and its evidence, then approve, reject, or request revisions.
- The exporter refuses drafts and records without complete owner approval.
- A valid approved record generates a static page with sourced product details, rating and review count, methodology, affiliate disclosure, and correctly attributed affiliate links when available.
- The exporter adds the approved page to sitemap/index navigation, preserves the demo catalog boundary, and does not overwrite unrelated files.
- Static preflight catches missing evidence/disclosure, invalid links/metadata, and accidental publication of drafts.
- The workflow works without retailer credentials or a live ratings API by accepting verified, owner-provided/imported evidence and labeling its provenance. No scraping is introduced.
- Each candidate has a required source-supported reason for consideration and an optional source-supported considerations/trade-offs field; both appear in the private review and exported page.
- README instructions explain the draft, approval, export, review, and deployment steps, including the manual steps and source limitations.

## Dependencies and open decisions

- The owner still needs to choose the initial audience, category, market, retailer/affiliate program, and minimum review-count rule.
- Automated ratings depend on selecting an authorized source that exposes the required product identity, ratings, review counts, and affiliate destinations under terms permitting the intended display and storage. Until then, use owner-verified imported evidence.
- Coordinate the input/output schema with the separate agent implementation task before coding duplicate mechanisms.
- Review whether the privacy policy and terms need updates before connecting an external LLM, retailer API, or other provider that changes data handling. Do not claim legal review is complete.

## Out of scope

- Building a general-purpose AI agent or adding unapproved LLM/retailer APIs
- Scraping search engines or retailer websites
- Automatically publishing or deploying pages
- Affiliate applications, link creation, product ordering, or spending
- Dropshipping listings, inventory, supplier fulfillment, or sales prediction

## Handoff

Before implementation, propose the schema, draft-preview mechanism, approval record, and interaction with the separate agent task. After implementation, record the files and behavior delivered in this task and the SBRP operations snapshot. Never inspect or expose secrets, local databases, or generated research reports.
