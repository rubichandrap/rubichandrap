#!/usr/bin/env python3
"""Regenerate the stat cards in the profile README from the GitHub API.

Stdlib only. Run by .github/workflows/update-stats.yml once a day.
Prints STATS_CHANGED (README rewritten) or STATS_UNCHANGED (no diff).
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone

USER = "rubichandrap"
README = "README.md"
START = "<!-- STATS:START -->"
END = "<!-- STATS:END -->"


def api(path: str):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"User-Agent": "rubi-stats-bot", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def card(num, label, sub=""):
    s = ('<td align="center" style="width: 25%; background: #161b22; '
         'border: 1px solid #30363d; border-radius: 10px; padding: 12px 6px;">\n'
         f'<div style="font-size: 24px; font-weight: 800; color: #e6edf3; line-height: 1.2;">{num}</div>\n'
         f'<div style="font-size: 11px; letter-spacing: 1px; color: #8b949e;">{label}</div>\n')
    if sub:
        s += f'<div style="font-size: 11px; color: #8b949e;">{sub}</div>\n'
    return s + "</td>"


def main() -> int:
    user = api(f"/users/{USER}")

    # paginate in case the profile outgrows 100 repos
    repos, page = [], 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}&sort=updated")
        if not batch:
            break
        repos += batch
        if len(repos) >= user["public_repos"]:
            break
        page += 1

    own = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in repos)  # includes fork stars, like GitHub's profile total

    block = "\n".join([
        "<tr>",
        card(len(repos), "REPOS", f"{len(own)} own"),
        card(stars, "STARS"),
        card(user["followers"], "FOLLOWERS"),
        card(user["following"], "FOLLOWING"),
        "</tr>",
        f"<!-- synced: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC -->",
    ])

    text = open(README, encoding="utf-8").read()
    i = text.index(START)
    j = text.index(END)
    new = text[: i + len(START)] + "\n" + block + "\n" + text[j:]
    if new == text:
        print("STATS_UNCHANGED")
        return 0
    open(README, "w", encoding="utf-8").write(new)
    print("STATS_CHANGED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
