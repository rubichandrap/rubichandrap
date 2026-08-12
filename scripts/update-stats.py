#!/usr/bin/env python3
"""Regenerate the auto-stats block in the profile README from the GitHub API.

Stdlib only. Run by .github/workflows/update-stats.yml once a day.
Prints STATS_CHANGED (README rewritten) or STATS_UNCHANGED (no diff).
"""
import json
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone

USER = "rubichandrap"
README = "README.md"
START = '<span style="color:#6e7781"># ── auto-stats:start ──</span>'
END = '<span style="color:#6e7781"># ── auto-stats:end ──</span>'
BAR_W = 34  # chars per language bar


def api(path: str):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"User-Agent": "rubi-stats-bot", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


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
    stars = sum(r["stargazers_count"] for r in repos)

    langs = Counter(r["language"] for r in own if r.get("language"))
    lang_total = sum(langs.values())

    lines = [
        f'<span style="color:#b58900">repos</span>      : {len(repos)} ({len(own)} own)   '
        f'<span style="color:#b58900">stars</span>     : {stars:>5}',
        f'<span style="color:#b58900">followers</span>  : {user["followers"]:<2}            '
        f'<span style="color:#b58900">following</span> : {user["following"]:>3}',
        "",
        '<span style="color:#2f9e44">$</span> <span style="color:#1f6feb">./langs.sh</span>',
        '<span style="color:#6e7781"># primary language across my own repos</span>',
    ]
    ranked = langs.most_common(10)
    for lang, cnt in ranked:
        pct = round(cnt / lang_total * 100)
        fill = round(pct * BAR_W / 100)
        bar = "█" * fill + "░" * (BAR_W - fill)
        lines.append(f"{lang:<12}<span style=\"color:#6f42c1\">{bar}</span>  {pct:>3}%")
    rest = [l for l, _ in langs.most_common()[10:]]
    if rest:
        lines.append('<span style="color:#6e7781"># + ' + ", ".join(rest) + "</span>")
    lines.append(
        f'<span style="color:#6e7781"># synced {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC'
        " — .github/workflows/update-stats.yml</span>"
    )

    block = "\n".join(lines)
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
