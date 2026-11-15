<div align="center">

# Agency SEO Ranker

**Automated 28-point technical SEO auditor and AI agent skill for modern websites.**

[![SEO Ranker CI](https://github.com/deprofessorie/seo-ranker-skill/actions/workflows/test.yml/badge.svg)](https://github.com/deprofessorie/seo-ranker-skill/actions/workflows/test.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)
![Dependencies: Zero](https://img.shields.io/badge/dependencies-zero-brightgreen?style=flat-square)
![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)

[Quick Start](#quick-start) · [CLI Options](#cli-options) · [Supported Agents](#supported-agents) · [28-Point Checklist](#the-28-point-checklist) · [Scoring](#scoring)

</div>

---

AI website builders ship fast, yet they routinely leave behind silent ranking killers: leftover `noindex` tags, duplicate `<title>` elements, missing `sitemap.xml` or canonicals, broken links, uncompressed images, skipped heading levels, and invalid JSON-LD schema.

**Agency SEO Ranker** diagnoses and fixes these in one structured pass—combining a deterministic Python 3 CLI (`scripts/seo_audit.py`) with a phased remediation workflow (`SKILL.md`), optional Playwright SPA rendering, real Google Lighthouse / PageSpeed Insights Core Web Vitals, and competitor benchmarking.

---

## Core Capabilities

| Pillar | What It Delivers |
| :--- | :--- |
| **Zero-Dependency Core** | Runs on pure Python 3 stdlib (`html.parser`, `xml.etree.ElementTree`, `urllib`)—no `pip` or `npm` packages required for static/HTML audits. |
| **Real Browser & CWV** | Optional `--render-js` (Playwright Chromium) for SPAs, plus `--lighthouse` and `--pagespeed-key` for live LCP, INP/FID, and CLS metrics. |
| **CI/CD & SARIF Ready** | Gate deployments with `--fail-under`, export `--format sarif` for GitHub Code Scanning, or drop in `action.yml`. |
| **Hardened by Design** | Redirect-safe SSRF protection (`SafeRedirectHandler`), Playwright sub-request route guards, local symlink checks, and Markdown pipe escaping. |

---

## Quick Start

### 1. Run Locally (No Installation Required)

```bash
# Audit a local build folder (dist/, out/, public/, or .)
python scripts/seo_audit.py ./dist

# Auto-generate missing robots.txt, sitemap.xml, and llms.txt
python scripts/seo_audit.py ./dist --fix

# Audit a live site with SPA rendering, Lighthouse CWV, and competitor comparison
python scripts/seo_audit.py https://example.com --render-js --lighthouse --competitors https://comp1.com https://comp2.com
```

### 2. Install as a CLI (`pipx`) or GitHub Action

```bash
pipx install .
seo-audit ./dist --fix --fail-under 60
```

```yaml
# .github/workflows/seo.yml
- uses: deprofessorie/seo-ranker-skill@main
  with:
    target: ./dist
    format: sarif
    output: seo.sarif
    fail-under: "60"
```

---

## CLI Options

| Flag | Description | Default |
| :--- | :--- | :--- |
| `target` | Local build directory path or `http(s)://` URL | *Required* |
| `--max-pages N` | Maximum HTML pages to scan or crawl | `20` |
| `--format` | Output format: `markdown`, `json`, or `sarif` | `markdown` |
| `--output FILE` | Write report to a file instead of stdout | `stdout` |
| `--fail-under SCORE` | Exit with code `1` if score is below `SCORE` (out of `84`) | `0` |
| `--fix` | Generate missing starter `robots.txt`, `sitemap.xml`, and `llms.txt` locally | `false` |
| `--check-external` | Concurrently verify outbound HTTP(S) links and image URLs | `false` |
| `--render-js` | Render client-side JS/SPAs using Playwright Chromium (optional) | `false` |
| `--lighthouse` | Run Lighthouse CLI for real LCP, INP/FID, CLS, and performance score | `false` |
| `--pagespeed-key KEY` | Query Google PageSpeed Insights v5 API (or set `PAGESPEED_API_KEY`) | `""` |
| `--competitors URL ...` | Benchmark competitor URLs (score, avg words, links, schema types) | `[]` |
| `--allow-private` | Opt-in to audit `localhost` or private network targets | `false` |

---

## Supported Agents

Every adapter points to the same source-of-truth [SKILL.md](./SKILL.md) so the workflow stays consistent across tools.

| Agent | Adapter | Activation |
| :--- | :--- | :--- |
| **Claude Code** | [SKILL.md](./SKILL.md) | `/agency-seo-ranker` or auto-detected |
| **Cursor** | [adapters/cursor/agency-seo-ranker.mdc](./adapters/cursor/agency-seo-ranker.mdc) | `alwaysApply: false` (scoped to web & SEO globs) |
| **GitHub Copilot** | [.github/copilot-instructions.md](./.github/copilot-instructions.md) | Loaded automatically from `.github/` |
| **Gemini CLI** | [.gemini/AGENTS.md](./.gemini/AGENTS.md) | Loaded as project agent instructions |
| **Codex / OpenCode** | [AGENTS.md](./AGENTS.md) | Read as general-purpose agent instructions |

<details>
<summary><strong>Installation instructions per agent</strong></summary>

- **Claude Code (global):**
  ```bash
  git clone https://github.com/deprofessorie/seo-ranker-skill.git
  cp -r seo-ranker-skill ~/.claude/skills/agency-seo-ranker
  ```
  Then run `/agency-seo-ranker` in any chat.
- **Cursor:** Copy `adapters/cursor/agency-seo-ranker.mdc` into `.cursor/rules/` in your project.
- **GitHub Copilot:** Copy `.github/copilot-instructions.md` into your repo's `.github/` folder.
- **Gemini CLI:** Copy `.gemini/AGENTS.md` into your project's `.gemini/` folder.
- **Codex / OpenCode:** Copy `AGENTS.md` to your project root.

</details>

---

## The 28-Point Checklist

Audits execute strictly in phase order—fixing crawlability before on-page meta, performance, and competitive gaps:

```
Phase 1 (Crawlability)  →  Phase 2 (On-Page Meta)  →  Phase 3 (Performance)
                                    ↓
Phase 4 (Semantic HTML) →  Phase 5 (Legal & Trust) →  Phase 6 (Design & Humanization)
                                    ↓
                           Phase 7 (Competitive Intelligence)
```

<details>
<summary><strong>View all 28 checklist items</strong></summary>

| # | Item | Phase | Impact |
| :-: | :--- | :--- | :--- |
| 1 | Build `sitemap.xml` | Crawlability | Critical |
| 2 | Add `robots.txt` | Crawlability | Critical |
| 3 | Remove `noindex` tags | Crawlability | Critical |
| 4 | Add canonical & `hreflang` tags | Crawlability | Critical |
| 5 | Add meta titles & descriptions | On-Page Meta | High |
| 6 | Add internal links | On-Page Meta | High |
| 7 | Fix broken links | On-Page Meta | High |
| 8 | Compress images | Performance | High |
| 9 | Core Web Vitals (LCP, INP, CLS) | Performance | High |
| 10 | Fix mobile layout | Performance | Medium |
| 11 | At least one `<h1>` per page | Semantic HTML | Medium |
| 12 | Clean up URL slugs | Semantic HTML | Medium |
| 13 | Fix heading order | Semantic HTML | Medium |
| 14 | Add an `og:image` | Semantic HTML | Medium |
| 15 | Add `alt` text | Semantic HTML | Medium |
| 16 | Verify Google Search Console | Semantic HTML | High |
| 17 | Add JSON-LD schema markup | Semantic HTML | High |
| 18 | Add `llms.txt` | Legal & Trust | Emerging |
| 19 | Add contact page | Legal & Trust | Medium |
| 20 | Add consistent footer | Legal & Trust | Low |
| 21 | Add privacy policy | Legal & Trust | Required |
| 22 | Add cookie policy | Legal & Trust | Required |
| 23 | Remove AI slugs | Legal & Trust | Medium |
| 24 | Adapt humanizer for paragraphs | Humanization | High |
| 25 | Adapt Apple design guidelines | Design | Medium |
| 26 | Adapt Google web design guidelines | Design | Medium |
| 27 | Modern UI/UX & accessibility | Design | Medium |
| 28 | Competitor analysis & gap closure | Competitive | High |

Full descriptions, AI traps, and remediation steps live in [SKILL.md](./SKILL.md).

</details>

---

## Scoring

Each item is scored **0–3** (`0` = missing, `1` = partial, `2` = minor issues, `3` = validated) for a maximum total of **84 points**.

| Score Range | Verdict | Recommended Action |
| :---: | :--- | :--- |
| **76–84** | 🟢 **Excellent** | Ready to compete; monitor quarterly |
| **50–75** | 🟡 **Good** | Fix top 3 lowest-scoring items |
| **25–49** | 🟠 **Poor** | Major SEO overhaul needed |
| **0–24** | 🔴 **Critical** | Site will not rank without intervention |

---

## Repository Structure

```
seo-ranker-skill/
├── SKILL.md                      # Source of truth — full 28-item checklist
├── README.md                     # Overview & documentation
├── AGENTS.md                     # Codex / OpenCode instructions
├── action.yml                    # Reusable GitHub Action
├── pyproject.toml                # Python package (pipx / uvx)
├── LICENSE                       # MIT
├── scripts/
│   └── seo_audit.py              # Zero-dependency 28-point CLI auditor
├── tests/
│   └── test_seo_audit.py         # Unit test suite
├── adapters/
│   ├── bootstrap.md              # Always-on bootstrap marker
│   └── cursor/
│       └── agency-seo-ranker.mdc # Cursor .mdc rule (glob-scoped)
├── .github/
│   ├── copilot-instructions.md   # GitHub Copilot instructions
│   └── workflows/
│       └── test.yml              # CI test workflow
├── .gemini/
│   └── AGENTS.md                 # Gemini CLI instructions
├── docs/
│   └── usage.md                  # Tool references & AI trap patterns
└── examples/
    └── audit-template.md         # Ready-to-fill scorecard template
```

## License

MIT — see [LICENSE](./LICENSE).
