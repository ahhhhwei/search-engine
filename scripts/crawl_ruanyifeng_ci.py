#!/usr/bin/env python3
"""CI-safe entry point for the Ruan Yifeng corpus crawler.

The original project crawler disables TLS verification for ruanyifeng.com because
that host has historically produced certificate-chain failures in some Linux CI
environments. This wrapper preserves the main crawler logic while making network
startup failures visible and recoverable in GitHub Actions.
"""

from __future__ import annotations

import sys
import traceback
from urllib.robotparser import RobotFileParser

import requests
import urllib3

import crawl_ruanyifeng as crawler

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
    "ahhhhwei-search-engine/1.2"
)


def log(message: str, *, error: bool = False) -> None:
    print(message, file=sys.stderr if error else sys.stdout, flush=True)


def build_ci_session() -> requests.Session:
    session = crawler.build_session()
    session.headers["User-Agent"] = BROWSER_USER_AGENT
    session.headers["Connection"] = "keep-alive"

    # This is a read-only crawl of a public site. The repository's original
    # crawler also disables verification for this domain to avoid CI-specific
    # certificate-chain errors.
    session.verify = False
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return session


def load_robots_without_startup_abort(
    session: requests.Session, timeout: float
) -> RobotFileParser:
    parser = RobotFileParser()
    parser.set_url(crawler.ROBOTS_URL)

    try:
        response = session.get(
            crawler.ROBOTS_URL,
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException as error:
        log(
            f"warning: robots.txt could not be fetched; treating it as unavailable: {error}",
            error=True,
        )
        parser.parse([])
        return parser

    if response.status_code == 200:
        parser.parse(response.text.splitlines())
        if not parser.can_fetch(BROWSER_USER_AGENT, crawler.ARCHIVE_URL):
            raise RuntimeError(
                f"robots.txt does not permit fetching {crawler.ARCHIVE_URL}"
            )
        return parser

    # RFC 9309 treats most 4xx responses as an unavailable robots file rather
    # than a prohibition. 429 remains an error because it signals throttling.
    if 400 <= response.status_code < 500 and response.status_code != 429:
        log(
            f"warning: robots.txt returned HTTP {response.status_code}; "
            "treating it as unavailable",
            error=True,
        )
        parser.parse([])
        return parser

    response.raise_for_status()
    parser.parse([])
    return parser


def main() -> int:
    crawler.USER_AGENT = BROWSER_USER_AGENT
    crawler.build_session = build_ci_session
    crawler.check_robots = load_robots_without_startup_abort
    return crawler.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as error:
        log(
            f"::error title=Ruan Yifeng crawl failed::"
            f"{type(error).__name__}: {error}",
            error=True,
        )
        traceback.print_exc()
        raise SystemExit(1)
