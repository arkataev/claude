---
description: Establish or refine the architectural shape of a system — layers, value objects, patterns, and decision records
user_invocable: true
argument: What you're designing — a new system, a redesign target, or "review" to assess current shape
---

# Design

You are establishing or refining the architectural shape of a system. The output is **structural decisions backed by rationale** — not implementation. Implementation comes later (often via `/tdd` or `/bdd`).

This skill owns the principle catalog. The `/refactoring` skill references it as the target shape.

## Process

### 1. Identify the shape question

Determine which mode applies:

- **Greenfield** — building something new. Start by stating the system's job in one sentence: who calls it, what input shapes, what output shapes.
- **Redesign** — reshaping existing code. Start by listing what's not working: where concerns cross, where one change touches many files, where new readers reliably get lost.
- **Review** — assessing the current shape against the principles below without proposing changes yet. Walk steps 2–6 against current code and report drift.

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

**Guardrail — when to ADR:**
For projects with few contributors (≤5) and short lifetime (<6 months), ADRs are often skipped — the team holds the context. Introduce ADRs when context is being lost: new contributors asking "why this shape?", reviewers re-litigating settled decisions. Below that threshold, a `# Why:` comment in code may suffice.

### 7. Verify the design

Before declaring the design done:

- **Trace one full operation end-to-end** through the proposed shape. Walk every layer. Note where data converts. Confirm each layer does only its layer's job.
- **Check invariants are enforced exactly once.** No invariant should appear in two layers. Pick the canonical site per the three-question rule.
- **Check there are no skip-layer calls.** Boundary doesn't call domain functions directly; domain doesn't see wire formats.
- **Check citations resolve.** Every cross-reference in the design doc (ADRs, layer table, module map, trace) points at a file or section the intended reader can open. For docs that ship beyond the immediate team, no citations to internal-only artifacts — those become dangling links downstream.
- **Cross-check against the principles in this skill.** Identify any drift between intent and proposed shape — call it out explicitly.

If any check fails, return to the relevant step.

## Output

Produce these artifacts:

1. **Layer responsibility table** (step 2).
2. **Module map** (step 2) — file-level index of which modules implement each layer. Skip for ≤3-module systems.
3. **Data model with invariants** (step 3).
4. **Validation placement decisions** (step 4) — per rule, which layer owns it and why.
5. **Patterns selected** (step 5) — with demand evidence for each.
6. **ADR drafts** (step 6) — one per non-obvious decision.
7. **End-to-end trace** (step 7) — narrative, ~10–15 sentences.

These collectively form the design document. Keep it ratio-heavy on rationale and decisions; defer implementation specifics to the code (which is the source of truth) and to runtime walkthroughs (which document call paths, not decisions).

## What this skill is NOT

- Not a code generator. It produces decisions, not files.
- Not a TDD/BDD replacement. Implementation work happens via `/tdd`; behavioral specification via `/bdd`.
- Not a forced ceremony. Every step has a guardrail for when it's over-engineering. Skip the steps whose guardrails fail.

## See also

- `/bdd` — start with feature spec before designing.
- `/tdd` — implement after design is approved.
- `/refactoring` — apply this skill's principles to existing code.
