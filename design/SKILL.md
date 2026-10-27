---
description: Establish or refine the architectural shape of a system — layers, value objects, patterns, and decision records
user_invocable: true
argument: The approved spec to plan (specs/<feature>/), or a redesign target
---

# Design

You are establishing or refining the architectural shape of a system. The output is **structural decisions backed by rationale** — not implementation. It starts from an approved spec (`/bdd`): the spec says what and how we know; the plan says how.

This skill owns the principle catalog. The `/refactoring` skill references it as the target shape, and audits current code against it.

## Process

### 1. Identify the shape question

Determine which mode applies:

- **Feature** — planning an approved spec. Read `specs/<feature>/spec.md` and its scenarios first; the plan answers its Acceptance and nothing more. State the job in one sentence: who calls it, what input shapes, what output shapes.
- **Redesign** — reshaping existing code. Start by listing what's not working: where concerns cross, where one change touches many files, where new readers reliably get lost. A redesign is a technical feature: it gets a spec with measurable acceptance first.

If the user's request is ambiguous, ask. Don't guess — the rest of the workflow branches on this.

### 2. Map concerns to layers

Survey what the system does and group operations by *concern*. Common concerns in typical layering order:

- **Boundary / I/O** — reading inputs, writing outputs, parsing wire formats.
- **Transformation / serialization** — converting between wire formats and domain shapes.
- **Orchestration / service** — coordinating operations, mapping exceptions to results.
- **Domain rules** — the actual logic the system embodies.
- **State / persistence** — storage (often deliberately omitted in stateless systems).

Define one layer per concern with one responsibility. Express as a table:

| Layer | File(s) | Responsibility |
|---|---|---|
| Boundary | … | one sentence |
| … | … | … |

**Rules:**
- No skipping layers in the call graph (boundary → service → domain, never boundary → domain directly).
- Convert raw inputs to typed values at the layer edge — no raw dicts/strings/JSON crossing inward.
- Each layer raises errors in its own vocabulary; the outer layer catches and translates (boundary I/O errors stay outside; domain exceptions stay inside until the service maps them to result types).
- **Design data access as if every call crossed a network, under concurrency, and could fail.** Never justify an access pattern by today's backend (an in-process SQLite, a local file, an in-memory fake, one user): the design must hold when the store is remote, shared by concurrent writers (threads, processes, tenants) and any statement can fail mid-way. Choose between approaches by how each behaves under a concurrent write and a failure, not by how it performs today. Concretely:
  - **No query per item in a loop.** Read a set in one query (`WHERE id IN (…)`, a join) and write a batch in one statement (`executemany`, a multi-row insert); the cost of an operation must not grow with the number of items it touches.
  - **One read per decision or view.** A decision reads every fact it needs together, into a value (`from_row`, § 3), and the rule is a method on that value in the domain: not a chain of yes/no repository predicates, and never the same fact read twice in one operation.
  - **Short transactions.** A transaction holds only the reads and writes it needs, never a loop of round trips or a call to a slow external service; facts read outside it are re-checked inside or read in the same query.
  - **Check-then-act is atomic.** A decision made on facts read and the write it leads to happen in one transaction that already holds the isolation it needs from its first read (a write lock taken up front, serializable isolation, `SELECT … FOR UPDATE`), or the write is itself conditional (`INSERT … ON CONFLICT`, `UPDATE … WHERE version = ?`, rows affected checked). Know the driver's transaction semantics: some begin a transaction only at the first write, leaving earlier reads outside it.
  - **The database enforces what must never be violated.** Uniqueness, references and required fields are constraints, not only application checks; a "find a free name, then insert it" loop is a race, an insert that relies on a unique constraint and resolves the conflict is not.
  - **Every unit of work survives failure.** A failure mid-way rolls back the whole unit (no partial writes); a unit is retryable (a bounded retry on busy / serialization errors) and has no side effects outside the database inside the retried block; a write that a caller may resend (a network retry, a redelivered message) is idempotent by a key.
  - **Derived state cannot go stale under a race.** A projection recomputed from a log is written in the transaction that appended to the log, or conditionally on the last event it saw, so a slower writer never overwrites a newer state.
  - **Tenancy is explicit.** Either a tenant is its own database (an ADR states it), or every table carries the tenant key and every query is scoped by it; never an implicit "there is only one".
  - **Guard it.** Each rule above that a test can decide is a test in the gate, so a regression cannot creep back silently:
    - **Statement budget:** a test counts the statements an operation runs (a driver trace hook) against a budget independent of the data size, so an N+1 fails it.
    - **External-call budget:** the same for the network. The fakes count model, HTTP and messaging calls per operation against a fixed budget, so a call per item, an extra retry or an edit loop that would break a rate limit fails.
    - **No leaked handles:** `ResourceWarning` (or the platform's equivalent) is an error in the test run, so an unclosed connection, file or socket fails the test that left it open.
    - **Fault injection:** a connection that fails at the k-th statement, for every k an operation sends. For each k: nothing is half-written, and a retry ends in the state a run without the failure gives.
    - **Idempotency:** every write entry point, listed automatically (not by hand), is called twice with the same input key; the second call writes nothing. A new write cannot skip the check.
  - **Know what each cost grows with.** Name the axes (items touched, catalog, history per entity, input length) and keep an operation's cost bounded in every axis but the one it must grow with. A state derived from a log is replayed from the last event that fixes it (or a checkpoint), not from the start, with an exhaustive test that the shortcut gives the same state. A lookup per row has an index, and a bound is the index range, not a filter after a walk (check `EXPLAIN`; a query-plan test pins the ones that matter). Measured with `/perf`.

**Guardrail — when to layer:**
Apply explicit layering when ≥2 distinct concerns currently cross each other. For single-concern scripts under ~200 LoC with one input source and one output sink, a flat module is more readable than ceremonial layering. Layering pays rent only when the concerns are real and growing.

**Module map — file-level companion to the layer table.**
Once layers are defined, produce a file-level index: which modules/files implement each layer, plus a one-line role per file. The map is the navigation backbone for every ADR cross-reference — readers shouldn't have to grep for a symbol after seeing "see ADR-N".

| Module | Layer | Role |
|---|---|---|
| `<path>` | boundary | one sentence |
| `<path>` | service | one sentence |
| … | … | … |

The module map and ADR citations move together: when a refactor reshapes the directory structure, stale citations land here first. Skip the map for systems with ≤3 modules — the layer table is enough.

### 3. Identify the data model and its invariants

List every distinct shape the system handles. For each, decide:

- **Value object** — identity by value, immutable, no lifecycle. Most domain shapes are this.
- **Entity** — identity beyond value (an ID), a lifecycle, mutable state. Rare in stateless systems.

For each value object, list its *invariants* — properties that must always hold:
- "Name is a non-empty string."
- "Conditions map has only non-null scalar values."
- "Sequence of steps is non-empty."

**Rules:**
- **Value objects own their invariants.** The constructor either yields a valid instance or raises. There is no "permissive constructor" path that skips checks.
- **Defensively copy mutable members.** Frozen records holding mutable containers (dicts, lists) must copy at construction, so caller mutation doesn't leak in. Frozen guards the binding, not the contents.
- **Build values whole; never patch them.** Construct a value once and complete, at the point where everything it needs is known: compute the parts first, then construct. Don't finish or correct an instance afterwards — no `dataclasses.replace`, `object.__setattr__` or attribute assignment to fix it up (a `__post_init__` normalizing its own fields is part of construction). A copy-and-patch hides which construction path is the real one and lets a half-built value travel. Deriving a genuinely new value is different: a state transition or a user's answer that changes a choice yields a new value, named for what happened, not a repair of the old one.
- **Construction belongs to the value.** Building a value from a wire shape or a storage row is a classmethod on the value (`Product.from_row(fields)`), taking plain types, so every construction path runs the same invariants. The adapter only reads the raw source (a DB row, JSON) into plain fields; it does not assemble domain objects in free helper functions.
- **Closed-set strings → enums.** Any field with a finite set of valid values (statuses, error codes, types) becomes a string-valued enum, not a raw string.

**Guardrail — when to formalize:**
Don't introduce typed value objects, enums, and invariants for systems with <3 distinct shapes or fully ephemeral data (one-shot transformation scripts). Plain dicts/tuples carry data fine when the system has nothing else to enforce. Formalize once you find the same invariant being checked in 2+ places.

### 4. Place validation by the three-question rule

When adding any validation rule, ask in order:

1. **Is the rule a property of the value itself?** (Invalid in any context, regardless of how constructed.)
   → **Model constructor** (e.g., `__post_init__`). The model owns its invariants.

2. **Is the rule a property of the wire format?** (Required keys, sub-shapes, named-reference resolution.)
   → **Boundary parser/serializer.** The parser is a thin adapter; it does not duplicate model invariants.

3. **Is the rule a property of the input source?** (File presence, JSON parse, top-level shape, command envelope.)
   → **Outermost boundary** (CLI / HTTP entrypoint / queue handler). Stays out of inner layers.

Rules with **both** an invariant and a wire-format aspect belong in the model — the parser inherits the check at construction time. Don't duplicate.

**Guardrail — when to tier:**
Single-layer validation is fine for short scripts with one entry path. Tier this when ≥2 entry paths reach the same model (e.g., CLI input + test fixture + future API), so the invariant is enforced regardless of construction site. Below that, parser-side checks alone are sufficient and lower-overhead.

### 5. Select patterns by demand, not prophylactically

For each candidate pattern, demand evidence before adopting:

- **Command pattern via classes** — when commands carry state, share an environment, and produce different result types.
  *Demand:* ≥2 command shapes, both needing the same context. Pure dispatch tables suffice for stateless dispatchers with two cases.

- **Context object** — when ≥2 callers need the same environment (e.g., configuration + acting user).
  *Demand:* literally two callers passing the same arguments to the same operations.

- **Registry-based parsing / two-pass build** — when the wire format is normalized (cross-references by name) and the domain is denormalized (tree of inlined value objects).
  *Demand:* the wire format actually has cross-references; otherwise a single-pass parser is shorter.

- **Dependency injection of I/O** — for code that does I/O, inject `reader`/`parser` callables. Tests use `Mock`, never monkeypatching of stdin/filesystem.
  *Demand:* none — baseline for any I/O code. Pure functions need no DI.

- **Thin subclass for ambient-state seams** — when a dependency you don't own reads ambient state (wall-clock, randomness, env, filesystem) internally and you need deterministic control of that state, subclass it and override the specific attribute or method that exposes the read. Prefer this over module-namespace patching of the dependency (`module.time = fake_clock` and similar).
  *Demand:* the dependency exposes a public settable seam (attribute or method) controlling the ambient read. Subclass is locally scoped, type-checker friendly, explicit at the call site, and survives upstream refactors that leave the public seam intact. If no seam exists, fall back to DI or to wrapping the dependency in a composition adapter.

- **Frozen value objects with constructor invariants** — for any domain shape.
  *Demand:* none — baseline once you have ≥3 typed shapes.

**Patterns explicitly NOT applied without strong evidence:**
- **Strategy / Visitor** — over-engineering for closed sets.
- **Repository** — only when persistence exists; omit when stateless.
- **Centralized validator class** — undermines model self-validation.
- **Observer / pub-sub** — only with ≥3 unrelated reactions to one event.
- **Premature abstractions for hypothetical extensibility** — wait for the second concrete need before generalizing.

**Guardrail — when to defer all patterns:**
For systems under ~300 LoC with one operation and one shape of input/output, no pattern is justified. A flat module of functions is more readable than any pattern from this list. Patterns earn their keep when the structure they impose matches structure that already exists in the problem.

### 6. Document non-obvious decisions as ADRs

Draft an ADR for any decision that meets ANY of these conditions:
- An alternative was seriously considered and rejected.
- The behavior would surprise a reader who hadn't seen this decision (e.g., "failed submissions roll back fully — submitted data is discarded").
- The decision constrains future change ("we don't have a repository layer").

**ADR template:**

```
### ADR-N: <Short Title>

**Status:** Accepted | Superseded | Proposed

**Context:** <one paragraph — what problem are we solving, what constraint applies>

**Decision:** <one paragraph — what we chose to do>

**Consequences:** <positive and negative consequences>

**Alternatives considered:** <one line per alternative — why rejected>
```

**Rules:**
- ADRs go in one place (`docs/design.md` § ADRs, or `docs/adrs/ADR-NNN-*.md` if you prefer one file each).
- Cross-link from code (docstrings, comments) to the relevant ADR by number.
- ADR **decision text is append-only** — supersede a decision via a new ADR, not by rewriting the original.
- ADR **citations are not** — file paths, symbol names, code snippets, and cross-references in an ADR must stay current with the code they describe. When a referenced symbol is renamed or moved, the ADR's citation updates in place; the decision text does not. The distinction: the decision is immutable, the description of *where the decision lives* tracks reality.
- **Citations must resolve in the doc's audience.** Every cross-reference (file path, symbol name, sibling document) should point at an artifact the intended reader can open. When a design doc is bound for external distribution, audit citations to internal-only notes, agent prompts, personal configs, or sibling files that aren't shipped — they become dangling links downstream.
- Don't ADR what the code already says clearly. ADRs document **why**, not what.
- In a plan, ADRs are drafts; the step that makes a decision true adds its ADR to the design doc.

### 7. Verify the design

Before declaring the design done:

- **Trace one full operation end-to-end** through the proposed shape. Walk every layer. Note where data converts. Confirm each layer does only its layer's job.
- **Check invariants are enforced exactly once.** No invariant should appear in two layers. Pick the canonical site per the three-question rule.
- **Check there are no skip-layer calls.** Boundary doesn't call domain functions directly; domain doesn't see wire formats.
- **Check citations resolve.** Every cross-reference in the design doc (ADRs, layer table, module map, trace) points at a file or section the intended reader can open. For docs that ship beyond the immediate team, no citations to internal-only artifacts — those become dangling links downstream.
- **Cross-check against the principles in this skill.** Identify any drift between intent and proposed shape — call it out explicitly.

If any check fails, return to the relevant step.

## Output: `specs/<feature>/plan.md`

```markdown
# <Feature> — plan

**Spec:** specs/<feature>/spec.md (Approved <date>)   **Status:** Draft | Approved

## Job                  one sentence (step 1)
## Decisions            the user's answers, each with the question it settled
## Layers               the layer table and the module map rows this adds or changes (step 2)
## Data model           new values and their invariants (step 3)
## Data access          what each operation reads and writes, in how many statements; the
                        axes its cost grows with; the guards it must satisfy (step 2)
## Validation placement per rule, its layer and why (step 4)
## Patterns             with demand evidence (step 5)
## ADR drafts           one per non-obvious decision (step 6)
## Trace                one operation end to end, ~10–15 sentences (step 7)
## Steps
| # | What | Layers | Scenarios | Hot path |
|---|------|--------|-----------|----------|
| 1 | …    | domain, store | names from the spec | yes: <benchmarks expected to move, prototype numbers> / no |
## Verification         what /validate checks beyond the gate: evals, renders, benchmarks
```

- Every scenario and every acceptance criterion of the spec lands in exactly one step.
- **Hot path** marks a step that adds a loop over stored data, a query, a match against a whole
  catalog, a replay or a model request that grows with the data; `/feature-workflow` runs
  `/validate step` on it. Its numbers come from a prototype (`/perf` § 3), not a guess.
- Keep the plan ratio-heavy on rationale and decisions; implementation specifics belong to the
  code and the briefs.

Show the plan, settle its decisions with the user, set **Status: Approved** when they approve,
and commit it on the feature branch.

## What this skill is NOT

- Not a code generator. It produces decisions, not code.
- Not a spec (`/bdd`) and not implementation (`/tdd`).
- Not a forced ceremony. Every step has a guardrail for when it's over-engineering. Skip the steps whose guardrails fail.
