# Agency SEO Ranker — Automated Technical SEO Auditor & AI Agent Skill

**A zero-dependency Python SEO audit CLI and 28-point checklist skill for AI-generated websites, static builds, and SPAs — built for Claude Code, Cursor, GitHub Copilot, Gemini CLI, Codex, and CI/CD pipelines.**

AI website builders ship fast, but they routinely leave behind ranking killers: leftover `noindex` tags, duplicate `<title>`s, missing `sitemap.xml` or canonicals, broken footer links, uncompressed PNGs, skipped heading levels, and invalid JSON-LD schema.

**Agency SEO Ranker** fixes that in one pass. It combines a deterministic Python 3 auditor (`scripts/seo_audit.py`) with a phased 28-point remediation workflow (`SKILL.md`), optional Playwright SPA rendering, real Google Lighthouse / PageSpeed Insights Core Web Vitals, and side-by-side competitor benchmarking.

```
you: "audit this AI-built site"
        │
        ├─ phase 1 → sitemap + robots + noindex + canonicals + hreflang
        ├─ phase 2 → meta titles/descriptions, internal links, broken links
        ├─ phase 3 → image compression, Core Web Vitals (LCP/INP/CLS), mobile
        ├─ phase 4 → headings, URL slugs, OG tags, alt text, GSC, JSON-LD schema
        ├─ phase 5 → llms.txt, contact, footer, privacy/cookie policies, AI slugs
        ├─ phase 6 → humanized prose, Apple HIG, Material 3, accessibility
        └─ phase 7 → competitor technical & content gap benchmarking
```

Score each item **0–3** (max **84**). Anything below **50** needs major work.

## Why Use This Over Prompt-Only SEO Skills?

- **Zero dependencies by default:** Runs on pure Python 3 stdlib (`html.parser`, `xml.etree.ElementTree`, `urllib`) — no `pip install` or `npm install` required for static/HTML audits.
- **Optional real browser & CWV:** Pass `--render-js` for Playwright SPA rendering, `--lighthouse` for local Lighthouse Core Web Vitals, or `--pagespeed-key` for Google PageSpeed Insights v5 metrics.
- **CI/CD ready:** Use `--format json` and `--fail-under 60` to block deployments that regress SEO basics.
- **Hardened by design:** Redirect-safe SSRF protection (`SafeRedirectHandler`), Playwright sub-request route guards, local symlink traversal checks, and Markdown table escaping.

## Automated CLI Auditor

```bash
# 1. Audit a local build folder (dist/, out/, public/, or .)
python scripts/seo_audit.py ./dist

# 2. Audit a live site with SPA rendering, Lighthouse CWV, and competitor benchmarking
python scripts/seo_audit.py https://example.com --render-js --lighthouse --competitors https://comp1.com https://comp2.com

# 3. CI/CD gate: output JSON and fail build if score < 60/84
python scripts/seo_audit.py ./dist --format json --output seo-report.json --fail-under 60
```

### CLI Options

| Flag | Description |
|------|-------------|
| `target` | Local build directory path or `http(s)://` URL |
| `--max-pages N` | Maximum HTML pages to scan/crawl (default: `20`) |
| `--render-js` | Render client-side JS/SPAs using Playwright Chromium (optional) |
| `--lighthouse` | Run Lighthouse CLI for real LCP, INP/FID, CLS, and performance score (optional) |
| `--pagespeed-key KEY` | Query Google PageSpeed Insights v5 API (or set `PAGESPEED_API_KEY`) |
| `--competitors URL ...` | Benchmark competitor URLs (score, avg words, link counts, schema types) |
| `--format markdown\|json` | Report output format (default: `markdown`) |
| `--output FILE` | Write report to a file instead of stdout |
| `--fail-under SCORE` | Exit with code `1` if total score is below `SCORE` |
| `--allow-private` | Opt-in to audit `localhost` / private network targets (blocked by default) |

## Supported agents

| Agent | Adapter file | How it loads |
|-------|-------------|--------------|
| **Claude Code** | [SKILL.md](./SKILL.md) | `/agency-seo-ranker` or auto-detected |
| **Cursor** | [adapters/cursor/agency-seo-ranker.mdc](./adapters/cursor/agency-seo-ranker.mdc) | `alwaysApply: false` — activates via globs/description for web & SEO tasks |
| **GitHub Copilot** | [.github/copilot-instructions.md](./.github/copilot-instructions.md) | Picked up from `.github/` in the workspace |
| **Gemini CLI** | [.gemini/AGENTS.md](./.gemini/AGENTS.md) | Loaded as project agent instructions |
| **Codex / OpenCode** | [AGENTS.md](./AGENTS.md) | Read as general-purpose agent instructions |

Each adapter points back to the same source-of-truth [SKILL.md](./SKILL.md) so the checklist stays consistent everywhere.

## Install

### Claude Code (global — available in every project)

```bash
cp -r ~/.claude/skills/agency-seo-ranker/ ~/.claude/skills/
# or from this repo:
git clone https://github.com/deprofessorie/seo-ranker-skill.git
cp -r seo-ranker-skill ~/.claude/skills/agency-seo-ranker
```

Then type `/agency-seo-ranker` in any chat.

### Cursor

Place the repo (or just the `adapters/cursor/` folder) inside your project. Cursor picks up `.mdc` files automatically for matching web/SEO files (`alwaysApply: false`).

### GitHub Copilot

Copilot Reads instructions from `.github/copilot-instructions.md` at the workspace root. Clone this repo into your project or copy the single file into `.github/copilot-instructions.md`.

### Gemini CLI

Copy [`.gemini/AGENTS.md`](./.gemini/AGENTS.md) into your project's `.gemini/AGENTS.md` (create the directory if needed). Gemini loads it on project open.

### Codex / OpenCode / Other Agents

Copy [AGENTS.md](./AGENTS.md) to the project root. These agents read it as general instruction context.

## The 28-item checklist at a glance

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

**Total possible: 84**

| Range | Verdict |
|-------|---------|
| 76–84 | Excellent — ready to compete |
| 50–75 | Good — fix top 3 lowest-scoring items |
| 25–49 | Poor — major SEO overhaul needed |
| 0–24 | Critical — site will not rank without intervention |

## Repo structure

```
seo-ranker-skill/
├── SKILL.md                      # Source of truth — full 28-item checklist
├── README.md                     # This file
├── AGENTS.md                     # Codex / OpenCode generic instructions
├── LICENSE                       # MIT
├── scripts/
│   └── seo_audit.py              # Zero-dependency 28-point CLI auditor
├── tests/
│   └── test_seo_audit.py         # Unit tests for local & edge-case audits
├── adapters/
│   ├── bootstrap.md              # Always-on bootstrap marker
│   └── cursor/
│       └── agency-seo-ranker.mdc # Cursor .mdc adapter (glob-scoped)
├── .github/
│   └── copilot-instructions.md   # GitHub Copilot hook
├── .gemini/
│   └── AGENTS.md                 # Gemini CLI hook
├── docs/
│   └── usage.md                  # Tool references & AI trap patterns
└── examples/
    └── audit-template.md         # Ready-to-fill scorecard template
```

## Related Skills

This skill works alongside:
- [`session-pilot`](https://github.com/deprofessorie/session-pilot) — memory and routing
- Any frontend/design skill (Apple HIG, Google Material) referenced in phases 5–6

## License

MIT — see [LICENSE](./LICENSE).
