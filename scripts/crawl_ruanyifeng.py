#!/usr/bin/env python3
"""Build the browser-search corpus from Ruan Yifeng's public blog archives."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.ruanyifeng.com"
ARCHIVE_URL = f"{BASE_URL}/blog/archives.html"
ROBOTS_URL = f"{BASE_URL}/robots.txt"
ARTICLE_RE = re.compile(
    r"^https://www\.ruanyifeng\.com/blog/\d{4}/\d{2}/[^/?#]+\.html$"
)
CATEGORY_RE = re.compile(
    r"^https://www\.ruanyifeng\.com/blog/[A-Za-z0-9_-]+(?:/index\.html|/)?$"
)
USER_AGENT = "ahhhhwei-search-engine/1.1 (+https://github.com/ahhhhwei/search-engine)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-url", default=ARCHIVE_URL)
    parser.add_argument("--output", default="web/data/documents.json")
    parser.add_argument("--max-pages", type=int, default=0, help="0 means all discovered articles")
    parser.add_argument("--max-content-chars", type=int, default=20000)
    parser.add_argument("--max-discovery-pages", type=int, default=50)
    parser.add_argument("--min-documents", type=int, default=100)
    parser.add_argument("--delay", type=float, default=0.10)
    parser.add_argument("--timeout", type=float, default=25.0)
    return parser.parse_args()


def build_session() -> requests.Session:
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.5",
        }
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def canonicalize(url: str) -> str:
    parts = urlsplit(url)
    host = parts.netloc.lower()
    if host == "ruanyifeng.com":
        host = "www.ruanyifeng.com"
    path = parts.path or "/"
    return urlunsplit(("https", host, path, "", ""))


def check_robots(session: requests.Session, timeout: float) -> RobotFileParser:
    parser = RobotFileParser()
    parser.set_url(ROBOTS_URL)
    response = session.get(ROBOTS_URL, timeout=timeout)
    if response.status_code == 404:
        parser.parse([])
        return parser
    response.raise_for_status()
    parser.parse(response.text.splitlines())
    if not parser.can_fetch(USER_AGENT, ARCHIVE_URL):
        raise RuntimeError(f"robots.txt does not permit fetching {ARCHIVE_URL}")
    return parser


def fetch_html(session: requests.Session, url: str, timeout: float) -> str:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding or "utf-8"
    return response.text


def discover_links(html: str, source_url: str) -> tuple[set[str], set[str]]:
    soup = BeautifulSoup(html, "html.parser")
    article_urls: set[str] = set()
    category_urls: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        url = canonicalize(urljoin(source_url, anchor["href"]))
        if ARTICLE_RE.fullmatch(url):
            article_urls.add(url)
        elif CATEGORY_RE.fullmatch(url):
            category_urls.add(url)
    return article_urls, category_urls


def discover_articles(
    session: requests.Session,
    robots: RobotFileParser,
    archive_url: str,
    timeout: float,
    max_discovery_pages: int,
) -> list[str]:
    """Discover article URLs from the main archive and its category archives.

    The main archive only exposes the newest articles directly. Category archive
    pages contain the historical article links, so relying on archives.html alone
    makes the crawl brittle and incomplete.
    """
    archive_html = fetch_html(session, archive_url, timeout)
    article_urls, category_urls = discover_links(archive_html, archive_url)

    category_urls.discard(canonicalize(f"{BASE_URL}/blog/"))
    ordered_categories = sorted(category_urls)
    if max_discovery_pages > 0:
        ordered_categories = ordered_categories[:max_discovery_pages]

    print(
        f"main archive exposed {len(article_urls)} article URLs and "
        f"{len(ordered_categories)} category archives"
    )

    successful_categories = 0
    for index, category_url in enumerate(ordered_categories, start=1):
        if not robots.can_fetch(USER_AGENT, category_url):
            print(f"skip discovery page disallowed by robots.txt: {category_url}", file=sys.stderr)
            continue
        try:
            category_html = fetch_html(session, category_url, timeout)
            discovered, _ = discover_links(category_html, category_url)
            article_urls.update(discovered)
            successful_categories += 1
            print(
                f"discovery {index}/{len(ordered_categories)}: "
                f"{category_url} -> {len(discovered)} articles; "
                f"total unique {len(article_urls)}"
            )
        except requests.RequestException as error:
            print(f"skip discovery page failure: {category_url}: {error}", file=sys.stderr)

    if successful_categories == 0:
        raise RuntimeError("no category archive page could be fetched")
    if len(article_urls) < 100:
        raise RuntimeError(
            f"only {len(article_urls)} article URLs were discovered; expected at least 100"
        )

    # The URL path begins with YYYY/MM, so reverse lexical order is newest first.
    return sorted(article_urls, reverse=True)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_title(soup: BeautifulSoup) -> str:
    if soup.title:
        title = normalize_text(soup.title.get_text(" ", strip=True))
    else:
        heading = soup.find(["h1", "h2"])
        title = normalize_text(heading.get_text(" ", strip=True)) if heading else ""
    for suffix in (" - 阮一峰的网络日志", " | 阮一峰的网络日志", "_阮一峰的网络日志"):
        if title.endswith(suffix):
            title = title[: -len(suffix)].strip()
    return title


def select_article_root(soup: BeautifulSoup):
    selectors = (
        ".asset-content.entry-content",
        ".entry-content",
        ".asset-content",
        "article",
        "#main-content",
        "#content",
        ".content",
    )
    for selector in selectors:
        node = soup.select_one(selector)
        if node and len(normalize_text(node.get_text(" ", strip=True))) >= 80:
            return node
    return soup.body or soup


def parse_article(html: str, url: str, max_content_chars: int) -> dict[str, str] | None:
    soup = BeautifulSoup(html, "html.parser")
    title = clean_title(soup)
    root = select_article_root(soup)
    for node in root.select(
        "script, style, noscript, nav, footer, form, .asset-meta, .asset-footer, "
        ".module, #comments, .comments, .comment, .entry-tags, .entry-categories"
    ):
        node.decompose()
    content = normalize_text(root.get_text(" ", strip=True))
    if not title or len(content) < 80:
        return None
    if max_content_chars > 0:
        content = content[:max_content_chars]
    return {"title": title, "url": url, "content": content}


def crawl(
    session: requests.Session,
    robots: RobotFileParser,
    urls: Iterable[str],
    timeout: float,
    delay: float,
    max_content_chars: int,
) -> list[dict[str, str]]:
    documents: list[dict[str, str]] = []
    urls = list(urls)
    for index, url in enumerate(urls, start=1):
        if not robots.can_fetch(USER_AGENT, url):
            print(f"skip disallowed by robots.txt: {url}", file=sys.stderr)
            continue
        try:
            html = fetch_html(session, url, timeout)
            document = parse_article(html, url, max_content_chars)
            if document:
                documents.append(document)
            else:
                print(f"skip unparseable article: {url}", file=sys.stderr)
        except requests.RequestException as error:
            print(f"skip fetch failure: {url}: {error}", file=sys.stderr)
        if index == 1 or index % 25 == 0 or index == len(urls):
            print(f"processed {index}/{len(urls)}; accepted {len(documents)}")
        if delay > 0:
            time.sleep(delay)
    return documents


def write_documents(
    documents: list[dict[str, str]], output: Path, min_documents: int
) -> None:
    if len(documents) < min_documents:
        raise RuntimeError(
            f"only {len(documents)} documents were produced; "
            f"minimum is {min_documents}; refusing to deploy"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(documents, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)
    print(f"wrote {len(documents)} documents to {output}")


def main() -> int:
    args = parse_args()
    session = build_session()
    robots = check_robots(session, args.timeout)
    urls = discover_articles(
        session,
        robots,
        args.archive_url,
        args.timeout,
        args.max_discovery_pages,
    )
    if args.max_pages > 0:
        urls = urls[: args.max_pages]
    print(f"crawling {len(urls)} of the discovered article URLs")
    documents = crawl(
        session,
        robots,
        urls,
        args.timeout,
        args.delay,
        args.max_content_chars,
    )
    write_documents(documents, Path(args.output), args.min_documents)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
