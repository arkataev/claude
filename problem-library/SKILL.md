---
description: Capture or update an entry in the grouped problem-library Drive folder
user_invocable: true
argument: The problem to add or update — symptom, the resource/insight you want tied to it, and any extra context
---

# Problem Library

Turns a problem you elaborate in conversation into an entry in the problem library — a
quick-reference index of symptoms that should make you reach for a specific post/article,
organized by *symptom*, not topic. Companion skill `/anki` reads this library and uploads it
to Anki; this skill only writes it.

## Storage
`~/Google Drive/My Drive/Claude Knowledge/problem-library/<group-slug>.md` — a small number of
medium-sized files grouped by topic (e.g. `concurrency-and-coordination.md`), not one growing
file. No separate index file — group filenames are self-descriptive; list the directory
directly when deciding where an entry belongs.

Each group file:
```
# <Group Title>

<optional one-line description of what belongs in this group>

---

## <entry title>

**Symptom:** <text>

**Reach for:** [<link text>](<url>)

**One-line insight:** <text>

**Details worth keeping:**
- <bullet>

**When this should fire in your head:** <text>

---
```

## Card-content contract (must match `/anki`'s parser)
`anki_sync.py` (in the `/anki` skill) extracts exactly two things from each entry via regex:
- **Front** = the `**Symptom:**` text
- **Back** = `<Reach-for link text> — <One-line insight text>`

Every field written here must stay on its own single-line paragraph (blank line before/after)
— the parser doesn't handle multi-line field values. If this format ever needs to change,
update it here AND in `anki/SKILL.md`'s "Parsing problem-library entries → Card Content"
section together; they're one contract split across two files.

## Process
1. **Gather fields** from the user's argument or the current conversation: Symptom, Reach-for
   (a resource + its link), One-line insight. `Details worth keeping` and `When this should
   fire in your head` are optional. If Symptom, Reach-for, or One-line-insight is missing, ask
   — don't fabricate content for a personal knowledge base.
2. **List existing group files** in the Drive `problem-library/` folder.
3. **Update-vs-new check**: read through existing entries for the same underlying problem
   (same root cause/failure mode, even if worded differently). If found, revise that entry's
   fields in place rather than adding a near-duplicate — keep its title stable unless the user
   asks to rename it (a title change doesn't affect `/anki` uploads, only Front/Back do, but
   keep entries recognizable).
4. **Group selection** (new entries only): match the problem's domain against existing group
   filenames; append to the best fit. Only create a new group file when none genuinely fit —
   the goal is a handful of medium files, not one group per entry. New group files get a short
   H1 + one-line description header (see Storage above).
5. **Write** the entry in the exact field format above.
6. **Report back**: which file was written, whether it was a new group, a new entry, or an
   update to an existing one, and the entry text.

## Output
State the target file, new-group/new-entry/updated-entry, and the written entry. Remind the
user that `/anki` needs a run to push this into their Anki deck — this skill doesn't touch
AnkiConnect.
