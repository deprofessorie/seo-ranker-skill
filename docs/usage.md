# Usage Guide

## Running an audit on an AI-built website

1. Open the project folder in Claude Code.
2. Type `/agency-seo-ranker`.
3. Provide the target URL or point Claude at the project root.
4. Claude runs all 29 checks across 7 phases and returns:
   - Scorecard table (all 29 items scored 0–3)
   - Prioritized fix list (highest-impact first)
   - Before/after evidence snippets
   - 30-day improvement plan

## Audit ordering rule

Phases must run in order — fixes earlier in the list are prerequisites for later ones:

```
Phase 1 (Crawlability)    → Phase 2 (Meta) → Phase 3 (Performance)
                                    ↓
                    Phase 4 (HTML) → Phase 5 (Legal) → Phase 6 (Design)
                                    ↓
                                 Phase 7 (Competition)
```

Skipping Phase 1 renders everything downstream invisible to search engines.

## Quick-win triage

When time is short, address these four items first — they deliver ~60% of ranking lift:

1. **sitemap.xml** (#1) — get crawlers to find pages
2. **canonical tags** (#4) — prevent duplicate-content penalties
3. **meta titles** (#5) — the primary SERP click driver
4. **schema markup** (#17) — unlock rich results

## Tool reference

| Task | Recommended Tools |
|------|------------------|
| Sitemap validation | xml-sitemap-validator.com, sitemap-cli npm |
| Robots.txt linting | Google Robots Testing Tool |
| Broken-link crawl | Screaming Frog SEO Spider, Lighthouse CI |
| Core Web Vitals | PageSpeed Insights, lighthouse CLI, web-vitals extension |
| Mobile-friendly test | Google Mobile-Friendly Test |
| Schema validation | Google Rich Results Test, Schema Markup Validator |
| Competitor analysis | Ahrefs, Semrush, Moz, SimilarWeb, BuiltWith |
| Accessibility contrast | axe DevTools, WAVE |
| Heading/hierarchy audit | DOM inspector, custom script walking `<h1>`–`<h6>` |

## Red-flag patterns specific to AI-built sites

- Blanket `noindex` left from dev/staging builds
- Identical meta titles across all routes
- Uncompressed PNG hero images (often 2–5 MB each)
- Missing `alt` attributes or filename-as-alt strings
- Heading trees that skip levels (h1→h3)
- URLs containing UUIDs, timestamps, or provider names (`/openai-result`)
- No `llms.txt` at the domain root
- Schema JSON-LD that fails validation silently

Recognizing these saves hours of manual investigation.
