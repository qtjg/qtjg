#!/usr/bin/env python3
# ⬡ repo-pulse — zero-dependency git activity pulse for any repo
# made by Mayank Bhaskar · https://github.com/qtjg
# usage: python3 tools/repo_pulse.py
import argparse
import collections
import datetime
import json
import subprocess
import sys


def git(*args):
    return subprocess.run(("git",) + args, capture_output=True, text=True)


def collect_pulse() -> dict:
    """Collect the repo pulse as a structured dict.

    Returns None if not inside a git repository.
    """
    if git("rev-parse", "--git-dir").returncode != 0:
        return None
    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    head = git("rev-parse", "--short", "HEAD").stdout.strip()
    dirty = bool(git("status", "--porcelain").stdout.strip())
    today = datetime.date.today()
    since = (today - datetime.timedelta(days=27)).isoformat()

    days = collections.Counter(
        git("log", f"--since={since}", "--pretty=format:%ad", "--date=short").stdout.split())
    files = collections.Counter(
        ln.strip() for ln in git("log", f"--since={since}", "--name-only",
                                 "--pretty=format:").stdout.splitlines() if ln.strip())
    authors = collections.Counter(
        git("log", f"--since={since}", "--pretty=format:%an").stdout.splitlines())

    return {
        "branch": branch,
        "head": head,
        "dirty": dirty,
        "since": since,
        "total_commits": sum(days.values()),
        "days": dict(days),
        "hot_files": files.most_common(5),
        "authors": authors.most_common(3),
        "author_count": len(authors),
    }


def render_human(pulse: dict) -> str:
    """Render a pulse dict as the human-readable report."""
    today = datetime.date.today()
    days = collections.Counter(pulse["days"])
    bar = "".join(
        "█" if days.get((today - datetime.timedelta(days=i)).isoformat()) else "·"
        for i in range(27, -1, -1))
    lines = [
        f"⬡ repo-pulse · branch {pulse['branch']} @ {pulse['head']}"
        + (" · dirty tree" if pulse["dirty"] else " · clean"),
        f"  {pulse['total_commits']:>4} commits / 28d   {bar}",
    ]
    if days:
        peak, n = max(days.items(), key=lambda kv: kv[1])
        lines.append(f"  peak day: {peak} ({n} commits)")
    if pulse["hot_files"]:
        lines.append("  hot files:")
        for f, n in pulse["hot_files"]:
            lines.append(f"    {n:>3}x  {f[:72]}")
    if pulse["authors"]:
        top = ", ".join(f"{a} ({n})" for a, n in pulse["authors"])
        lines.append(f"  contributors: {pulse['author_count']} — {top}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Zero-dependency git activity pulse.")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of human-readable text")
    args = parser.parse_args(argv)
    pulse = collect_pulse()
    if pulse is None:
        print("repo-pulse: not inside a git repository")
        return 1
    if args.json:
        print(json.dumps(pulse, indent=2))
    else:
        print(render_human(pulse))
    return 0


if __name__ == "__main__":
    sys.exit(main())
