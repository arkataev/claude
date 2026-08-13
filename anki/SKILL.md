---
description: Sync problem-library entries into Anki flashcards via AnkiConnect
user_invocable: true
argument: Optional path to a problem-library markdown file or grouped directory (default: the Claude Knowledge Drive folder's problem-library/)
---

# Anki Sync

Generate/update Anki cards from the problem library, one card per `##` entry, via AnkiConnect.
Run whenever a library file has new or changed entries — typically after `/problem-library`
adds one. Parsing and upload are handled by `anki_sync.py` (stdlib-only Python, see Process
below) — deterministic and cheaper than issuing one AnkiConnect call per card live.

The library itself is written by the companion skill `/problem-library`, which groups entries
into a small number of topic files instead of one growing one (see its `SKILL.md` for the
grouping/authoring process). This skill only reads and uploads.

## Prerequisites
- Anki desktop open and running (AnkiConnect is a local server, `http://localhost:8765` — it only exists while Anki is open)
- AnkiConnect add-on installed (Tools → Add-ons → Get Add-ons → code `2055492159`)
- Library present — defaults to `~/Google Drive/My Drive/Claude Knowledge/problem-library/` (every `*.md` file in it, one per topic group); pass a path argument to point at a single file or a different directory instead

## AnkiConnect Reference
All requests are `POST http://localhost:8765` with JSON body `{"action": ..., "version": 6, "params": {...}}`. Response is `{"result": ..., "error": ...}` — check `error` is `null` before trusting `result`.

**Ensure the deck exists:**
```json
{"action": "createDeck", "version": 6, "params": {"deck": "Problem Library"}}
```

**Add a card** (AnkiConnect handles dedup itself — see below):
```json
{
  "action": "addNote",
  "version": 6,
  "params": {
    "note": {
      "deckName": "Problem Library",
      "modelName": "Basic",
      "fields": {"Front": "<symptom text>", "Back": "<pointer + one-line insight>"},
      "options": {"allowDuplicate": false, "duplicateScope": "deck"},
      "tags": ["problem-library"]
    }
  }
}
```

**Dedup behavior:** with `allowDuplicate: false`, AnkiConnect rejects the add with an error mentioning "duplicate" if a note with an identical Front already exists in that deck. No separate lookup needed — just catch that specific error per card and count it as "already exists, skipped" rather than a failure. This means: if you reword an existing entry's Front line later, it will NOT match the old card and will create a new one instead of updating it — keep Front text stable once a card's been added, same rule as the CSV path.

## Parsing problem-library entries → Card Content
For each `## <title>` section, in any group file:
- **Front** = the text after `**Symptom:**` (trim, keep it as the trigger phrase — don't shorten it further, that's the whole point of the card)
- **Back** = `<title from "Reach for" link> — <the "One-line insight" text>`. Keep Back to the pointer + the one insight sentence — do NOT include the "Details worth keeping" bullets; those stay in the markdown file for when the card sends you back to look something up.

`anki_sync.py` implements exactly these two rules — this section and `/problem-library`'s
matching one are the source of truth if the two ever drift; a format change needs both updated.

## Process
1. Confirm Anki is open (if not, stop and tell the user to open it).
2. Optionally preview first: `python3 anki_sync.py --dry-run` — parses and prints every Front/Back across all group files without touching AnkiConnect, useful after `/problem-library` adds or edits an entry.
3. Run `python3 anki_sync.py [path]` (path optional, defaults to the Drive `problem-library/` folder — pass a single file or another directory to override). It creates the "Problem Library" deck if needed, then adds a card per entry across every `*.md` file found, treating AnkiConnect's duplicate error as "already exists" rather than a failure.
4. Relay the script's printed summary — `N added, N already present, N errors` (with any per-entry error or malformed-entry detail, tagged by source file) — plus its sync reminder.

## Output
Report: N added, N already present, N errors (with detail on errors), plus the sync reminder (desktop → AnkiWeb, then AnkiMobile → AnkiWeb — AnkiConnect only writes to the local collection).
