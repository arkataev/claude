# Global Development Conventions
## Workflow & Skills
Spec-driven. Every change starts from a spec; the roadmap says what comes next, the changelog what is done:
**Roadmap** (`/roadmap`) → branch `feature/<name>` → **Spec** (`/bdd`) → **Plan** (`/design`) → per step: **Test → Implement** (`/tdd`) → **Review** (`/review`) → **Validate** (`/validate`) → **Changelog** (`/changelog`) → merge `--no-ff`

### Pipeline & quality passes
| Skill | When to invoke |
|---|---|
| `/roadmap` | `ROADMAP.md`: the current scope (Now / Next / Later / To confirm); start a feature from it. |
| `/bdd` | Every change, first — write or update `specs/<feature>/spec.md` and its Gherkin scenarios; the user approves it. |
| `/design` | The approved spec → `specs/<feature>/plan.md`: layers, value objects, validation placement, ADRs, steps (hot paths flagged). |
| `/tdd` | Implementation — red → green → refactor, one scenario at a time, gate at the end. |
| `/review` | The light check of any change (each step, or ad hoc): scenarios against tests, correctness against the rules. No timings. |
| `/validate` | Once per feature before merge (and `step` mode on a hot-path step): gate, spec acceptance, evals, benchmarks, profile, render. |
| `/changelog` | Close a feature: its `CHANGELOG.md` entry and the roadmap updated. |
| `/refactoring` | Existing code — audit + targeted fix. Standalone or after `/tdd` reveals drift. References `/design` for target shape. |
| `/perf` | The measuring method: prototype a fix before planning it, a performance audit, or a "slow after a while" symptom. |
| `/doc-pass` | Documentation pass — three parallel subagents (DRAFTER + STYLE_COP + VERIFIER) converge on a reviewable diff in one or two rounds. |
| `/feature-workflow` | Runs the loop for a roadmap feature — the main session specs, plans, briefs and triages; the global `writer` (Sonnet) and `reviewer` (Opus, read-only) agents implement and review. Project settings go in the project CLAUDE.md "Workflow" section. |

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
- **Build values whole; never patch them** — construct a value once, complete, where it is made; no `replace`/`__setattr__` afterwards to fix it up (a new value for a real state change is fine). Construction from rows or wire shapes is a classmethod on the value, not a free helper. See `/design` § 3.
- **Data access as if remote, concurrent and failing** — never rely on the backend being local, fast or single-user: no query per item in a loop, one read per decision with the rule in the domain, short atomic check-then-act transactions, constraints in the database, retryable idempotent units, explicit tenancy, a statement-count guard. Pick approaches by their failure and concurrency behavior. See `/design` § 2.
- **Validation placement (three-question rule)** — value invariant → model constructor; wire format → boundary parser; input source → outermost layer. See `/design` § 4 for guardrails.
**When these are over-engineering:** for single-concern scripts under ~200 LoC with one I/O path, ceremonial layering and typed value objects can be skipped. Apply once concerns cross or invariants need enforcing in 2+ places.
## Spec Conventions
Full format lives in `/bdd`. Contract that always holds:
- **Specs first.** No behavior is built, and no technical change is planned, without an approved spec: `specs/<feature>/spec.md`, plus `<feature>.feature` when the feature has behavior.
- **One folder per feature** (a roadmap item), holding its spec, scenarios, plan, briefs and validation report. A change to existing behavior edits the scenario in its own folder and lists it under "Affected specs".
- Scenarios describe **behavior**, not implementation — no code, no class names, no internal details; scenario names are unique, since tests cite them.
- Only one tag: `@documented-only`, with a comment saying why. A test's kind is its path.
## TDD Conventions
**Process:**
1. One failing test at a time — simplest first.
2. Minimum code to pass. No untested code.
3. Refactor only when green. One change at a time. Don't change test assertions.
4. The affected tests each cycle, the full suite after each section, the gate at the end. A test that passes at once is checked by breaking the code.
**Test quality:**
- Test behavior, not implementation — assert on responses and state, not method calls.
- **Test only public interfaces.** Privates are implementation details; tests against them break for the wrong reasons.
- Given-when-then structure with blank lines separating sections.
- If a test passes without implementing the expected behavior, the test is too weak — tighten assertions.
- **Inject I/O via callables** (reader, parser, etc.); tests use `Mock`. Never `monkeypatch` stdin/files.
- **Use real objects with `Mock` / `patch.object`** for objects whose interface might drift, not handcrafted stubs.
- **Unit and integration tests are two kinds, kept apart.** A *unit* test is pure: no database (not even in-memory), file, network, subprocess, real clock or environment; it runs with no infrastructure and replaces the repositories, ports and application API it calls with autospec mocks, so it tests business logic only. An *integration* test exercises a real adapter against its real dependency (SQL against the engine, a parser against real files, the wiring end to end). Each test is one kind, visible from its path (`tests/unit/`, `tests/integration/`), and the unit suite runs alone. Most tests are unit tests. See `/tdd` "Unit or integration".
**ZOMBIES** for test discovery: Zero, One, Many, Boundaries, Interfaces, Exceptions, Simple.
## Performance Conventions
Full method lives in `/perf`. Contract that always holds:
- **Measure, don't guess.** A change on a hot path (a loop over stored data, a new query, matching against a whole catalog, a replay of a log) is compared with a benchmark run saved before it; the commit message gives every change over 10%.
- **Guards every step, timings per feature.** The deterministic guards run in the gate at every step; benchmarks run in `/validate` once per feature against the baseline saved at the branch point, and at a step only when the plan marks it hot path.
- **Benchmarks outside the gate, guards inside.** Timings are noisy and one machine's, so they never fail the test command. What is deterministic is a test: the statement and external-call budgets per operation, query-plan tests for lookups that must seek, `ResourceWarning` as an error, fault injection and idempotency for every write (`/design` § 2 "Guard it").
- **Each benchmark size grows one axis** (catalog, history per entity, input length), besides the sizes that grow everything; a cost linear in one axis hides behind sizes that grow them together.
- **Prototype a fix and measure it before planning it**; the expected gain is a hypothesis.
- **A fast path proves it gives the same results** as the slow one (an exhaustive or brute-force check, or both forms compared on varied data), and a mutation of it fails a test.
- **Generated, seeded data only** for benchmarks and profiles; never real user data.
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
| `specs/<feature>/` | The feature's spec (`spec.md`), its Gherkin scenarios, plan, briefs and validation report |
| `ROADMAP.md` | What will be done: Now (work in progress, where a session resumes), Next, Later, To confirm |
| `CHANGELOG.md` | What has been done: one entry per merged feature, with its numbers |
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
| Agents a workflow spawns | `~/.claude/agents/<name>.md` (generic; project specifics in the project CLAUDE.md) |
| Project-local context that shouldn't generalize | Memory (`~/.claude/projects/<path>/memory/`) |
| Architectural decisions | `docs/design.md` § ADRs |
| Behavior specifications, plans, briefs | `specs/<feature>/` |
| What's next / what's done | `ROADMAP.md` / `CHANGELOG.md` (no handover notes) |

**Git:** one branch per feature, `feature/<name>`, from `main`; merged with `--no-ff` after the user has tried it, then deleted.
