#!/usr/bin/env python3
"""Collect and lightly classify GitHub issues for OSS contribution scouting."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ISSUE_FIELDS = [
    "number",
    "title",
    "url",
    "state",
    "labels",
    "createdAt",
    "updatedAt",
    "comments",
    "author",
    "assignees",
    "milestone",
    "body",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect GitHub issues and render JSON/Markdown inventory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Examples:
              collect_github_issues.py owner/repo --limit 200 --output-dir ./out
              collect_github_issues.py https://github.com/owner/repo --state open --labels "good first issue,help wanted"
            """
        ),
    )
    parser.add_argument("repo", help="GitHub repository as owner/repo or GitHub URL")
    parser.add_argument("--state", default="open", choices=["open", "closed", "all"])
    parser.add_argument("--limit", type=int, default=200, help="Maximum issues to collect")
    parser.add_argument("--labels", default="", help="Comma-separated labels to filter")
    parser.add_argument("--output-dir", default=".", help="Directory for JSON and Markdown outputs")
    parser.add_argument("--prefix", default="issue_inventory", help="Output file prefix")
    args = parser.parse_args()

    repo = normalize_repo(args.repo)
    labels = [label.strip() for label in args.labels.split(",") if label.strip()]

    try:
        issues, source = collect_with_gh(repo, args.state, args.limit, labels)
    except RuntimeError as gh_error:
        try:
            issues, source = collect_with_rest(repo, args.state, args.limit, labels)
        except RuntimeError as rest_error:
            print(f"gh collection failed: {gh_error}", file=sys.stderr)
            print(f"REST collection failed: {rest_error}", file=sys.stderr)
            return 2

    enriched = [enrich_issue(issue) for issue in issues[: args.limit]]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "repo": repo,
        "state": args.state,
        "labels": labels,
        "limit": args.limit,
        "count": len(enriched),
        "source": source,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }

    json_path = output_dir / f"{args.prefix}.json"
    md_path = output_dir / f"{args.prefix}.md"
    json_path.write_text(json.dumps({"metadata": metadata, "issues": enriched}, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(metadata, enriched), encoding="utf-8")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


def normalize_repo(value: str) -> str:
    value = value.strip()
    if value.startswith("git@github.com:"):
        value = value.removeprefix("git@github.com:")
    if value.startswith("https://github.com/"):
        value = value.removeprefix("https://github.com/")
    if value.startswith("http://github.com/"):
        value = value.removeprefix("http://github.com/")
    value = value.removesuffix(".git").strip("/")
    parts = value.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise SystemExit(f"Invalid GitHub repo: {value!r}. Expected owner/repo or GitHub URL.")
    return f"{parts[0]}/{parts[1]}"


def collect_with_gh(repo: str, state: str, limit: int, labels: list[str]) -> tuple[list[dict[str, Any]], str]:
    if not shutil.which("gh"):
        raise RuntimeError("gh is not installed")

    cmd = [
        "gh",
        "issue",
        "list",
        "--repo",
        repo,
        "--state",
        state,
        "--limit",
        str(limit),
        "--json",
        ",".join(ISSUE_FIELDS),
    ]
    for label in labels:
        cmd.extend(["--label", label])

    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "gh issue list failed")
    return json.loads(result.stdout), "gh issue list"


def collect_with_rest(repo: str, state: str, limit: int, labels: list[str]) -> tuple[list[dict[str, Any]], str]:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "oss-contribution-scout",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    issues: list[dict[str, Any]] = []
    page = 1
    while len(issues) < limit:
        query = {
            "state": state,
            "per_page": min(100, max(1, limit - len(issues))),
            "page": page,
            "sort": "updated",
            "direction": "desc",
        }
        if labels:
            query["labels"] = ",".join(labels)
        url = f"https://api.github.com/repos/{repo}/issues?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {body[:300]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(str(exc)) from exc

        if not payload:
            break
        for item in payload:
            if "pull_request" in item:
                continue
            issues.append(rest_to_common_issue(item))
            if len(issues) >= limit:
                break
        page += 1

    return issues, "GitHub REST"


def rest_to_common_issue(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": item.get("number"),
        "title": item.get("title"),
        "url": item.get("html_url"),
        "state": item.get("state"),
        "labels": [{"name": label.get("name", "")} for label in item.get("labels", [])],
        "createdAt": item.get("created_at"),
        "updatedAt": item.get("updated_at"),
        "comments": item.get("comments", 0),
        "author": {"login": (item.get("user") or {}).get("login", "")},
        "assignees": [{"login": assignee.get("login", "")} for assignee in item.get("assignees", [])],
        "milestone": item.get("milestone"),
        "body": item.get("body") or "",
    }


def enrich_issue(issue: dict[str, Any]) -> dict[str, Any]:
    labels = label_names(issue)
    text = " ".join([issue.get("title") or "", " ".join(labels), issue.get("body") or ""]).lower()
    category = classify_category(text, labels)
    comments = comment_count(issue.get("comments"))
    priority = estimate_priority(text, labels, comments)
    difficulty = estimate_difficulty(text, labels, category)
    return {
        "number": issue.get("number"),
        "title": issue.get("title") or "",
        "url": issue.get("url") or "",
        "state": issue.get("state") or "",
        "labels": labels,
        "created_at": issue.get("createdAt") or "",
        "updated_at": issue.get("updatedAt") or "",
        "comments": comments,
        "author": login(issue.get("author")),
        "assignees": [login(assignee) for assignee in issue.get("assignees") or [] if login(assignee)],
        "milestone": milestone_title(issue.get("milestone")),
        "category_hint": category,
        "priority_hint": priority,
        "difficulty_hint": difficulty,
        "body_excerpt": excerpt(issue.get("body") or "", 500),
    }


def label_names(issue: dict[str, Any]) -> list[str]:
    labels = []
    for label in issue.get("labels") or []:
        if isinstance(label, str):
            labels.append(label)
        elif isinstance(label, dict):
            labels.append(str(label.get("name") or ""))
    return [label for label in labels if label]


def login(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("login") or "")
    return str(value or "")


def milestone_title(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("title") or "")
    return str(value or "")


def comment_count(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, list):
        return len(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def excerpt(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def classify_category(text: str, labels: list[str]) -> str:
    joined = " ".join(label.lower() for label in labels) + " " + text
    checks = [
        ("security/private", r"\b(security|vulnerability|cve|xss|csrf|ssrf|rce|auth bypass)\b"),
        ("bug", r"\b(bug|regression|crash|incorrect|broken|fail|error|exception)\b"),
        ("docs", r"\b(doc|docs|documentation|readme|example|tutorial)\b"),
        ("tests", r"\b(test|flaky|coverage|fixture|ci)\b"),
        ("tooling", r"\b(build|lint|format|workflow|github action|dependency|deps|package)\b"),
        ("performance", r"\b(perf|performance|slow|latency|memory|cpu|optimi[sz])\b"),
        ("feature", r"\b(feature|enhancement|request|support|add)\b"),
    ]
    for category, pattern in checks:
        if re.search(pattern, joined):
            return category
    return "triage"


def estimate_priority(text: str, labels: list[str], comments: int) -> str:
    joined = " ".join(label.lower() for label in labels) + " " + text
    if re.search(r"\b(security|vulnerability|cve|data loss|rce|auth bypass)\b", joined):
        return "P0"
    if re.search(r"\b(priority|critical|regression|bug|crash|release blocker|help wanted)\b", joined):
        return "P1"
    if comments >= 5 or re.search(r"\b(good first issue|docs|test|ci|flaky|enhancement)\b", joined):
        return "P2"
    return "P3"


def estimate_difficulty(text: str, labels: list[str], category: str) -> str:
    joined = " ".join(label.lower() for label in labels) + " " + text
    if re.search(r"\b(typo|broken link|docs|documentation|readme)\b", joined):
        return "XS"
    if re.search(r"\b(good first issue|easy|beginner|small|help wanted)\b", joined):
        return "S"
    if category in {"bug", "tests", "tooling", "feature"}:
        return "M"
    if re.search(r"\b(refactor|architecture|migration|api change|performance|concurrency|database|compiler|kernel)\b", joined):
        return "L"
    if category == "security/private":
        return "XL"
    return "M"


def render_markdown(metadata: dict[str, Any], issues: list[dict[str, Any]]) -> str:
    lines = [
        f"# GitHub Issue Inventory: {metadata['repo']}",
        "",
        f"- Generated UTC: {metadata['generated_at_utc']}",
        f"- State: {metadata['state']}",
        f"- Labels: {', '.join(metadata['labels']) if metadata['labels'] else 'all'}",
        f"- Count: {metadata['count']}",
        f"- Source: {metadata['source']}",
        "",
        "| Priority Hint | Difficulty Hint | Category Hint | Issue | Labels | Updated | Comments |",
        "|---|---|---|---|---|---|---:|",
    ]
    for issue in issues:
        title = escape_table(issue["title"])
        url = issue["url"]
        issue_link = f"[#{issue['number']} {title}]({url})" if url else f"#{issue['number']} {title}"
        labels = escape_table(", ".join(issue["labels"]))
        updated = escape_table(issue["updated_at"][:10])
        lines.append(
            "| {priority} | {difficulty} | {category} | {issue} | {labels} | {updated} | {comments} |".format(
                priority=issue["priority_hint"],
                difficulty=issue["difficulty_hint"],
                category=issue["category_hint"],
                issue=issue_link,
                labels=labels,
                updated=updated,
                comments=issue["comments"],
            )
        )
    lines.append("")
    lines.append("Hints are starting points only. Re-score final recommendations with `references/scoring.md` and repository evidence.")
    lines.append("")
    return "\n".join(lines)


def escape_table(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
