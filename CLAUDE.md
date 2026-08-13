# Global Development Conventions
## Workflow & Skills
Typical pipeline:
**Behavior** (`/bdd`) → **Design** (`/design`) → **Test → Implement** (`/tdd`) → **Refactor** (`/refactoring`) → **Coverage** (`/review`)

### Pipeline & quality passes
| Skill | When to invoke |
|---|---|
| `/bdd` | New features — define behavior in Gherkin, then derive tests. |
| `/design` | Non-trivial shape decisions — layers, value objects, validation placement, ADRs. |
| `/tdd` | Implementation — strict red → green → refactor → lint cycle, one behavior at a time. |
| `/refactoring` | Existing code — audit + targeted fix. Standalone or after `/tdd` reveals drift. References `/design` for target shape. |
| `/review` | Coverage gap audit between scenarios and tests. |
| `/doc-pass` | Documentation pass — three parallel subagents (DRAFTER + STYLE_COP + VERIFIER) converge on a reviewable diff in one or two rounds. |

### Behavior modes
| Skill | When to invoke |
|---|---|
| `/coach` | Guidance-only mode for design coaching, interview prep, and learning. No file edits; user drives implementation. |
| `/short` | Terse, code-first answers to "how do I X in Y" questions. For live-coding and quick reference. Complements `/coach`. |

### Tooling
| Skill | When to invoke |
|---|---|
| `/dockerize` | Scaffold Docker setup — Dockerfile, docker-compose, env vars, Makefile targets. |
| `/problem-library` | Capture or update an entry in the grouped problem-library Drive folder. |
| `/anki` | Sync problem-library entries into Anki flashcards via AnkiConnect. |

Feature files are human-readable specifications — NOT wired to test runners (no pytest-bdd, no behave). They guide test writing.

**Coach vs builder default.** Read context cues. If the user is asking design questions ("should I...?", "what are the trade-offs?", "what's wrong with this approach?"), doing interview prep, or learning a new topic, default to **guidance** — short snippets inline, push back with questions, let them drive implementation. Don't reach for Write/Edit unless they explicitly ask. For sustained coaching sessions, `/coach` makes this mode explicit.
## Code Style
Priorities (in order):
1. Self-explanatory code over comments.
2. Domain language in names.
3. Consistent abstraction levels within methods.
4. Extract code paragraphs into well-named methods.
5. Remove noise: dead code, unused imports, commented-out code.
**Comments and docstrings:**
- Only **WHY** comments — never WHAT comments.
- Public functions, classes, and methods get a terse docstring; privates get docstrings only when WHY isn't obvious.
- Don't narrate the current task or callers in code — that belongs in PR descriptions and rots fast.
## Architecture Principles
Always-apply baseline. Decision rules and guardrails live in `/design`.
- **Layer separation** — boundary → service → domain (+ repository when persistent). No skipping layers in the call graph.
- **DTO boundaries** — convert raw types (dicts, JSON, ORM rows, wire formats) to typed values at the layer edge. No raw types cross inward.
- **Domain exceptions** — domain raises domain exceptions; outer layer maps them to protocol-specific responses (HTTP status, exit codes, JSON envelopes).
- **Enums over strings** — `str` enums for any field with a finite set of values. Never bare strings.
- **Self-validating value objects** — constructor yields a valid instance or raises. Defensively copy mutable members on otherwise-immutable records.
- **Validation placement (three-question rule)** — value invariant → model constructor; wire format → boundary parser; input source → outermost layer. See `/design` § 4 for guardrails.
**When these are over-engineering:** for single-concern scripts under ~200 LoC with one I/O path, ceremonial layering and typed value objects can be skipped. Apply once concerns cross or invariants need enforcing in 2+ places.
## BDD Feature Conventions
```gherkin
Feature: Short Name
  As a <role>
  I want to <capability>
  So that <business value>
  Scenario: Descriptive name of one behavior
    Given <precondition>
    When <action>
    Then <observable outcome>
```
Rules:
- One feature file per domain concept (not per endpoint or class).
- Scenarios describe **behavior**, not implementation — no code, no class names, no internal details.
- Tags for test categories: `@sequence-mock`, `@integration`, `@documented-only`.
- `@documented-only` for scenarios that can't be automated yet — include a comment explaining why.
- `Background` for shared preconditions.
- Comments for domain rules and edge case explanations.
## TDD Conventions
**Process:**
1. One failing test at a time — simplest first.
2. Minimum code to pass. No untested code.
3. Refactor only when green. One change at a time. Don't change test assertions.
4. Run the full suite after every change — or the fastest reliable subset locally + full suite at commit boundary.
**Test quality:**
- Test behavior, not implementation — assert on responses and state, not method calls.
- **Test only public interfaces.** Privates are implementation details; tests against them break for the wrong reasons.
- Given-when-then structure with blank lines separating sections.
- If a test passes without implementing the expected behavior, the test is too weak — tighten assertions.
- **Inject I/O via callables** (reader, parser, etc.); tests use `Mock`. Never `monkeypatch` stdin/files.
- **Use real objects with `Mock` / `patch.object`** for objects whose interface might drift, not handcrafted stubs.
**ZOMBIES** for test discovery: Zero, One, Many, Boundaries, Interfaces, Exceptions, Simple.
## Refactoring
Full workflow lives in `/refactoring`. Contract that always holds:
- **Tests pass before and after** every change.
- **Report the actual pass count after a refactor**, not just "tests pass". A drift from N → N-1 with a fresh skip somewhere is the kind of silent regression a number catches and a vibe doesn't.
- **One logical refactoring at a time.** Verify each before the next.
- **Don't add behavior** — switch to `/tdd` for new behavior.
- **Don't change test assertions.** Renames and import updates are fine.
- **No backwards-compatibility hacks** — delete unused code completely.
- **No safety net, no refactor.** Without a full test suite or acceptance gate, restrict to the safest tactics (renames within one file, comments, docs).
- **Verify generated artifacts.** If the refactor touches code that produces non-test outputs (plots, snapshots, generated docs, fixture files, golden files), verify those artifacts are byte-identical to the pre-refactor version or explicitly document the difference. The test suite alone doesn't catch this.
- **Don't hide architectural problems with adjacent patches.** If a refactor would introduce a circular import, the fix is restructuring the layering — not moving the function to an inappropriate module to break the cycle. Surface the architectural issue and propose the structural fix; prefer the cleanest fix at the root cause over the smallest patch at the symptom.
## Documentation
| Doc | Owns |
|---|---|
| `README.md` | What the project is, how to run it, key examples, top-level diagram |
| Project `CLAUDE.md` | Project-specific commands, layer adaptation, conventions, testing patterns |
| `docs/design.md` | Architectural decisions, ADRs, pattern selection, technology choices |
| `docs/runtime-walkthrough.md` (or similar) | End-to-end trace — only when multi-layer flow is worth tracing |
| `features/*.feature` | Behavioral specifications in Gherkin |
| Inline docstrings | Public contracts; code-specific limitations (`Limitation:`) |
**Doc style:**
- **WHY over WHAT** — same rule as comments. Docs explain motivation, constraints, and non-obvious context; WHAT belongs in the code's identifiers.
- **Don't restructure well-written existing docs without an explicit request.** Add and refine sections; rewrite the structure only when asked. Wholesale rewrites of already-good prose are a source of regression and tone drift.
- **Consistent domain terminology.** Use the terms the project's CLAUDE.md or design doc establishes — don't introduce synonyms when an existing project-defined term covers the meaning.
- **No filler words.** Drop "simply", "just", "basically", "in order to", "it is important to note that". Lead with the substantive point.
- **Prefer multiple focused docs over one bloated one.** A long README is harder to maintain than a few focused docs that link to each other.

**Placement rule:** decision *rationale* → design doc / ADR. Code-specific *behavior* and limitations → docstrings or inline comments. Implementation specifics drift; rationale doesn't.
**ADRs** — record any decision that (a) had a serious alternative rejected, (b) would surprise a reader unfamiliar with the context, or (c) constrains future change. Template in `/design` § 6.
**Doc/code alignment:** no stale docs. If code changed, docs are updated in the same logical change (typically the same PR; ideally the same commit). Mermaid diagrams for data models and key flows.
## Operational Rules
**Commits:**
- Only commit when the user explicitly asks.
- Subject: present-tense imperative under 72 chars ("Push validation onto domain models").
- Body: **why** and what changed per file/concern; cross-reference issues/PRs.
- Never commit secrets, build artifacts (`.pyc`, `dist/`, `node_modules/`), or large binaries.
**Dependencies:**
- Any new runtime dependency requires documented justification. Prefer stdlib.
- Test/lint deps: same standard, lower bar; avoid duplicates (one test framework, one linter).
**Where things go:**
| Type | Location |
|---|---|
| Ambient conventions (apply across projects) | This file |
| Project-specific commands, structure, decisions | Project `CLAUDE.md` and `docs/` |
| Invocable workflows | Skills (`~/.claude/skills/<name>/SKILL.md`) |
| Project-local context that shouldn't generalize | Memory (`~/.claude/projects/<path>/memory/`) |
| Architectural decisions | `docs/design.md` § ADRs |
| Behavior specifications | `features/*.feature` |
