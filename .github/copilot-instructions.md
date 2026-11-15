# Website SEO Audit Instructions

When the user asks you to audit, improve, or review the SEO of any website — especially one built with AI — run the **Agency SEO Ranker** 28-point checklist from [SKILL.md](../SKILL.md) and `python scripts/seo_audit.py <target>`.

## How to proceed

1. **Read SKILL.md once** at the start of the conversation.
2. **Run all 28 checks** in phase order (crawlability → meta → performance → HTML → legal → design → competition).
3. **Score each item** 0–3. Total out of 84.
4. **Return**: a scorecard table, a prioritized fix list (highest impact first), and a 30-day remediation plan.
5. **Never skip Phase 1** — without a sitemap and correct canonicals nothing else matters for indexing.

## Quick wins (when time is short)

Fix these four first — they deliver ~60% of ranking lift:
- #1 sitemap.xml
- #4 canonical tags
- #5 meta titles
- #17 schema markup

Refer to [docs/usage.md](../docs/usage.md) for tool recommendations and AI-specific trap patterns.
