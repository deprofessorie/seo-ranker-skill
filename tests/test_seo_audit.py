#!/usr/bin/env python3
"""Unit tests for scripts/seo_audit.py."""

import json
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import seo_audit  # noqa: E402


GOOD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fast Static Site SEO Guide — Practical Checklist | Acme</title>
  <meta name="description" content="A practical guide to technical SEO for modern static sites.">
  <meta name="google-site-verification" content="abc123token">
  <link rel="canonical" href="https://example.com/">
  <meta property="og:title" content="Fast Static Site SEO Guide">
  <meta property="og:description" content="Practical SEO checklist.">
  <meta property="og:image" content="https://example.com/og.webp">
  <meta property="og:url" content="https://example.com/">
  <script type="application/ld+json">
  {"@context": "https://schema.org", "@type": "WebSite", "name": "Acme"}
  </script>
  <style>@media (prefers-color-scheme: dark) { body { background: #111; } }</style>
</head>
<body>
  <main role="main" aria-label="Primary content">
    <h1>Practical Technical SEO Checklist for Modern Sites</h1>
    <h2>Why Crawlability Comes First</h2>
    <p>Search engines need clean sitemaps and valid canonical tags before anything else matters.
    Have you checked whether your generated pages actually appear in Google Search Console?
    Teams that fix indexing basics early see faster organic growth and fewer wasted crawl cycles.</p>
    <img src="/hero.webp" alt="Diagram showing crawlability and indexing flow" width="800" height="450" loading="lazy">
    <nav>
      <a href="/about.html">About Us</a>
      <a href="/contact.html">Contact</a>
      <a href="/privacy.html">Privacy Policy</a>
      <a href="/cookies.html">Cookie Policy</a>
    </nav>
    <form action="/subscribe"><input type="email" aria-label="Email"></form>
  </main>
  <footer><p>Copyright 2026 Acme</p></footer>
</body>
</html>
"""

BAD_HTML = """<!DOCTYPE html>
<html>
<head>
  <title>Home</title>
  <meta name="robots" content="noindex">
  <script src="/bundle.js"></script>
  <script type="application/ld+json">{invalid json</script>
</head>
<body>
  <h2>Welcome</h2>
  <h4>Skipped H3</h4>
  <p>Furthermore, it is important to note that in today's digital landscape we must delve into
  the tapestry of modern web solutions. Additionally, this game-changer will unlock the power
  of your online presence in conclusion for every business owner reading this page right now.</p>
  <img src="/big-banner.png">
  <img src="/photo.jpg" alt="photo.jpg">
  <a href="/missing-page">Broken Link</a>
</body>
</html>
"""


class TestSEOAudit(unittest.TestCase):
    def test_good_local_site_scores_high(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text(GOOD_HTML, encoding="utf-8")
            for page in ("about.html", "contact.html", "privacy.html", "cookies.html"):
                (root / page).write_text(
                    GOOD_HTML.replace("https://example.com/", f"https://example.com/{page}").replace(
                        "Fast Static Site SEO Guide — Practical Checklist | Acme",
                        f"{page.replace('.html', '').title()} — Acme Guide Page",
                    ),
                    encoding="utf-8",
                )
            (root / "sitemap.xml").write_text(
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                "<url><loc>https://example.com/</loc><lastmod>2026-11-15</lastmod></url>"
                "</urlset>",
                encoding="utf-8",
            )
            (root / "robots.txt").write_text(
                "User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n",
                encoding="utf-8",
            )
            (root / "llms.txt").write_text(
                "# Acme\nTechnical SEO guides, documentation, and contact information for AI agents.",
                encoding="utf-8",
            )

            site = seo_audit.collect_local_site(root, max_pages=10)
            results = seo_audit.score_site(site, competitor_count=0)
            total = sum(r.score for r in results)

            self.assertEqual(len(results), 28)
            self.assertGreaterEqual(total, 75)

    def test_bad_ai_site_flags_traps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ai_dir = root / "ai"
            ai_dir.mkdir()
            (ai_dir / "post-12345.html").write_text(BAD_HTML, encoding="utf-8")

            site = seo_audit.collect_local_site(root, max_pages=10)
            results = {r.id: r for r in seo_audit.score_site(site)}

            self.assertEqual(results[1].score, 0)  # missing sitemap
            self.assertEqual(results[2].score, 0)  # missing robots
            self.assertEqual(results[3].score, 0)  # blanket noindex
            self.assertEqual(results[4].score, 0)  # missing canonical
            self.assertEqual(results[5].score, 1)  # generic "Home" title
            self.assertEqual(results[7].score, 1)  # broken link
            self.assertEqual(results[13].score, 1)  # skipped h2 -> h4
            self.assertEqual(results[17].score, 1)  # invalid JSON-LD
            self.assertEqual(results[23].score, 0)  # /ai/post-12345.html slug
            self.assertEqual(results[24].score, 1)  # AI filler phrases

    def test_ssrf_guard_blocks_private_ips(self) -> None:
        with self.assertRaises(ValueError):
            seo_audit.validate_url("http://127.0.0.1:8080/", allow_private=False)
        with self.assertRaises(ValueError):
            seo_audit.validate_url("http://169.254.169.254/latest/meta-data/", allow_private=False)
        self.assertEqual(
            seo_audit.validate_url("http://127.0.0.1:8080/", allow_private=True),
            "http://127.0.0.1:8080/",
        )

    def test_cli_json_and_fail_under(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text(BAD_HTML, encoding="utf-8")
            out_file = root / "report.json"

            code = seo_audit.main([str(root), "--format", "json", "--output", str(out_file), "--fail-under", "50"])
            self.assertEqual(code, 1)
            report = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertEqual(report["max_score"], 84)
            self.assertEqual(len(report["results"]), 28)

    def test_redirect_ssrf_handler_blocks_private_target(self) -> None:
        handler = seo_audit.SafeRedirectHandler(allow_private=False)
        req = urllib.request.Request("https://example.com/")
        with self.assertRaises(ValueError):
            handler.redirect_request(req, None, 302, "Found", {}, "http://127.0.0.1/admin")
        with self.assertRaises(ValueError):
            handler.redirect_request(req, None, 301, "Moved", {}, "http://169.254.169.254/latest/meta-data/")

    def test_hreflang_meta_description_and_markdown_escape(self) -> None:
        html = """<!DOCTYPE html><html lang="en"><head>
        <title>Example Product Page | Brand Name</title>
        <meta name="description" content="Detailed description for SEO testing.">
        <link rel="canonical" href="https://example.com/en">
        <link rel="alternate" hreflang="en" href="https://example.com/en">
        <link rel="alternate" hreflang="es" href="https://example.com/es">
        </head><body><h1>Main Heading</h1></body></html>"""
        page = seo_audit.parse_html(html, "https://example.com/en", "/en")
        self.assertEqual(page.hreflangs, ["en", "es"])
        self.assertEqual(page.meta_description, "Detailed description for SEO testing.")
        self.assertEqual(seo_audit._score_titles([page]).score, 3)
        self.assertIn("hreflang_pages=1/1", seo_audit._score_canonical([page]).notes)
        self.assertEqual(seo_audit.sanitize_untrusted_text("Evil | Title\nInjection"), "Evil \\| Title Injection")

    def test_lighthouse_metrics_parsing_and_cwv_scoring(self) -> None:
        sample_lhr = {
            "categories": {"performance": {"score": 0.96}},
            "audits": {
                "largest-contentful-paint": {"numericValue": 1850.4},
                "interaction-to-next-paint": {"numericValue": 120.0},
                "cumulative-layout-shift": {"numericValue": 0.04},
            },
        }
        metrics = seo_audit.parse_lighthouse_metrics(sample_lhr)
        self.assertEqual(metrics["performance_score"], 96)
        self.assertEqual(metrics["lcp_ms"], 1850)
        self.assertEqual(metrics["inp_ms"], 120)
        self.assertEqual(metrics["cls"], 0.04)
        res = seo_audit._score_cwv([], metrics)
        self.assertEqual(res.score, 3)
        self.assertIn("LCP=1850ms", res.notes)

    def test_fix_starter_files_and_sarif_and_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text(GOOD_HTML, encoding="utf-8")
            (root / "dup.html").write_text(GOOD_HTML, encoding="utf-8")
            sarif_out = root / "seo.sarif"

            code = seo_audit.main([str(root), "--fix", "--format", "sarif", "--output", str(sarif_out)])
            self.assertEqual(code, 0)
            self.assertTrue((root / "robots.txt").is_file())
            self.assertTrue((root / "sitemap.xml").is_file())
            self.assertTrue((root / "llms.txt").is_file())

            sarif = json.loads(sarif_out.read_text(encoding="utf-8"))
            self.assertEqual(sarif["version"], "2.1.0")
            self.assertTrue(len(sarif["runs"][0]["results"]) > 0)

            site = seo_audit.collect_local_site(root, max_pages=10)
            health = seo_audit.detect_thin_and_duplicate_pages(site["pages"], min_words=150)
            self.assertEqual(len(health["duplicate_pages"]), 1)
            self.assertTrue(len(health["thin_pages"]) >= 1)

            diff = seo_audit.diff_sitemap_and_pages(
                '<urlset><url><loc>https://example.com/orphan</loc></url></urlset>',
                site["pages"],
            )
            self.assertIn("/orphan", diff["orphan_pages"])


if __name__ == "__main__":
    unittest.main()
