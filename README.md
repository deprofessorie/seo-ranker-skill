# Agency SEO Ranker

**29-point SEO audit checklist for AI-generated websites — works across any AI agent.**

Diagnose crawlability, on-page signals, Core Web Vitals, legal compliance, and competitive positioning, then remediate with confidence. Works in Claude Code, Cursor, GitHub Copilot, Gemini CLI, Codex, OpenCode, and any agent that reads instruction files.

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

## Supported agents

| Agent | Adapter file | How it loads |
|-------|-------------|--------------|
| **Claude Code** | [SKILL.md](./SKILL.md) | `/agency-seo-ranker` or auto-detected |
| **Cursor** | [adapters/cursor/agency-seo-ranker.mdc](./adapters/cursor/agency-seo-ranker.mdc) | `alwaysApply: true` — runs in every chat |
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

Place the repo (or just the `adapters/cursor/` folder) inside your project. Cursor picks up `.mdc` files automatically. The skill applies to all chats via `alwaysApply: true`.

### GitHub Copilot

Copilot Reads instructions from `.github/copilot-instructions.md` at the workspace root. Clone this repo into your project or copy the single file into `.github/copilot-instructions.md`.

### Gemini CLI

Copy [`.gemini/AGENTS.md`](./.gemini/AGENTS.md) into your project's `.gemini/AGENTS.md` (create the directory if needed). Gemini loads it on project open.

### Codex / OpenCode / Other Agents

Copy [AGENTS.md](./AGENTS.md) to the project root. These agents read it as general instruction context.

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

## Repo structure

```
seo-ranker-skill/
├── SKILL.md                      # Source of truth — full 29-item checklist
├── README.md                     # This file
├── AGENTS.md                     # Codex / OpenCode generic instructions
├── LICENSE                       # MIT
├── adapters/
│   ├── bootstrap.md              # Always-on bootstrap marker
│   └── cursor/
│       └── agency-seo-ranker.mdc # Cursor .mdc adapter (alwaysApply)
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
