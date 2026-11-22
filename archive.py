"""Look up and compare archived US consumer policy wording."""
import argparse
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit


def moment(value):
    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.utcoffset() is None:
        raise ValueError("Include a time and UTC offset, for example 2026-11-20T12:00:00-05:00.")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def add(db, key, at, url, body):
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("Provide an HTTP or HTTPS source URL.")
    body = body.strip()
    if not body:
        raise ValueError("The policy text is empty.")
    stamp = moment(at)
    with db:
        existing = db.execute(
            "SELECT url, body FROM captures WHERE policy = ? AND stamp = ?", (key, stamp)
        ).fetchone()
        if existing == (url, body):
            return
        db.execute("INSERT INTO captures VALUES (?, ?, ?, ?)", (key, stamp, url, body))


def observations(db, key, at):
    return db.execute(
        "SELECT stamp, url, body FROM captures WHERE policy = ? AND stamp <= ? "
        "ORDER BY stamp DESC LIMIT 2", (key, moment(at))
    ).fetchall()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="archive.sqlite")
    commands = parser.add_subparsers(dest="action", required=True)
    capture = commands.add_parser("capture", help="Save an observed copy of policy text.")
    capture.add_argument("policy")
    capture.add_argument("file", type=Path)
    capture.add_argument("--url", required=True)
    capture.add_argument("--at", help="Observation time with UTC offset. Defaults to now.")
    for name in ("lookup", "diff"):
        command = commands.add_parser(name)
        command.add_argument("policy")
        command.add_argument("--at", required=True)
    commands.add_parser("demo", help="Load fictional return and subscription examples.")
    args = parser.parse_args()
    db = sqlite3.connect(args.db)
    db.execute("CREATE TABLE IF NOT EXISTS captures (policy TEXT, stamp TEXT, url TEXT, "
               "body TEXT, PRIMARY KEY (policy, stamp))")
    try:
        if args.action == "demo":
            samples = {
                "demo-returns": (
                    "You can return an item within 30 days of delivery.",
                    "You can return an item within 14 days of delivery.",
                ),
                "demo-cancellation": (
                    "Cancel any time before your next billing date to avoid renewal.",
                    "Cancel at least 48 hours before your next billing date to avoid renewal.",
                ),
            }
            for policy, versions in samples.items():
                for day, wording in zip((2, 9), versions):
                    add(db, policy, f"2026-11-{day:02}T09:00:00-05:00",
                        f"https://example.org/{policy}", f"Fictional example. {wording}")
            print("Loaded fictional examples for demo-returns and demo-cancellation.")
        elif args.action == "capture":
            at = args.at or datetime.now(timezone.utc).isoformat()
            add(db, args.policy, at, args.url, args.file.read_text(encoding="utf-8"))
            print("Capture saved.")
        else:
            rows = observations(db, args.policy, args.at)
            if not rows:
                print("No capture on or before the requested time.")
                return 1
            stamp, url, body = rows[0]
            print(f"Last observed: {stamp}\nSource: {url}")
            if args.action == "lookup":
                print(body)
            elif len(rows) == 1:
                print("Only one capture is available by this time.")
            else:
                before, _, old = rows[1]
                diff = unified_diff(old.splitlines(), body.splitlines(), before, stamp, lineterm="")
                print("\n".join(diff) or "The text is identical in both captures.")
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.exit(2, f"Error: {exc}\n")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
