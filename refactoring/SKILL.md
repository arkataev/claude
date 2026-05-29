---
description: Improve the shape of existing code — audit smells, prioritize fixes, apply tactics one at a time without changing behavior
user_invocable: true
argument: Target file/area, specific smell description, or empty for "review my recent changes"
---

# Refactoring

You are improving the shape of existing code **without changing its behavior**. The target shape is defined by the principles in `/design`. Your job is to identify the gap between current code and that shape, then close it incrementally.

## Process

### 1. Detect mode from argument

- **Specific smell named** ("function X mixes parsing and validation") → **Targeted mode**. Skip to step 4.
- **Area or vague** ("review parse_*", "clean up cli.py") → **Audit mode**. Continue to step 2.
- **Empty argument** → ask the user: which area to audit, or which specific smell to fix? Default to audit if they're unsure.

### 2. Audit mode: critical review

Read the target area in full. List smells by severity, distinguishing:

- **Real flaws** — affect correctness, testability, or the layer/invariant rules from `/design`.
- **Smells** — readability, naming, navigation friction, mild duplication.
- **Not-actually-smells** — patterns that look suspicious but are intentional. Defer-list them with a one-line reason so the user can confirm.

Present as a table:

| # | Smell | Severity | Tactic (see § 4) |
|---|---|---|---|
| 1 | … | flaw | … |
| 2 | … | smell | … |

**Then prioritize:**
- Structural fixes before cosmetic ones.
- Independent fixes before bundled ones.
- High-confidence fixes (clear smell + clear tactic) before judgment calls.

Present the prioritized list to the user and **ask which to act on**. Do not apply fixes the user hasn't approved.

**Guardrail:** Don't bundle unrelated fixes into one pass. Each fix should stand alone with its own verification.

### 3. (User selects which smells to fix; the rest are deferred or recorded as follow-ups.)

### 4. Look up the tactic from the smell catalog

| Smell | Tactic | Design reference |
|---|---|---|
| Mixed concerns in one function | Split by concern — each new function's name says what it does | `/design` § 2 (layers) |
| Validation duplicated parser + caller | Push to model constructor; parser becomes thin adapter | `/design` § 4 (three-question rule) |
| Two functions, identical inner loop | Extract helper — only when name + signature fit both, no awkward parameters | `/design` § 5 (patterns by demand) |
| Mutable member on frozen value object | Defensively copy in constructor | `/design` § 3 (invariants) |
| Sub-package with <3 small files (~30 LoC each) | Flatten into the parent | `/design` § 2 (layers) |
| Naming collision (one type doesn't fit a shared prefix) | Rename the outlier so the prefix means one thing | — |
| Test uses handcrafted stub for object under test | Replace with real object + `Mock` / `patch.object` | `/design` § 5 (DI) |
| I/O coupled via globals (stdin, file paths) | Inject reader/parser callables; tests use `Mock` | `/design` § 5 (DI) |
| Test patches a dependency's module namespace to inject ambient state (clock, randomness, env, filesystem) | Replace with a thin subclass that overrides the public seam; use the subclass at the call site | `/design` § 5 (thin subclass for ambient-state seams) |
| ADR / design doc / module map cites a symbol this refactor renames, moves, or removes | Update the citation in place during the same pass — it's part of the change, not a follow-up | `/design` § 6 (ADR citation hygiene) |
| Stale documentation contradicts code | Align or remove — never both leave-and-correct | — |
| Test asserts on private function/method | Move test to nearest public caller | — |
| Function signature has `\| None` parameter that's never None | Tighten the type; remove the None-handling | — |
| TODO / "fix later" comment older than the current change | Either fix now, or convert to an ADR / issue with a date | `/design` § 6 (ADRs) |
| Skip-layer call (boundary calls domain directly) | Route via the missing intermediate layer | `/design` § 2 (layers) |

For smells not in the catalog: derive the tactic by asking which `/design` principle is being violated. The fix is whatever brings the code into compliance with that principle.

### 5. Apply, one change at a time

For each chosen smell:

1. **Verify before** — run tests + acceptance gate (e.g., reference contract, end-to-end check). Confirm green baseline.
2. **Make the change.** Single conceptual change. No bundling. (Renames touching many files are still one conceptual change.)
3. **Verify after** — same tests + gate. Confirm green.
4. If red: identify the cause. Either revert or fix forward in the same conceptual change. Never leave a half-applied refactor.
5. Repeat for the next smell.

**Rules:**
- Don't change test assertions during refactoring (renames and import updates are fine).
- Don't add new behavior. If a refactor reveals a missing behavior, note it and run `/tdd` separately.
- Each pass should be small enough to revert cleanly.

**Guardrail — no safety net, no refactor:**
If verification has no acceptance gate (no full test suite, no reference output to diff against), pause and ask the user to add one before refactoring further. Refactoring without a safety net is risky regardless of intent. If the user can't add one (e.g., unfamiliar codebase, no time), stick to the safest tactics only: renames within one file, comment additions, doc updates.

### 6. Cross-check the result against `/design` principles

After all chosen smells are addressed:

- Layer responsibilities still clean? (No skip-layer calls, no concerns crossed.)
- Invariants enforced exactly once?
- Patterns still earning their keep, or did the refactor leave any orphan abstractions?
- Validation placement still matches the three-question rule?
- **Design-doc citations still resolve?** Module map entries, ADR cross-references, and design-doc symbol mentions should still point at the post-refactor reality. A structural refactor (rename, move, signature change) shifts code under fixed doc text; fix any drift now, in the same pass.

Note any drift between current state and target shape. Either fix in the same pass (if cheap and isolated) or record as a follow-up.

### 7. Report

Output:

- **Audit summary** (if audit mode) — smells found, severity breakdown.
- **Fixes applied** — one line per smell with the tactic used.
- **Doc updates** — citations / module map entries / design-doc cross-references updated to track the code change. Empty if the refactor touched no symbols referenced by docs.
- **Deferred** — smells the user chose not to act on (with reason).
- **Follow-ups** — drift noted in step 6, not addressed in this pass.
- **Verification status** — tests passing, acceptance gate holding.
- **Files touched** — with diff scope.

## What this skill is NOT

- Not a behavior-change tool. New functionality goes through `/tdd`, not here.
- Not a one-pass cleanup. Each refactor is independent and verifiable. Multi-issue cleanups are multiple passes.
- Not a substitute for tests. If you don't have a safety net, the skill's guardrail in step 5 will pause you.

## See also

- `/design` — the target shape principles and decision rules. Every tactic in this skill maps to one or more design principles.
- `/tdd` — when a refactor reveals missing behavior, switch to TDD instead.
- `/review` — coverage gaps between feature scenarios and tests (orthogonal to refactoring; useful before/after).
