#!/usr/bin/env python3
"""
Agency SEO Ranker — Automated 28-Point SEO Auditor (v2.0.0)

Audits a local website build directory or a live HTTP(S) URL against the
28-point Agency SEO Ranker checklist (max score: 84), producing a scored
Markdown or JSON report. Uses only the Python 3 standard library.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


AI_FILLER_PHRASES = (
    "furthermore",
    "additionally",
    "it is important to note",
    "in today's digital landscape",
    "in conclusion",
    "moreover",
    "delve into",
    "tapestry of",
    "game-changer",
    "unlock the power",
)

AI_SLUG_PATTERNS = (
    re.compile(r"/(?:ai|generated|bot|auto)/", re.IGNORECASE),
    re.compile(r"/openai[-_]", re.IGNORECASE),
    re.compile(r"-\d{4,}$"),
)

GENERIC_ALT_WORDS = {"image", "photo", "picture", "img", "banner", "icon", "logo"}
GENERIC_TITLES = {"home", "welcome", "index", "untitled", "document", "react app", "vite app"}
STOP_WORDS = {"a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"}

USER_AGENT = "AgencySEORanker/2.0 (+https://github.com/deprofessorie/seo-ranker-skill)"


@dataclass
class PageData:
    """Extracted SEO signals for a single HTML page."""

    url_or_path: str
    slug: str = "/"
    status_code: int | None = None
    title: str = ""
    meta_description: str = ""
    lang: str = ""
    viewport: str = ""
    canonical: str = ""
    robots_meta: list[str] = field(default_factory=list)
    gsc_verification: bool = False
    og_tags: dict[str, str] = field(default_factory=dict)
    headings: list[tuple[int, str]] = field(default_factory=list)
    images: list[dict[str, Any]] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    json_ld_raw: list[str] = field(default_factory=list)
    blocking_scripts_in_head: int = 0
    has_footer: bool = False
    has_form: bool = False
    has_dark_mode_hint: bool = False
    has_aria_or_skip: bool = False
    body_text: str = ""


@dataclass
class CheckResult:
    """Result for a single checklist item (scored 0-3)."""

    id: int
    name: str
    phase: str
    score: int
    impact: str
    notes: str
    recommendation: str = ""

    @property
    def status_emoji(self) -> str:
        if self.score >= 3:
            return "🟢"
        if self.score >= 1:
            return "🟡"
        return "🔴"


class SEOHTMLParser(HTMLParser):
    """Safe, stdlib HTML parser that extracts SEO-relevant tags and visible text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.in_title = False
        self.in_body = False
        self.in_script = False
        self.in_style = False
        self.current_script_type = ""
        self.current_heading_level: int | None = None
        self.current_link_href: str | None = None
        self.current_link_text: list[str] = []
        self.heading_buf: list[str] = []
        self.title_buf: list[str] = []
        self.script_buf: list[str] = []
        self.body_text_parts: list[str] = []

        self.lang = ""
        self.viewport = ""
        self.canonical = ""
        self.meta_description = ""
        self.robots_meta: list[str] = []
        self.gsc_verification = False
        self.og_tags: dict[str, str] = {}
        self.headings: list[tuple[int, str]] = []
        self.images: list[dict[str, Any]] = []
        self.links: list[dict[str, str]] = []
        self.json_ld_raw: list[str] = []
        self.blocking_scripts_in_head = 0
        self.has_footer = False
        self.has_form = False
        self.has_dark_mode_hint = False
        self.has_aria_or_skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {k.lower(): (v or "") for k, v in attrs}

        if any(k.startswith("aria-") or k == "role" for k in attr_map):
            self.has_aria_or_skip = True
        if "dark" in attr_map.get("class", "").lower() or "theme" in attr_map.get("data-theme", "").lower():
            self.has_dark_mode_hint = True

        if tag == "html":
            self.lang = attr_map.get("lang", "").strip()
        elif tag == "head":
            self.in_head = True
        elif tag == "body":
            self.in_body = True
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            self._handle_meta(attr_map)
        elif tag == "link":
            rel = attr_map.get("rel", "").lower().split()
            href = attr_map.get("href", "").strip()
            if "canonical" in rel and href and not self.canonical:
                self.canonical = href
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.current_heading_level = int(tag[1])
            self.heading_buf = []
        elif tag == "img":
            self.images.append(
                {
                    "src": attr_map.get("src", "").strip(),
                    "alt": attr_map.get("alt"),
                    "loading": attr_map.get("loading", "").lower(),
                    "width": attr_map.get("width", "").strip(),
                    "height": attr_map.get("height", "").strip(),
                }
            )
        elif tag == "a":
            self.current_link_href = attr_map.get("href", "").strip()
            self.current_link_text = []
        elif tag == "script":
            self.in_script = True
            self.current_script_type = attr_map.get("type", "").lower()
            self.script_buf = []
            if (
                self.in_head
                and "src" in attr_map
                and "defer" not in attr_map
                and "async" not in attr_map
                and self.current_script_type != "module"
                and self.current_script_type != "application/ld+json"
            ):
                self.blocking_scripts_in_head += 1
        elif tag == "style":
            self.in_style = True
        elif tag == "footer":
            self.has_footer = True
        elif tag == "form":
            self.has_form = True

    def _handle_meta(self, attr_map: dict[str, str]) -> None:
        name = attr_map.get("name", "").lower()
        prop = attr_map.get("property", "").lower()
        content = attr_map.get("content", "").strip()

        if name == "viewport":
            self.viewport = content
        elif name == "description":
            self.meta_description = content
        elif name in ("robots", "googlebot"):
            self.robots_meta.append(content.lower())
        elif name == "google-site-verification" and content:
            self.gsc_verification = True
        elif name == "color-scheme" and "dark" in content.lower():
            self.has_dark_mode_hint = True

        if prop.startswith("og:"):
            self.og_tags[prop] = content

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "head":
            self.in_head = False
        elif tag == "body":
            self.in_body = False
        elif tag == "title":
            self.in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self.current_heading_level is not None:
            text = " ".join("".join(self.heading_buf).split())
            self.headings.append((self.current_heading_level, text))
            self.current_heading_level = None
        elif tag == "a" and self.current_link_href is not None:
            text = " ".join("".join(self.current_link_text).split())
            self.links.append({"href": self.current_link_href, "text": text})
            self.current_link_href = None
        elif tag == "script":
            if self.current_script_type == "application/ld+json":
                self.json_ld_raw.append("".join(self.script_buf).strip())
            self.in_script = False
            self.current_script_type = ""
        elif tag == "style":
            self.in_style = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_buf.append(data)
        if self.current_heading_level is not None:
            self.heading_buf.append(data)
        if self.current_link_href is not None:
            self.current_link_text.append(data)
        if self.in_script:
            self.script_buf.append(data)
        elif self.in_style:
            if "prefers-color-scheme" in data:
                self.has_dark_mode_hint = True
        elif self.in_body:
            self.body_text_parts.append(data)


def parse_html(html: str, url_or_path: str, slug: str, status_code: int | None = None) -> PageData:
    """Parse HTML string into a PageData object."""
    parser = SEOHTMLParser()
    parser.feed(html)
    parser.close()
    return PageData(
        url_or_path=url_or_path,
        slug=slug,
        status_code=status_code,
        title=" ".join("".join(parser.title_buf).split()),
        meta_description=parser.meta_description,
        lang=parser.lang,
        viewport=parser.viewport,
        canonical=parser.canonical,
        robots_meta=parser.robots_meta,
        gsc_verification=parser.gsc_verification,
        og_tags=parser.og_tags,
        headings=parser.headings,
        images=parser.images,
        links=parser.links,
        json_ld_raw=parser.json_ld_raw,
        blocking_scripts_in_head=parser.blocking_scripts_in_head,
        has_footer=parser.has_footer,
        has_form=parser.has_form,
        has_dark_mode_hint=parser.has_dark_mode_hint,
        has_aria_or_skip=parser.has_aria_or_skip,
        body_text=" ".join("".join(parser.body_text_parts).split()),
    )


def _is_private_host(hostname: str) -> bool:
    """Return True if hostname resolves to a private, loopback, or link-local IP."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return True
    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return True
        except ValueError:
            return True
    return False


def validate_url(url: str, allow_private: bool = False) -> str:
    """Validate HTTP(S) URL and enforce SSRF guard unless allow_private is True."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Unsupported or invalid URL: {url}")
    hostname = parsed.hostname or ""
    if not allow_private and _is_private_host(hostname):
        raise ValueError(
            f"Refusing private/loopback host '{hostname}' (pass --allow-private to override for local dev)"
        )
    return url


def fetch_url(url: str, timeout: int = 10, allow_private: bool = False) -> tuple[int, dict[str, str], str]:
    """Fetch a URL safely and return (status_code, lowercased_headers, body_text)."""
    validate_url(url, allow_private=allow_private)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            raw = resp.read(2_000_000)  # Cap at 2 MB per page
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.status, headers, raw.decode(charset, errors="replace")
    except urllib.error.HTTPError as err:
        return err.code, {k.lower(): v for k, v in err.headers.items()}, ""
    except urllib.error.URLError:
        return 0, {}, ""


def collect_local_site(root: Path, max_pages: int) -> dict[str, Any]:
    """Scan a local directory for HTML files, sitemap.xml, robots.txt, llms.txt, and images."""
    skip_dirs = {"node_modules", ".git", ".next", ".venv", "venv", "__pycache__"}
    html_files: list[Path] = []
    image_sizes: list[tuple[str, int]] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower()
            if ext in (".html", ".htm"):
                html_files.append(fpath)
            elif ext in (".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg"):
                image_sizes.append((str(fpath.relative_to(root)), fpath.stat().st_size))

    html_files.sort()
    pages: list[PageData] = []
    for fpath in html_files[:max_pages]:
        rel = "/" + str(fpath.relative_to(root)).replace("\\", "/")
        if rel.endswith("/index.html"):
            slug = rel[: -len("index.html")] or "/"
        else:
            slug = rel
        text = fpath.read_text(encoding="utf-8", errors="replace")
        pages.append(parse_html(text, str(fpath), slug, status_code=200))

    def _read_optional(name: str) -> str | None:
        for candidate in (root / name, root / "public" / name):
            if candidate.is_file():
                return candidate.read_text(encoding="utf-8", errors="replace")
        return None

    return {
        "mode": "local",
        "target": str(root),
        "pages": pages,
        "sitemap": _read_optional("sitemap.xml"),
        "robots": _read_optional("robots.txt"),
        "llms": _read_optional("llms.txt"),
        "image_sizes": image_sizes,
        "broken_links": _check_local_links(root, pages),
        "x_robots_noindex": False,
    }


def _check_local_links(root: Path, pages: list[PageData]) -> list[str]:
    """Check relative internal links against local filesystem paths."""
    broken: list[str] = []
    for page in pages:
        for link in page.links:
            href = link["href"]
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "http://", "https://")):
                continue
            clean = href.split("#", 1)[0].split("?", 1)[0]
            if not clean:
                continue
            rel = clean.lstrip("/")
            candidates = [root / rel, root / rel / "index.html", root / f"{rel}.html"]
            if not any(c.exists() for c in candidates):
                broken.append(f"{page.slug} -> {href}")
    return broken


def collect_remote_site(base_url: str, max_pages: int, timeout: int, allow_private: bool) -> dict[str, Any]:
    """Crawl a live HTTP(S) site up to max_pages and fetch sitemap.xml, robots.txt, and llms.txt."""
    parsed_base = urllib.parse.urlparse(validate_url(base_url, allow_private=allow_private))
    origin = f"{parsed_base.scheme}://{parsed_base.netloc}"

    visited: set[str] = set()
    queue: list[str] = [base_url]
    pages: list[PageData] = []
    broken_links: list[str] = []
    x_robots_noindex = False

    while queue and len(pages) < max_pages:
        current = queue.pop(0)
        norm = current.rstrip("/") or origin
        if norm in visited:
            continue
        visited.add(norm)

        status, headers, body = fetch_url(current, timeout=timeout, allow_private=allow_private)
        if "noindex" in headers.get("x-robots-tag", "").lower():
            x_robots_noindex = True
        if status >= 400 or status == 0:
            broken_links.append(f"{current} (HTTP {status})")
            continue

        slug = urllib.parse.urlparse(current).path or "/"
        page = parse_html(body, current, slug, status_code=status)
        pages.append(page)

        for link in page.links:
            href = link["href"]
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            resolved = urllib.parse.urljoin(current, href).split("#", 1)[0]
            r_parsed = urllib.parse.urlparse(resolved)
            if r_parsed.netloc == parsed_base.netloc:
                r_norm = resolved.rstrip("/") or origin
                if r_norm not in visited and len(visited) + len(queue) < max_pages * 2:
                    queue.append(resolved)

    def _fetch_root_file(path: str) -> str | None:
        st, _, text = fetch_url(f"{origin}/{path}", timeout=timeout, allow_private=allow_private)
        return text if st == 200 and text.strip() else None

    return {
        "mode": "remote",
        "target": base_url,
        "pages": pages,
        "sitemap": _fetch_root_file("sitemap.xml"),
        "robots": _fetch_root_file("robots.txt"),
        "llms": _fetch_root_file("llms.txt"),
        "image_sizes": [],
        "broken_links": broken_links,
        "x_robots_noindex": x_robots_noindex,
    }


def _score_sitemap(sitemap: str | None) -> CheckResult:
    if not sitemap:
        return CheckResult(1, "Build sitemap.xml", "Crawlability", 0, "Critical", "No sitemap.xml found.", "Generate sitemap.xml with clean canonical URLs.")
    try:
        root = ET.fromstring(sitemap)
    except ET.ParseError as exc:
        return CheckResult(1, "Build sitemap.xml", "Crawlability", 1, "Critical", f"Invalid XML in sitemap.xml: {exc}", "Fix XML syntax and validate sitemap.")
    locs = [el.text.strip() for el in root.iter() if el.tag.endswith("loc") and el.text]
    has_lastmod = any(el.tag.endswith("lastmod") for el in root.iter())
    dupes = len(locs) != len(set(locs))
    if not locs:
        return CheckResult(1, "Build sitemap.xml", "Crawlability", 1, "Critical", "sitemap.xml has 0 <loc> entries.", "Populate sitemap.xml with indexable URLs.")
    if dupes or not has_lastmod:
        return CheckResult(1, "Build sitemap.xml", "Crawlability", 2, "Critical", f"{len(locs)} URLs found; dupes={dupes}, lastmod={has_lastmod}.", "Deduplicate URLs and include <lastmod>.")
    return CheckResult(1, "Build sitemap.xml", "Crawlability", 3, "Critical", f"Valid sitemap.xml with {len(locs)} unique URLs and <lastmod>.", "")


def _score_robots(robots: str | None) -> CheckResult:
    if not robots:
        return CheckResult(2, "Add robots.txt", "Crawlability", 0, "Critical", "No robots.txt found.", "Add robots.txt with Allow/Disallow and Sitemap directive.")
    lower = robots.lower()
    blocks_all = bool(re.search(r"disallow:\s*/\s*$", lower, re.MULTILINE))
    has_sitemap = "sitemap:" in lower
    if blocks_all:
        return CheckResult(2, "Add robots.txt", "Crawlability", 1, "Critical", "robots.txt contains 'Disallow: /' blocking all crawlers.", "Replace 'Disallow: /' with 'Allow: /' for public content.")
    if not has_sitemap:
        return CheckResult(2, "Add robots.txt", "Crawlability", 2, "Critical", "robots.txt present but missing Sitemap: directive.", "Add 'Sitemap: https://yourdomain.com/sitemap.xml'.")
    return CheckResult(2, "Add robots.txt", "Crawlability", 3, "Critical", "robots.txt valid with Sitemap directive.", "")


def _score_noindex(pages: list[PageData], x_robots_noindex: bool) -> CheckResult:
    if not pages:
        return CheckResult(3, "Remove noindex tags", "Crawlability", 0, "Critical", "No HTML pages found to inspect.")
    flagged = [p.slug for p in pages if any("noindex" in m for m in p.robots_meta)]
    if x_robots_noindex or len(flagged) == len(pages):
        return CheckResult(3, "Remove noindex tags", "Crawlability", 0, "Critical", "Blanket noindex detected across site/headers.", "Strip noindex from production pages.")
    if flagged:
        return CheckResult(3, "Remove noindex tags", "Crawlability", 2, "Critical", f"noindex found on: {', '.join(flagged[:5])}", "Verify noindex is only on genuinely private pages.")
    return CheckResult(3, "Remove noindex tags", "Crawlability", 3, "Critical", "No stray noindex tags detected.", "")


def _score_canonical(pages: list[PageData]) -> CheckResult:
    if not pages:
        return CheckResult(4, "Add canonical tags", "Crawlability", 0, "Critical", "No HTML pages found.")
    canonicals = [p.canonical for p in pages]
    missing = sum(1 for c in canonicals if not c)
    if missing == len(pages):
        return CheckResult(4, "Add canonical tags", "Crawlability", 0, "Critical", "No <link rel='canonical'> tags found.", "Add self-referencing canonical tag to every page.")
    non_empty = [c for c in canonicals if c]
    if missing > 0 or (len(pages) > 1 and len(set(non_empty)) == 1):
        return CheckResult(4, "Add canonical tags", "Crawlability", 1, "Critical", f"Missing on {missing}/{len(pages)} pages or hardcoded identical canonical.", "Ensure every page has a unique, self-referencing canonical URL.")
    return CheckResult(4, "Add canonical tags", "Crawlability", 3, "Critical", "All audited pages have unique canonical tags.", "")


def _score_titles(pages: list[PageData]) -> CheckResult:
    if not pages:
        return CheckResult(5, "Add meta titles", "On-Page Meta", 0, "High", "No HTML pages found.")
    titles = [p.title for p in pages]
    missing = sum(1 for t in titles if not t)
    if missing == len(pages):
        return CheckResult(5, "Add meta titles", "On-Page Meta", 0, "High", "All pages missing <title>.", "Add unique 50-60 char <title> tags.")
    generic = [t for t in titles if t.lower() in GENERIC_TITLES]
    bad_len = [t for t in titles if t and (len(t) < 20 or len(t) > 70)]
    dupes = len([t for t in titles if t]) != len(set(t for t in titles if t))
    if missing > 0 or generic or dupes:
        return CheckResult(5, "Add meta titles", "On-Page Meta", 1, "High", f"Missing={missing}, dupes={dupes}, generic={len(generic)}.", "Make every <title> unique, descriptive, and 50-60 chars.")
    if bad_len:
        return CheckResult(5, "Add meta titles", "On-Page Meta", 2, "High", f"{len(bad_len)} title(s) outside 20-70 chars.", "Tighten titles to 50-60 characters.")
    return CheckResult(5, "Add meta titles", "On-Page Meta", 3, "High", "Unique, well-sized <title> tags on all pages.", "")


def _score_internal_links(pages: list[PageData]) -> CheckResult:
    if not pages:
        return CheckResult(6, "Add internal links", "On-Page Meta", 0, "High", "No HTML pages found.")
    counts = []
    for p in pages:
        internal = [l for l in p.links if l["href"] and not l["href"].startswith(("http://", "https://", "mailto:", "tel:", "#"))]
        counts.append(len(internal))
    avg = sum(counts) / len(counts)
    if avg == 0:
        return CheckResult(6, "Add internal links", "On-Page Meta", 0, "High", "0 internal links detected.", "Add 3-7 contextual internal links per page.")
    if avg < 3:
        return CheckResult(6, "Add internal links", "On-Page Meta", 2, "High", f"Average {avg:.1f} internal links/page (target 3-7).", "Add more topic-cluster internal links.")
    return CheckResult(6, "Add internal links", "On-Page Meta", 3, "High", f"Average {avg:.1f} internal links/page.", "")


def _score_broken_links(broken_links: list[str]) -> CheckResult:
    if not broken_links:
        return CheckResult(7, "Fix broken links", "On-Page Meta", 3, "High", "0 broken internal links/pages detected.", "")
    score = 1 if len(broken_links) <= 3 else 0
    return CheckResult(7, "Fix broken links", "On-Page Meta", score, "High", f"{len(broken_links)} broken link(s): {', '.join(broken_links[:3])}", "Fix or 301-redirect broken routes.")


def _score_images(pages: list[PageData], image_sizes: list[tuple[str, int]]) -> CheckResult:
    imgs = [img for p in pages for img in p.images]
    large_files = [(name, sz) for name, sz in image_sizes if sz > 150_000]
    non_modern = [img["src"] for img in imgs if img["src"] and not any(img["src"].lower().split("?")[0].endswith(ext) for ext in (".webp", ".avif", ".svg"))]
    if not imgs and not image_sizes:
        return CheckResult(8, "Compress images", "Performance", 2, "High", "No <img> tags found to audit.", "Verify image pipeline if images are added.")
    if large_files or (imgs and len(non_modern) == len(imgs)):
        return CheckResult(8, "Compress images", "Performance", 1, "High", f"{len(large_files)} image(s) >150KB; {len(non_modern)}/{len(imgs)} non-WebP/AVIF.", "Convert images to WebP/AVIF, compress <150KB, add loading='lazy'.")
    if non_modern:
        return CheckResult(8, "Compress images", "Performance", 2, "High", f"{len(non_modern)}/{len(imgs)} images use legacy formats.", "Prefer WebP/AVIF with srcset.")
    return CheckResult(8, "Compress images", "Performance", 3, "High", "Images use modern formats and reasonable sizes.", "")


def _score_cwv(pages: list[PageData]) -> CheckResult:
    if not pages:
        return CheckResult(9, "Core Web Vitals", "Performance", 0, "High", "No HTML pages found.")
    imgs = [img for p in pages for img in p.images]
    missing_dims = sum(1 for img in imgs if not img["width"] or not img["height"])
    blocking = sum(p.blocking_scripts_in_head for p in pages)
    if blocking > 0 and missing_dims > 0:
        return CheckResult(9, "Core Web Vitals", "Performance", 1, "High", f"{blocking} render-blocking <script> in <head>; {missing_dims} <img> missing width/height.", "Add defer/async to scripts and explicit width/height to images; verify with Lighthouse.")
    if blocking > 0 or missing_dims > 0:
        return CheckResult(9, "Core Web Vitals", "Performance", 2, "High", f"blocking_scripts={blocking}, imgs_without_dims={missing_dims}.", "Fix remaining CLS/INP hints and run Lighthouse CI.")
    return CheckResult(9, "Core Web Vitals", "Performance", 3, "High", "No render-blocking head scripts or unsized images detected (confirm with Lighthouse).", "")


def _score_mobile(pages: list[PageData]) -> CheckResult:
    if not pages:
        return CheckResult(10, "Fix mobile layout", "Performance", 0, "Medium", "No HTML pages found.")
    missing_vp = sum(1 for p in pages if "width=device-width" not in p.viewport.lower())
    if missing_vp == len(pages):
        return CheckResult(10, "Fix mobile layout", "Performance", 0, "Medium", "Missing viewport meta tag.", "Add <meta name='viewport' content='width=device-width, initial-scale=1'>.")
    if missing_vp > 0:
        return CheckResult(10, "Fix mobile layout", "Performance", 1, "Medium", f"Viewport meta missing on {missing_vp}/{len(pages)} pages.", "Add viewport meta to all templates.")
    return CheckResult(10, "Fix mobile layout", "Performance", 3, "Medium", "Responsive viewport meta present on all pages.", "")


def _score_h1(pages: list[PageData]) -> CheckResult:
    if not pages:
        return CheckResult(11, "At least one h1 per page", "Semantic HTML", 0, "Medium", "No HTML pages found.")
    bad = []
    for p in pages:
        h1s = [h for h in p.headings if h[0] == 1]
        if len(h1s) != 1:
            bad.append(f"{p.slug}({len(h1s)})")
    if len(bad) == len(pages):
        return CheckResult(11, "At least one h1 per page", "Semantic HTML", 0, "Medium", f"H1 count != 1 on all pages: {', '.join(bad[:4])}", "Ensure exactly one <h1> per page.")
    if bad:
        return CheckResult(11, "At least one h1 per page", "Semantic HTML", 2, "Medium", f"H1 count != 1 on: {', '.join(bad[:4])}", "Fix pages with 0 or multiple <h1> tags.")
    return CheckResult(11, "At least one h1 per page", "Semantic HTML", 3, "Medium", "Every page has exactly one <h1>.", "")


def _score_slugs(pages: list[PageData]) -> CheckResult:
    bad = []
    for p in pages:
        if p.slug in ("/", "/index.html"):
            continue
        seg = p.slug.strip("/").split("/")[-1].replace(".html", "")
        words = [w for w in seg.split("-") if w]
        if seg != seg.lower() or "_" in seg or len(words) > 5 or any(w in STOP_WORDS for w in words):
            bad.append(p.slug)
    if bad:
        score = 1 if len(bad) > len(pages) / 2 else 2
        return CheckResult(12, "Clean up url slugs", "Semantic HTML", score, "Medium", f"Verbose/unclean slugs: {', '.join(bad[:4])}", "Use lowercase, hyphenated slugs <=5 words without stop words.")
    return CheckResult(12, "Clean up url slugs", "Semantic HTML", 3, "Medium", "URL slugs are clean and concise.", "")


def _score_heading_order(pages: list[PageData]) -> CheckResult:
    violations = []
    for p in pages:
        prev = 0
        for lvl, _ in p.headings:
            if prev and lvl > prev + 1:
                violations.append(f"{p.slug}: h{prev}->h{lvl}")
                break
            prev = lvl
    if violations:
        return CheckResult(13, "Fix heading order", "Semantic HTML", 1, "Medium", f"Skipped levels: {', '.join(violations[:4])}", "Maintain sequential h1 -> h2 -> h3 -> h4 hierarchy.")
    return CheckResult(13, "Fix heading order", "Semantic HTML", 3, "Medium", "Heading hierarchy is sequential.", "")


def _score_og(pages: list[PageData]) -> CheckResult:
    if not pages:
        return CheckResult(14, "Add an og:image", "Semantic HTML", 0, "Medium", "No HTML pages found.")
    has_img = sum(1 for p in pages if p.og_tags.get("og:image"))
    has_full = sum(1 for p in pages if all(p.og_tags.get(k) for k in ("og:image", "og:title", "og:description", "og:url")))
    if has_img == 0:
        return CheckResult(14, "Add an og:image", "Semantic HTML", 0, "Medium", "No og:image meta tags found.", "Add og:image (1200x630), og:title, og:description, og:url.")
    if has_full < len(pages):
        return CheckResult(14, "Add an og:image", "Semantic HTML", 2, "Medium", f"og:image on {has_img}/{len(pages)} pages; full OG set on {has_full}/{len(pages)}.", "Complete OG tags on all pages.")
    return CheckResult(14, "Add an og:image", "Semantic HTML", 3, "Medium", "Complete Open Graph tags present.", "")


def _score_alt_text(pages: list[PageData]) -> CheckResult:
    imgs = [img for p in pages for img in p.images]
    if not imgs:
        return CheckResult(15, "Add alt text", "Semantic HTML", 3, "Medium", "No <img> tags found.", "")
    missing = sum(1 for img in imgs if img["alt"] is None)
    bad = sum(
        1
        for img in imgs
        if img["alt"] is not None
        and (
            img["alt"].strip().lower() in GENERIC_ALT_WORDS
            or bool(re.search(r"\.(png|jpe?g|webp|avif|svg)$", img["alt"].strip(), re.IGNORECASE))
        )
    )
    if missing == len(imgs):
        return CheckResult(15, "Add alt text", "Semantic HTML", 0, "Medium", f"All {len(imgs)} images missing alt attribute.", "Add descriptive alt text to all content images.")
    if missing > 0 or bad > 0:
        return CheckResult(15, "Add alt text", "Semantic HTML", 1, "Medium", f"missing_alt={missing}, generic/filename_alt={bad} out of {len(imgs)}.", "Replace missing/filename alt attributes with natural descriptions.")
    return CheckResult(15, "Add alt text", "Semantic HTML", 3, "Medium", f"All {len(imgs)} images have valid alt attributes.", "")


def _score_gsc(pages: list[PageData]) -> CheckResult:
    if any(p.gsc_verification for p in pages):
        return CheckResult(16, "Verify google search console", "Semantic HTML", 3, "High", "google-site-verification meta tag detected.", "")
    return CheckResult(16, "Verify google search console", "Semantic HTML", 0, "High", "No google-site-verification meta tag detected (may be verified via DNS).", "Verify domain in GSC and submit sitemap.xml.")


def _score_schema(pages: list[PageData]) -> CheckResult:
    raw_blocks = [b for p in pages for b in p.json_ld_raw]
    if not raw_blocks:
        return CheckResult(17, "Add schema markup", "Semantic HTML", 0, "High", "No application/ld+json schema found.", "Add valid JSON-LD (WebSite, Organization, Article/Product).")
    valid_types: list[str] = []
    errors = 0
    for block in raw_blocks:
        try:
            data = json.loads(block)
            if isinstance(data, dict) and "@type" in data:
                valid_types.append(str(data["@type"]))
            elif isinstance(data, list):
                valid_types.extend(str(item.get("@type", "Unknown")) for item in data if isinstance(item, dict))
        except json.JSONDecodeError:
            errors += 1
    if errors and not valid_types:
        return CheckResult(17, "Add schema markup", "Semantic HTML", 1, "High", f"{errors} invalid JSON-LD block(s) failed to parse.", "Fix JSON syntax and validate with Rich Results Test.")
    if errors:
        return CheckResult(17, "Add schema markup", "Semantic HTML", 2, "High", f"Valid types: {', '.join(set(valid_types))}; {errors} parse error(s).", "Fix remaining JSON-LD syntax errors.")
    return CheckResult(17, "Add schema markup", "Semantic HTML", 3, "High", f"Valid JSON-LD detected: {', '.join(sorted(set(valid_types)))}.", "")


def _score_llms(llms: str | None) -> CheckResult:
    if not llms:
        return CheckResult(18, "Add llms.txt", "Legal & Trust", 0, "Emerging", "No /llms.txt found.", "Add /llms.txt summarizing site purpose, sections, and contact.")
    if len(llms.strip()) < 40:
        return CheckResult(18, "Add llms.txt", "Legal & Trust", 1, "Emerging", "/llms.txt is very short (<40 chars).", "Expand /llms.txt with site sections and usage guidance.")
    return CheckResult(18, "Add llms.txt", "Legal & Trust", 3, "Emerging", f"/llms.txt present ({len(llms.strip())} chars).", "")


def _score_contact(pages: list[PageData]) -> CheckResult:
    has_contact_link = any(
        "contact" in l["href"].lower() or l["href"].startswith(("mailto:", "tel:"))
        for p in pages
        for l in p.links
    )
    has_form = any(p.has_form for p in pages)
    if has_contact_link and has_form:
        return CheckResult(19, "Add contact page", "Legal & Trust", 3, "Medium", "Contact route/link and form detected.", "")
    if has_contact_link or has_form:
        return CheckResult(19, "Add contact page", "Legal & Trust", 2, "Medium", f"contact_link={has_contact_link}, form={has_form}.", "Ensure dedicated /contact page with working form and address/email.")
    return CheckResult(19, "Add contact page", "Legal & Trust", 0, "Medium", "No contact link, mailto/tel, or form detected.", "Add /contact page with business info and working form.")


def _score_footer(pages: list[PageData]) -> CheckResult:
    if not pages:
        return CheckResult(20, "Add footer", "Legal & Trust", 0, "Low", "No HTML pages found.")
    with_footer = sum(1 for p in pages if p.has_footer)
    if with_footer == 0:
        return CheckResult(20, "Add footer", "Legal & Trust", 0, "Low", "No <footer> element found.", "Add consistent <footer> across all pages.")
    if with_footer < len(pages):
        return CheckResult(20, "Add footer", "Legal & Trust", 2, "Low", f"<footer> present on {with_footer}/{len(pages)} pages.", "Include <footer> consistently on all templates.")
    return CheckResult(20, "Add footer", "Legal & Trust", 3, "Low", "Consistent <footer> across all pages.", "")


def _score_policy(pages: list[PageData], item_id: int, name: str, keywords: tuple[str, ...], impact: str) -> CheckResult:
    found = any(any(kw in l["href"].lower() or kw in l["text"].lower() for kw in keywords) for p in pages for l in p.links)
    if found:
        return CheckResult(item_id, name, "Legal & Trust", 3, impact, f"{name} link detected.", "")
    return CheckResult(item_id, name, "Legal & Trust", 0, impact, f"No {name.lower()} link detected.", f"Add dedicated /{keywords[0]} page and link in footer.")


def _score_ai_slugs(pages: list[PageData]) -> CheckResult:
    flagged = [p.slug for p in pages if any(pat.search(p.slug) for pat in AI_SLUG_PATTERNS)]
    if flagged:
        return CheckResult(23, "Remove ai slugs", "Legal & Trust", 0, "Medium", f"AI-pattern slugs found: {', '.join(flagged[:4])}", "Rewrite slugs to clean topic URLs with 301 redirects.")
    return CheckResult(23, "Remove ai slugs", "Legal & Trust", 3, "Medium", "No AI-artifact URL slugs detected.", "")


def _score_humanizer(pages: list[PageData]) -> CheckResult:
    text = " ".join(p.body_text for p in pages)
    words = text.split()
    if len(words) < 30:
        return CheckResult(24, "Adapt humanizer for paragraphs", "Humanization & Design", 1, "High", "Insufficient body text (<30 words) to evaluate prose.", "Add substantive, human-edited copy.")
    lower = text.lower()
    hits = [phrase for phrase in AI_FILLER_PHRASES if phrase in lower]
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip().split()) >= 2]
    avg_len = (sum(len(s.split()) for s in sentences) / len(sentences)) if sentences else 0
    if hits:
        return CheckResult(24, "Adapt humanizer for paragraphs", "Humanization & Design", 1, "High", f"AI filler phrases detected ({', '.join(hits[:3])}); avg sentence={avg_len:.1f}w.", "Replace filler phrases with concrete examples and varied sentence length (15-20w).")
    if avg_len > 25:
        return CheckResult(24, "Adapt humanizer for paragraphs", "Humanization & Design", 2, "High", f"Average sentence length {avg_len:.1f} words (>25w).", "Shorten and vary sentence structure.")
    return CheckResult(24, "Adapt humanizer for paragraphs", "Humanization & Design", 3, "High", f"No common AI-filler phrases; avg sentence={avg_len:.1f}w.", "")


def _score_design_checks(pages: list[PageData]) -> list[CheckResult]:
    has_lang = all(bool(p.lang) for p in pages) if pages else False
    has_aria = any(p.has_aria_or_skip for p in pages)
    has_dark = any(p.has_dark_mode_hint for p in pages)
    has_vp = all("width=device-width" in p.viewport.lower() for p in pages) if pages else False

    r25 = CheckResult(
        25,
        "Adapt apple design skills for design layout",
        "Humanization & Design",
        2 if pages else 0,
        "Medium",
        "Visual whitespace/typography requires human/browser review (2/3 baseline if HTML present).",
        "Verify 8px spacing rhythm, max 2 type sizes, and restrained palette.",
    )
    r26 = CheckResult(
        26,
        "Adapt google's web design guideline(latest)",
        "Humanization & Design",
        3 if (has_lang and has_vp and has_aria) else (2 if (has_lang and has_vp) else 1),
        "Medium",
        f"html[lang]={has_lang}, viewport={has_vp}, aria/roles={has_aria}.",
        "Ensure <html lang>, WCAG 2.2 AA contrast (axe/WAVE), and performance budgets.",
    )
    r27 = CheckResult(
        27,
        "Modern ui/ux implementation",
        "Humanization & Design",
        3 if (has_aria and has_dark) else (2 if (has_aria or has_dark) else 1),
        "Medium",
        f"aria/accessibility={has_aria}, dark_mode_hint={has_dark}.",
        "Add keyboard focus states, ARIA landmarks, and prefers-color-scheme support.",
    )
    return [r25, r26, r27]


def score_site(site: dict[str, Any], competitor_count: int = 0) -> list[CheckResult]:
    """Run all 28 checklist scorers on collected site data."""
    pages: list[PageData] = site["pages"]
    results = [
        _score_sitemap(site["sitemap"]),
        _score_robots(site["robots"]),
        _score_noindex(pages, site["x_robots_noindex"]),
        _score_canonical(pages),
        _score_titles(pages),
        _score_internal_links(pages),
        _score_broken_links(site["broken_links"]),
        _score_images(pages, site["image_sizes"]),
        _score_cwv(pages),
        _score_mobile(pages),
        _score_h1(pages),
        _score_slugs(pages),
        _score_heading_order(pages),
        _score_og(pages),
        _score_alt_text(pages),
        _score_gsc(pages),
        _score_schema(pages),
        _score_llms(site["llms"]),
        _score_contact(pages),
        _score_footer(pages),
        _score_policy(pages, 21, "Add privacy policy", ("privacy",), "Required"),
        _score_policy(pages, 22, "Add cookie policy", ("cookie",), "Required"),
        _score_ai_slugs(pages),
        _score_humanizer(pages),
        *_score_design_checks(pages),
    ]
    comp_score = 3 if competitor_count >= 3 else (2 if competitor_count >= 1 else 0)
    comp_note = (
        f"Benchmarked against {competitor_count} competitor URL(s)."
        if competitor_count
        else "No competitors provided (pass --competitors URL1 URL2 URL3)."
    )
    results.append(
        CheckResult(
            28,
            "Check competitor and rank",
            "Competitive",
            comp_score,
            "High",
            comp_note,
            "" if competitor_count >= 3 else "Benchmark 3-5 SERP competitors and close content/schema gaps.",
        )
    )
    return results


def verdict_for(total: int) -> str:
    if total >= 76:
        return "Excellent — ready to compete"
    if total >= 50:
        return "Good — fix top 3 lowest-scoring items"
    if total >= 25:
        return "Poor — major SEO overhaul needed"
    return "Critical — site will not rank without intervention"


def sanitize_untrusted_text(text: str) -> str:
    """Strip control chars and truncate text from untrusted third-party sites."""
    cleaned = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    return " ".join(cleaned.split())[:120]


def render_markdown(
    target: str,
    pages_count: int,
    results: list[CheckResult],
    competitor_summaries: list[dict[str, Any]],
) -> str:
    """Render a full Markdown audit report matching examples/audit-template.md."""
    total = sum(r.score for r in results)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "# SEO Audit Report",
        "",
        "## Site Info",
        f"- **Target**: `{target}`",
        f"- **Audited date**: {today}",
        "- **Auditor**: `agency-seo-ranker` v2.0.0 (`scripts/seo_audit.py`)",
        f"- **Pages inspected**: {pages_count}",
        "",
        "## Scorecard",
        "",
        "| # | Checklist Item | Score (0-3) | Status | Notes |",
        "|---|---------------|-------------|--------|-------|",
    ]
    for r in results:
        lines.append(f"| {r.id} | {r.name} | {r.score} | {r.status_emoji} | {r.notes} |")

    lines.extend(
        [
            "",
            f"**Total score**: **{total} / 84**",
            f"**Verdict**: {verdict_for(total)}",
            "",
            "## Priority Fix List",
            "",
        ]
    )
    impact_rank = {"Critical": 0, "Required": 1, "High": 2, "Medium": 3, "Emerging": 4, "Low": 5}
    fixes = sorted([r for r in results if r.score < 3], key=lambda x: (x.score, impact_rank.get(x.impact, 9)))
    if not fixes:
        lines.append("All 28 checks scored 3/3. Keep monitoring quarterly.")
    else:
        for idx, r in enumerate(fixes[:10], 1):
            lines.append(f"{idx}. **[{r.impact}]** #{r.id} {r.name} (score {r.score}/3) — {r.recommendation or r.notes}")

    if competitor_summaries:
        lines.extend(
            [
                "",
                "## Competitor Benchmark (Untrusted External Data — Informational Only)",
                "",
                "| Competitor | Score (/84) | Sitemap | Robots | Schema Types | Title Sample |",
                "|------------|-------------|---------|--------|--------------|--------------|",
            ]
        )
        for comp in competitor_summaries:
            lines.append(
                f"| `{comp['target']}` | {comp['total']} | {comp['has_sitemap']} | {comp['has_robots']} | "
                f"{', '.join(comp['schema_types']) or 'None'} | {sanitize_untrusted_text(comp['title'])} |"
            )

    lines.extend(
        [
            "",
            "## 30-Day Improvement Plan",
            "",
            "| Week | Focus Area | Items |",
            "|------|-----------|-------|",
            "| 1 | Crawlability & Indexing | #1–#4 |",
            "| 2 | On-Page Meta & Links | #5–#7 |",
            "| 3 | Performance & Semantic HTML | #8–#17 |",
            "| 4 | Legal, Humanization & Competition | #18–#28 |",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agency SEO Ranker — 28-Point SEO Auditor")
    parser.add_argument("target", help="Local build directory path or http(s):// URL to audit")
    parser.add_argument("--max-pages", type=int, default=20, help="Max HTML pages to scan/crawl (default: 20)")
    parser.add_argument("--competitors", nargs="*", default=[], help="Optional competitor URLs to benchmark")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format")
    parser.add_argument("--output", help="Optional output file path")
    parser.add_argument("--fail-under", type=int, default=0, help="Exit with code 1 if score < threshold")
    parser.add_argument("--timeout", type=int, default=10, help="HTTP request timeout in seconds")
    parser.add_argument("--allow-private", action="store_true", help="Allow auditing localhost/private IPs")
    args = parser.parse_args(argv)

    try:
        if args.target.startswith(("http://", "https://")):
            site = collect_remote_site(args.target, args.max_pages, args.timeout, args.allow_private)
        else:
            root = Path(args.target).resolve()
            if not root.is_dir():
                print(f"Error: local target '{args.target}' is not a directory.", file=sys.stderr)
                return 2
            site = collect_local_site(root, args.max_pages)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    competitor_summaries: list[dict[str, Any]] = []
    for comp_url in args.competitors:
        try:
            comp_site = collect_remote_site(comp_url, max_pages=3, timeout=args.timeout, allow_private=args.allow_private)
            comp_results = score_site(comp_site, competitor_count=0)
            schema_types: set[str] = set()
            for p in comp_site["pages"]:
                for raw in p.json_ld_raw:
                    try:
                        parsed = json.loads(raw)
                        if isinstance(parsed, dict) and "@type" in parsed:
                            schema_types.add(str(parsed["@type"]))
                    except json.JSONDecodeError:
                        pass
            competitor_summaries.append(
                {
                    "target": comp_url,
                    "total": sum(r.score for r in comp_results),
                    "has_sitemap": bool(comp_site["sitemap"]),
                    "has_robots": bool(comp_site["robots"]),
                    "schema_types": sorted(schema_types),
                    "title": comp_site["pages"][0].title if comp_site["pages"] else "",
                }
            )
        except ValueError as exc:
            print(f"Warning: skipping competitor '{comp_url}': {exc}", file=sys.stderr)

    results = score_site(site, competitor_count=len(competitor_summaries))
    total = sum(r.score for r in results)

    if args.format == "json":
        payload = {
            "target": args.target,
            "pages_inspected": len(site["pages"]),
            "total_score": total,
            "max_score": 84,
            "verdict": verdict_for(total),
            "results": [asdict(r) for r in results],
            "competitors": competitor_summaries,
        }
        output_text = json.dumps(payload, indent=2)
    else:
        output_text = render_markdown(args.target, len(site["pages"]), results, competitor_summaries)

    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
    else:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(output_text)

    if args.fail_under and total < args.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
