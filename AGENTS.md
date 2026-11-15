# Codex / OpenAI Agent Instructions

See [SKILL.md](./SKILL.md) for the full 28-point SEO audit checklist, or run `python scripts/seo_audit.py <target>` for an automated baseline audit.

## Quick reference

| Phase | Items | Focus |
|-------|-------|-------|
| 1. Crawlability | 1–4 | sitemap, robots.txt, noindex removal, canonical tags |
| 2. On-Page Meta | 5–7 | meta titles, internal links, broken link fixes |
| 3. Performance | 8–10 | image compression, Core Web Vitals, mobile layout |
| 4. Semantic HTML | 11–17 | h1 enforcement, URL slugs, heading order, OG tags, alt text, GSC, schema |
| 5. Legal & Trust | 18–23 | llms.txt, contact page, footer, privacy/cookie policies, remove AI slugs |
| 6. Design Polish | 24–27 | paragraph humanizer, Apple HIG, Google Material 3, modern UI/UX |
| 7. Competition | 28 | SERP competitor analysis + gap closure strategy |

## Scoring

Each item: 0 (not implemented) – 3 (fully validated). Max total: 84.
Below 50 = needs major work. Below 25 = critical.

## Top 4 quick wins

If you can only fix four things, do these first:
1. Build `sitemap.xml` (#1)
2. Add canonical tags (#4)
3. Write unique meta titles (#5)
4. Add JSON-LD schema markup (#17)
