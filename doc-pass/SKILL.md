---
description: Improve documentation on a target (file, module, package) via three parallel subagents — DRAFTER, STYLE_COP, VERIFIER — converging on a single reviewable diff in one or two rounds.
user_invocable: true
argument: Target to document — file path, module name, or package directory (e.g., `path/to/module.py` or `path/to/package/`)
---

# Doc Pass

Improve docstrings, comments, and inline documentation on a target by running three parallel subagents that critique a single shared input, then reconciling their findings into one diff. Designed to converge in one or two rounds instead of multi-iteration rewording cycles.

## When to use

- A module or package needs docstrings added or refined.
- Existing docs have drifted from the code (terminology shift, stale example, buried WHY).
- You want filler/jargon and code-example correctness caught in the same pass.

Don't use for: new feature scoping (use `/bdd` or `/design`), code-level review (use `/code-review` or `/review`), or terse single-snippet answers (use `/short`).

## Process

### 1. Scope the target

Read the target — keep it tight (one file, one module, or a small package). Identify:

- Public symbols (functions, classes, methods) — which already have docs, which don't.
- Existing docstrings — note which are already good (will not be touched per the global "no unprompted restructuring" rule).
- Project-defined terminology — pull from the project's `CLAUDE.md` and any `docs/design.md` so subagents don't drift into synonyms.

If scope is ambiguous (file vs. package, all symbols vs. only public), ask once before launching subagents.

### 2. Launch three subagents in parallel

Single message, three `Agent` tool calls. Each subagent gets the same target slice but a different lens. They run concurrently.

**DRAFTER** — `general-purpose` agent
- Input: the target code in full + the project's domain vocabulary.
- Output: a list of `{symbol, current_doc, proposed_doc, why}`. Proposes docstrings/comments where missing, refines where the WHY is buried. Does NOT touch docs that are already good.
- Rule: WHY over WHAT. No multi-paragraph essays. One-line or short-paragraph rationale per symbol.

**STYLE_COP** — `Explore` agent (read-only)
- Input: the target code's existing docs + the global Documentation style rules (`~/.claude/CLAUDE.md` § Documentation) + the project's `CLAUDE.md` if present.
- Output: a list of `{location, verdict (flag/accept), reason}`. Flags filler words, jargon when a plain term exists, inconsistent terminology, WHAT comments that should be WHY, oversized prose blocks.
- Does NOT propose replacements — it only flags. DRAFTER (or step 3) decides what to do.

**VERIFIER** — `general-purpose` agent (can run Bash)
- Input: every code example embedded in the target's existing docs (docstring examples, inline `>>>` blocks, fenced code in markdown docstrings).
- Output: a list of `{example_location, runs_clean, observed_output, notes}`. Runs each example in isolation (or against the project's test environment) and reports.
- Does NOT propose fixes — only flags broken examples.

### 3. Reconcile into a unified diff

Take the three reports and produce one diff:

- **Where DRAFTER added a new docstring** and STYLE_COP doesn't flag it → include.
- **Where STYLE_COP flagged existing prose** that DRAFTER didn't already address → either refine in-place (if the fix is mechanical: drop filler, swap jargon) or surface as a question if the fix needs judgment.
- **Where VERIFIER flagged a broken example** → fix the example, remove it, or drop the surrounding claim — never leave a broken `>>>` in committed docs.
- **Where DRAFTER proposed a change but STYLE_COP rejected** → keep the original, document why the proposed change was rejected.

The diff is hunk-level, file-by-file. Don't bundle unrelated changes.

### 4. (Optional) second round on residual issues

If the reconciled diff introduces *new* prose (DRAFTER's additions) or fixes that STYLE_COP/VERIFIER haven't yet seen, run a single second round of STYLE_COP and VERIFIER on the *delta* only (not the whole file). Cap at one additional round — if issues remain after round 2, surface them as open questions, don't keep iterating.

### 5. Present the diff for approval

Show the user:

- The proposed diff (file-by-file, hunk-by-hunk).
- Per-hunk: one sentence on what WHY it documents and which subagent triggered the change.
- Any STYLE_COP rejections that need user judgment.
- Any VERIFIER findings that required dropping or rewriting an example.

**Do NOT apply changes yet.** Wait for user approval, then apply.

## Rules

- **Three subagents, max two rounds.** Don't add a fourth agent or a third round — the cycle is designed to converge.
- **Don't restructure well-written existing docs without explicit request.** DRAFTER must flag prose it wants to change and only proceed if the WHY is genuinely buried; STYLE_COP doesn't trigger DRAFTER edits on its own.
- **No applying changes without user approval.** This skill produces a diff for review, not an edit.
- **Cap each subagent's context.** Pass each one only the slice it needs: DRAFTER gets the target + vocabulary, STYLE_COP gets style rules + target docs, VERIFIER gets only the extracted examples.
- **Use the project's terminology.** If the project says "X", subagents do not drift to "Y" in proposed docs. STYLE_COP is the enforcement layer for this.
- **Empty diff is a valid result.** If all three subagents return "no findings", report that and exit — don't manufacture changes to justify the run.

## Output

A unified diff with per-hunk annotations:

```
=== <file>:<line range> ===
WHY: <one sentence — what this hunk documents or fixes>
Triggered by: DRAFTER | STYLE_COP | VERIFIER (or combination)
Notes: <STYLE_COP rejection rationale or VERIFIER finding, if relevant>

<diff hunk>
```

Followed by:
- Open questions (if any) — STYLE_COP rejections requiring user judgment, VERIFIER findings that can't be auto-fixed.
- Final summary: N hunks accepted, M open questions, K subagent rounds run.

## What this skill is NOT for

- Writing READMEs or full guides from scratch — use `/design`'s module map as the spine and this skill for refinement once the structure exists.
- Code-level correctness review — use `/code-review` or `/review`.
- Architectural decisions and ADRs — use `/design`.
- One-off "improve this paragraph" requests — heavyweight for a single hunk; just edit directly.
