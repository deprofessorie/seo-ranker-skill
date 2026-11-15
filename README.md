# Agency SEO Ranker

**29-point SEO audit checklist for AI-generated websites.** Diagnose crawlability, on-page signals, Core Web Vitals, legal compliance, and competitive positioning — then remediate with confidence.

```
you: "audit this AI-built site"
        │
        ├─ phase 1 → sitemap + robots + noindex + canonicals
        ├─ phase 2 → meta titles, internal links, broken links
        ├─ phase 3 → image compression, CWV, mobile layout
        ├─ phase 4 → headings, slugs, OG tags, schema
        ├─ phase 5 → llms.txt, contact, footer, policies
        ├─ phase 6 → humanized content, Apple/Google design
        └─ phase 7 → competitor analysis & ranking strategy
```

Score each item 0–3. Total: 87. Anything below 52 needs serious work.

## What it does

| Capability | How |
| --- | --- |
| **Crawlability audit** | Validates sitemap.xml completeness, robots.txt coverage, noindex removal, canonical self-reference. |
| **On-page signal review** | Checks meta title uniqueness/density, internal link depth matrix, broken-link crawl. |
| **Performance scoring** | Image weight budgets, LCP / INP / CLS thresholds, mobile tap-target sizing. |
| **Semantic HTML check** | H1-per-page enforcement, heading hierarchy walk, slug hygiene, OG tag set. |
| **Structured data validation** | JSON-LD schema present + valid via Google Rich Results Test. |
| **Trust & legal compliance** | llms.txt, privacy policy, cookie policy, contact page presence and quality. |
| **Content humanization** | Sentence-length variance, transition-word density, passive-voice ratio targets. |
| **Design alignment** | Apple HIG whitespace rules, Google Material 3 / WCAG 2.2 AA contrast checks. |
| **Competitive gap analysis** | Top-5 SERP competitor extraction → technical + content diff → prioritized action list. |

## Install

Place `SKILL.md` into your Claude Code skills directory:

```bash
# Global install (available in every project)
cp -r agency-seo-ranker/ ~/.claude/skills/

# Or project-local install
cp SKILL.md <your-project>/.claude/skills/
```

Then invoke anytime in a chat:

```
/agency-seo-ranker
```

Or let it auto-load when the skill is detected for the task.

## The 29-item checklist at a glance

| # | Item | Phase | Impact |
|---|------|-------|--------|
| 1 | Build sitemap.xml | Crawlability | Critical |
| 2 | Add robots.txt | Crawlability | Critical |
| 3 | Remove noindex tags | Crawlability | Critical |
| 4 | Add canonical tags | Crawlability | Critical |
| 5 | Add meta titles | On-Page Meta | High |
| 6 | Add internal links | On-Page Meta | High |
| 7 | Fix broken links | On-Page Meta | High |
| 8 | Compress images | Performance | High |
| 9 | Core Web Vitals | Performance | High |
| 10 | Fix mobile layout | Performance | Medium |
| 11 | At least one h1 per page | Semantic HTML | Medium |
| 12 | Clean up URL slugs | Semantic HTML | Medium |
| 13 | Fix heading order | Semantic HTML | Medium |
| 14 | Add an og:image | Semantic HTML | Medium |
| 15 | Add alt text | Semantic HTML | Medium |
| 16 | Verify Google Search Console | Semantic HTML | High |
| 17 | Add schema markup | Semantic HTML | High |
| 18 | Add llms.txt | Legal & Trust | Emerging |
| 19 | Add contact page | Legal & Trust | Medium |
| 20 | Add footer | Legal & Trust | Low |
| 21 | Add privacy policy | Legal & Trust | Required |
| 22 | Add cookie policy | Legal & Trust | Required |
| 23 | Remove AI slugs | Legal & Trust | Medium |
| 24 | Adapt humanizer for paragraphs | Humanization | High |
| 25 | Adapt Apple design skills | Design | Medium |
| 26 | Adapt Google web design guidelines | Design | Medium |
| 27 | Modern UI/UX implementation | Design | Medium |
| 28 | Check competitors & rank adopting strategies | Competitive | High |

Full descriptions, AI traps to avoid, tool recommendations, and remediation steps are in [SKILL.md](./SKILL.md).

## Scoring

Each item scores **0–3**:

| Score | Meaning |
|-------|---------|
| 0 | Not implemented |
| 1 | Partially implemented, significant gaps |
| 2 | Implemented with minor issues |
| 3 | Fully implemented, validated |

**Total possible: 87**

| Range | Verdict |
|-------|---------|
| 78–87 | Excellent — ready to compete |
| 52–77 | Good — fix top 3 lowest-scoring items |
| 26–51 | Poor — major SEO overhaul needed |
| 0–25 | Critical — site will not rank without intervention |

## Related Skills

This skill works alongside:
- [`session-pilot`](https://github.com/deprofessorie/session-pilot) — memory and routing
- Any frontend/design skill (Apple HIG, Google Material) referenced in phases 5–6

## License

MIT — see [LICENSE](./LICENSE).
