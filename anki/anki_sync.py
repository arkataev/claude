#!/usr/bin/env python3
"""Sync problem-library.md entries into Anki flashcards via AnkiConnect.

Deterministic counterpart to the /anki skill's manual process: parses every
`## <title>` entry once and uploads it in a single pass, instead of Claude
issuing one curl call per card per run.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_URL = "http://localhost:8765"
DEFAULT_DECK = "Problem Library"

SYMPTOM_RE = re.compile(r"\*\*Symptom:\*\*\s*(.+)")
REACH_FOR_RE = re.compile(r"\*\*Reach for:\*\*\s*\[([^\]]+)\]")
INSIGHT_RE = re.compile(r"\*\*One-line insight:\*\*\s*(.+)")


def parse_entries(text):
    """Split problem-library.md into (front, back, title) card tuples.

    Blocks missing Symptom, Reach-for, or One-line-insight are skipped and
    reported separately — malformed data shouldn't abort the whole run.
    """
    blocks = re.split(r"(?m)^## ", text)[1:]
    entries = []
    malformed = []
    for block in blocks:
        title = block.splitlines()[0].strip()
        symptom = SYMPTOM_RE.search(block)
        reach_for = REACH_FOR_RE.search(block)
        insight = INSIGHT_RE.search(block)
        if not (symptom and reach_for and insight):
            malformed.append(title)
            continue
        front = symptom.group(1).strip()
        back = f"{reach_for.group(1).strip()} — {insight.group(1).strip()}"
        entries.append((front, back, title))
    return entries, malformed


def call_ankiconnect(url, action, params):
    body = json.dumps({"action": action, "version": 6, "params": params}).encode()
    request = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(request, timeout=10) as response:
        payload = json.loads(response.read())
    if payload.get("error") is not None:
        raise RuntimeError(payload["error"])
    return payload["result"]


def add_note(url, deck, front, back):
    """Upload one card; returns "added" or "duplicate", raises on other errors."""
    try:
        call_ankiconnect(
            url,
            "addNote",
            {
                "note": {
                    "deckName": deck,
                    "modelName": "Basic",
                    "fields": {"Front": front, "Back": back},
                    "options": {"allowDuplicate": False, "duplicateScope": "deck"},
                    "tags": ["problem-library"],
                }
            },
        )
        return "added"
    except RuntimeError as exc:
        if "duplicate" in str(exc).lower():
            return "duplicate"
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "library_path",
        nargs="?",
        default=str(Path(__file__).parent / "problem-library.md"),
        help="Path to problem-library.md (default: sibling file next to this script)",
    )
    parser.add_argument("--deck", default=DEFAULT_DECK)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and print Front/Back for every entry without calling AnkiConnect",
    )
    args = parser.parse_args()

    library_path = Path(args.library_path)
    if not library_path.exists():
        print(f"error: {library_path} not found", file=sys.stderr)
        sys.exit(1)

    entries, malformed = parse_entries(library_path.read_text())

    if args.dry_run:
        for front, back, title in entries:
            print(f"[{title}]\n  Front: {front}\n  Back:  {back}\n")
        print(f"{len(entries)} entries parsed, {len(malformed)} malformed")
        for title in malformed:
            print(f"  malformed, skipped: {title}")
        return

    try:
        call_ankiconnect(args.url, "createDeck", {"deck": args.deck})
    except (urllib.error.URLError, ConnectionError) as exc:
        print(
            f"error: can't reach AnkiConnect at {args.url} — is Anki desktop open? ({exc})",
            file=sys.stderr,
        )
        sys.exit(1)

    added = duplicate = 0
    errors = []
    for front, back, title in entries:
        try:
            result = add_note(args.url, args.deck, front, back)
            if result == "added":
                added += 1
            else:
                duplicate += 1
        except Exception as exc:
            errors.append((title, str(exc)))

    print(f"{added} added, {duplicate} already present, {len(errors)} errors")
    for title, message in errors:
        print(f"  error [{title}]: {message}")
    for title in malformed:
        print(f"  malformed, skipped: {title}")
    print(
        "\nRemember to sync: Anki desktop → AnkiWeb, then AnkiMobile → AnkiWeb "
        "(AnkiConnect only writes to the local collection)."
    )


if __name__ == "__main__":
    main()
