#!/usr/bin/env python3
"""Build KOL seed rows from reviewed TweetClaw JSON or JSONL exports."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any


ROWS_KEYS = ("items", "tweets", "results", "data", "rows")
HANDLE_KEYS = (
    "authorUsername",
    "author_username",
    "screen_name",
    "username",
    "userName",
    "handle",
)
VIEW_KEYS = ("views", "viewCount", "view_count", "impressions")
LIKE_KEYS = ("likes", "likeCount", "like_count", "favorite_count")
DATE_KEYS = ("createdAt", "created_at", "postedAt", "posted_at", "date")


def load_rows(path: Path) -> list[Any]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ROWS_KEYS:
            rows = parsed.get(key)
            if isinstance(rows, list):
                return rows
        return [parsed]
    return []


def normalize_handle(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    match = re.search(r"(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})", value)
    if match:
        value = match.group(1)
    value = value.removeprefix("@")
    if re.fullmatch(r"[A-Za-z0-9_]{1,15}", value):
        return value
    return None


def extract_handle(row: Any) -> str | None:
    if not isinstance(row, dict):
        return None
    for key in HANDLE_KEYS:
        handle = normalize_handle(row.get(key))
        if handle:
            return handle
    for key in ("author", "user", "profile"):
        nested = row.get(key)
        if isinstance(nested, dict):
            handle = extract_handle(nested)
            if handle:
                return handle
    for key in ("url", "tweetUrl", "tweet_url", "profileUrl", "profile_url"):
        handle = normalize_handle(row.get(key))
        if handle:
            return handle
    return None


def number_from(row: dict[str, Any], keys: tuple[str, ...]) -> int | None:
    for key in keys:
        value = row.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            cleaned = value.replace(",", "").strip().upper()
            try:
                if cleaned.endswith("K"):
                    return int(float(cleaned[:-1]) * 1_000)
                if cleaned.endswith("M"):
                    return int(float(cleaned[:-1]) * 1_000_000)
                return int(float(cleaned))
            except ValueError:
                continue
    return None


def first_text(row: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def average(values: list[int]) -> int:
    if not values:
        return 0
    return round(sum(values) / len(values))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert TweetClaw exports into KOL seed rows.",
    )
    parser.add_argument("export", type=Path, help="TweetClaw JSON or JSONL export")
    args = parser.parse_args()

    groups: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for row in load_rows(args.export):
        if not isinstance(row, dict):
            continue
        handle = extract_handle(row)
        if not handle:
            continue
        key = handle.lower()
        group = groups.setdefault(
            key,
            {
                "handle": f"@{handle}",
                "account_url": f"https://x.com/{handle}",
                "source": "tweetclaw",
                "sample_posts": 0,
                "views": [],
                "likes": [],
                "last_post": "",
            },
        )
        group["sample_posts"] += 1
        view = number_from(row, VIEW_KEYS)
        like = number_from(row, LIKE_KEYS)
        if view is not None:
            group["views"].append(view)
        if like is not None:
            group["likes"].append(like)
        date_value = first_text(row, DATE_KEYS)
        if date_value and date_value > group["last_post"]:
            group["last_post"] = date_value

    output = []
    for group in groups.values():
        output.append(
            {
                "handle": group["handle"],
                "account_url": group["account_url"],
                "source": group["source"],
                "sample_posts": group["sample_posts"],
                "avg_views": average(group["views"]),
                "avg_likes": average(group["likes"]),
                "last_post": group["last_post"],
            },
        )

    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
