#!/usr/bin/env python3
"""Generate browser-search JSON from the official ruanyf/weekly Markdown corpus."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

ISSUE_RE = re.compile(r"issue-(\d+)\.md$")
LINK_RE = re.compile(r"\[([^\]]+)\]\((?:[^()]|\([^)]*\))*\)")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\((?:[^()]|\([^)]*\))*\)")
HTML_RE = re.compile(r"<[^>]+>")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.S)
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
MARKDOWN_PREFIX_RE = re.compile(
    r"(?m)^\s{0,3}(?:#{1,6}\s+|>\s?|[-*+]\s+|\d+[.)]\s+)"
)
DECORATION_RE = re.compile(r"[*_~]{1,3}")
WHITESPACE_RE = re.compile(r"\s+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=".corpus/weekly/docs")
    parser.add_argument("--output", default="web/data/documents.json")
    parser.add_argument(
        "--source-revision",
        default="07fea239b574fa2677bdb60696eb117184bd9b0d",
    )
    parser.add_argument("--max-content-chars", type=int, default=15000)
    parser.add_argument("--min-documents", type=int, default=300)
    return parser.parse_args()


def plain_text(markdown: str) -> str:
    text = COMMENT_RE.sub(" ", markdown)
    text = IMAGE_RE.sub(" ", text)
    text = FENCE_RE.sub(lambda match: " " + match.group(1) + " ", text)
    text = LINK_RE.sub(lambda match: match.group(1), text)
    text = INLINE_CODE_RE.sub(lambda match: match.group(1), text)
    text = HTML_RE.sub(" ", text)
    text = MARKDOWN_PREFIX_RE.sub("", text)
    text = DECORATION_RE.sub("", text)
    return WHITESPACE_RE.sub(" ", html.unescape(text)).strip()


def title_from_markdown(markdown: str, issue_number: int) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return f"科技爱好者周刊（第 {issue_number} 期）"


def issue_number(path: Path) -> int:
    match = ISSUE_RE.search(path.name)
    if not match:
        raise ValueError(f"not an issue file: {path}")
    return int(match.group(1))


def build_documents(
    source: Path, revision: str, max_content_chars: int
) -> list[dict[str, str]]:
    files = sorted(source.glob("issue-*.md"), key=issue_number, reverse=True)
    documents: list[dict[str, str]] = []

    for path in files:
        number = issue_number(path)
        markdown = path.read_text(encoding="utf-8")
        title = title_from_markdown(markdown, number)
        content = plain_text(markdown)
        if max_content_chars > 0:
            content = content[:max_content_chars]
        if not title or len(content) < 80:
            print(f"skip invalid corpus file: {path}")
            continue
        documents.append(
            {
                "title": title,
                "url": (
                    "https://github.com/ruanyf/weekly/blob/"
                    f"{revision}/docs/issue-{number}.md"
                ),
                "content": content,
            }
        )

    return documents


def main() -> int:
    args = parse_args()
    source = Path(args.source)
    if not source.is_dir():
        raise RuntimeError(f"official corpus directory does not exist: {source}")

    documents = build_documents(source, args.source_revision, args.max_content_chars)
    if len(documents) < args.min_documents:
        raise RuntimeError(
            f"only {len(documents)} official weekly documents were generated; "
            f"minimum is {args.min_documents}"
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(documents, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)
    print(f"generated {len(documents)} official Ruan Yifeng weekly documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
