---
description: The solid flow's rule catalog — typed I/O, SOLID, DRY, KISS/YAGNI, the pure domain with adapters that own their model, tests by layer — each rule with the role that owns it and what holds it. Preloaded by solid-design's designer and by solid-critic, solid-writer and solid-reviewer
user_invocable: true
---

# Solid principles

One catalog of design rules for any Python project, grouped by principle. Each rule says who
decides it and what checks it. So each rule is checked once, at the cheapest stage: a tool,
then the critic (on a plan), then the reviewer (on a diff), then the designer.

The rules already in the global `CLAUDE.md` and in `/solid-design` are named here with a pointer
and are not restated. The tools that hold the code rules are in `baseline.toml`, next to this
file; a project copies it into its `pyproject.toml`.

## Precedence
This catalog and the `solid-` skills (`/solid-workflow`, `/solid-design`, `/solid-tdd`,
`/solid-review`) amend the global `CLAUDE.md` inside the solid flow. Where the two differ, the
solid rule wins, and a finding cites the solid rule:

| Global `CLAUDE.md` says | In the solid flow |
|---|---|
| A domain package holds "the interfaces of what it depends on (the ports it needs, which adapters implement)" | The domain package is pure and has no ports (D1). An adapter owns its interface and its model (D2). A service maps between them (D3). |
| An implementation "declares that it implements" its interface, and adapters implement the domain's ports | An adapter's implementation subclasses the adapter's own `Protocol` |
| Integration tests include "SQL against the engine" | An adapter has no tests of its own. It is tested at the composition layer, in-process (V1). |

Everything else in the global `CLAUDE.md` holds as written. That includes "depend on
interfaces", "only the composition root names an implementation" and the package layout.

## Ownership

Each rule has a tag:
- **Shape**: owners, interfaces, where knowledge lives. The designer decides it with the user, in
  the plan. The critic checks the plan. The brief fixes the shape, and the reviewer checks only
  that the diff keeps it.
- **Code**: how a function or class is written. The writer applies it. The gate checks it, or the
  reviewer when no tool can.

| Role | Does | Checks |
|---|---|---|
| Designer | Decides the Shape rules with the user; names in each brief the rule IDs the step touches | Triages findings; a finding a tool could catch becomes a candidate guard for the user |
| Critic | — | Every Shape rule on the plan; T2 on every interface the plan adds or changes |
| Writer | Applies the Code rules; runs the gate | Before the report, the rules no tool holds |
| Reviewer | — | The Code rules no tool holds; that the diff keeps the brief's shape |
| User | Owns the rule set: limits, exemptions, guard files | — |

- **The writer never changes a shape.** When a Code rule can only be met by a change of shape
  (a split class, a new interface, a helper moved to another package), the writer leaves the
  check failing and lists it under open items with the rule ID. The designer takes it to the user.
- **Every finding cites a rule ID** (`T1`, `D2`…) or `global: <rule name>`.
- **A finding a tool could catch** is marked `candidate guard: <tool and rule>`. Only the user adds
  a guard or changes a limit.

Each rule has four parts: the rule, **why**, **too much** (when it is over-engineering), and
**held by**. The global guardrail applies to every rule: a script under ~200 lines with one
I/O path is exempt.

## Typed input and output (T)

Global: typed values at the layer edge, enums over strings, self-validating values, values
built whole, construction on the value (`CLAUDE.md` Architecture Principles; `/solid-design` § 3).

**T1 · Code · A function returns a named type.** A return annotation names only primitives,
enums, classes the project defines (or a dependency's class that it wraps), and `list`,
`Sequence` or `Iterator` of those. It never names `dict`, `tuple`, `set`, `frozenset` or `Mapping`.
A wire shape is a `TypedDict`.
- Why: the caller of a `dict` or a `tuple` must know what each key or position means. A named type
  carries that meaning, and the type checker proves it.
- Too much: `__init__` and `__post_init__`.
- Held by: Ruff `ANN` (every signature is annotated); a guard test that scans the return
  annotations in the AST (`ast` names, not substrings).

**T2 · Code · Public interface parameters follow T1.** A method on a public `Protocol` takes the
same kinds of types it may return. Private functions are free.
- Why: the interface is the contract that callers and mocks read. A private helper's parameters
  change with its one caller.
- Too much: private functions, and the constructors of values (`from_row`), which are not
  interfaces.
- Held by: the T1 guard, extended to the parameters of methods on `Protocol` classes in public
  modules. The critic checks every signature the plan lists.

**T3 · Code · No `Any` and no `cast` in source.** (Tests: global TDD rule.)
- Why: each one is a hole in what the type checker proves. A `cast` claims what a check should
  prove.
- Too much: untyped data at the boundary (`json.loads`) is read as `object` and narrowed with
  `isinstance`, or parsed into a `TypedDict`; a dependency's `Any` stops at the adapter.
- Held by: mypy `disallow_any_explicit`; Ruff `ANN401`; Ruff `TID251` bans `typing.cast`.

**T4 · Code · A `match` over a closed set handles every case.** A `match` over an enum or a union
lists each member, with no `case _:` fallback.
- Why: a new member then fails the type check at every `match` that must handle it, instead of
  falling silently into a default.
- Too much: an open set (any `str`, any `int`) needs a default.
- Held by: mypy `exhaustive-match`. The reviewer catches a `case _:` over a closed set.

## Single responsibility (S)

Global: one layer per concern, one package per owner (`CLAUDE.md`; `/solid-design` §§ 2, 5).

**S1 · Shape · An owner knows only its own models.** No word in its interface names a caller or
a flow (a chat, a receipt, a language model, a question). It returns facts, and the caller
decides what they mean. This holds for an adapter too: its interface and its model name storage
facts, never a domain decision (D2).
- Why: an interface shaped for one caller changes when that caller changes, and the next caller
  inherits words that do not fit it.
- Too much: a boundary is named for its protocol (a CLI handler names its commands). A package
  named for the product (`desk/` in a "baggage desk") names its owner, not a caller.
- Held by: the critic, on every interface the plan adds or changes.

**S2 · Code · Many collaborators or many public methods is a split signal.** More than 5
constructor arguments, or more than 20 public methods (the tools' defaults).
- Why: each collaborator is one more reason for the class to change.
- Too much: a value (a frozen dataclass) with many fields is one fact; a field is not a
  collaborator.
- Held by: Ruff `PLR0913` for arguments; the reviewer for methods (candidate guard: Ruff
  `PLR0904`, preview only). A split is a shape change: the writer raises it.

## Open/closed (O)

Global: patterns by demand, no abstraction before the second real need (`/solid-design` § 5).

**O1 · Shape · O and YAGNI agree.** A closed set of variants is an enum with a full `match` (T4).
A behavior that varies gets a `Protocol` only at its second real implementation.
- Why: a `Protocol` with one implementation guesses where change will come from. A `match` over an
  enum is closed on purpose, and the checker finds every place to extend.
- Too much: the interface every class others call has (global, "depend on interfaces") is not a
  variation point; O1 is about abstractions beyond it.
- Held by: the critic.

## Liskov substitution (L)

Global: signatures conform (the implementation subclasses its `Protocol`; mocks use autospec).

**L1 · Shape · Behavior conforms too.** When a `Protocol` has two implementations or more
(fakes included), one contract suite runs on each: the same tests, parametrized over them.
- Why: a fake that behaves differently from the real implementation lets unit tests pass in a
  world that does not exist.
- Too much: one implementation and no fake (its own tests are the contract).
- Held by: the critic (the plan names the contract suite of each such `Protocol`); the reviewer
  (a new implementation or fake runs in the suite).

**L2 · Code · No inheritance between implementations.** A class subclasses its `Protocol` and
standard bases (`Exception`, `Enum`, `TypedDict`) only. Shared behavior is composed.
- Why: a subclass inherits behavior it can break, and ties two owners' changes together.
- Too much: a project's error hierarchy; the thin subclass of a dependency you do not own, at an
  ambient-state seam (`/solid-design` § 5).
- Held by: the reviewer (candidate guard: an AST scan of class bases).

## Interface segregation (I)

Global: a client depends on the interface of what it calls (`/solid-design` § 5).

**I1 · Shape · The first interface is the smallest core.** A component starts with only its own
behavior and assumes no other component exists. A method that implies an integration waits on
the roadmap, with what was settled.
- Why: an interface drafted for flows that do not exist turns guesses into a contract, and a
  contract changes only when the user says so.
- Too much: —
- Held by: the critic.

**I2 · Shape · A client that uses part of an interface gets a role `Protocol`.** The consumer
declares a narrow `Protocol` with only the methods it calls. The implementation meets it
structurally.
- Why: the client's tests mock only what it uses, and a change to a method it does not use does
  not touch it.
- Too much: a client that uses nearly the whole interface takes the interface itself.
- Held by: the critic.

## Dependency inversion (D)

Global: depend on interfaces, and only the composition root names an implementation
(`CLAUDE.md`; `/solid-design` § 5). Imports at module scope only: Ruff `PLC0415`, and `TID251`
bans `typing.TYPE_CHECKING`. In this flow, an adapter owns its abstraction. The domain owns
none: it depends on nothing.

```
boundary ──▶ service ──▶ domain        (values, rules, refusals: imports nothing of the app)
                 └─────▶ adapter       (its own interface and model: imports nothing of the app)
composition root ──▶ boundary, service, adapter   (the only module naming implementations)
```

**D1 · Shape · The domain is pure.** A domain package holds values, the rules on them and its
refusals. It has no ports, no I/O, no transaction and no storage type, and it imports nothing of
the app. A rule takes the facts it decides on as values and returns a value or raises a refusal.
- Why: a domain that declares what storage must do is shaped by the storage it expects. Its
  rules then need mocks to test, and a storage change reaches them.
- Too much: an ambient value the rule needs (the time now) is passed in as a value by the
  service, not read through a port.
- Held by: the critic (the plan's module map and imports); a guard test on the import graph
  (the domain package imports only the standard library and its own modules).

**D2 · Shape · An adapter owns its interface and its model.** An adapter package (a store, a
client) declares its own `Protocol`, its own values (`StoredBag`, its own enums), its own errors
(`StoreUnavailable`) and, for a store, its unit of work. It imports nothing of the app and does
only its infrastructure: it builds no domain value and decides no domain outcome. A database
constraint guards against corruption. A refusal is never decided there, and the constraint's
values come from the adapter's own enums.
- Why: an adapter that implements a domain-owned port and builds domain entities has two
  concerns, its infrastructure and the domain's model, and changes with both.
- Too much: a storage form that restates a domain enum is not a copy (R1). It is a different
  owner's vocabulary on purpose.
- Held by: the critic; a guard test on the import graph (the adapter package imports no app
  package).

**D3 · Shape · A service maps between the domain and the adapters.** The application service
is the only layer that imports both. In one unit of work it reads through the adapter's
interface, maps the stored values to domain values, asks the domain to decide, maps the result
back and writes it. It turns the adapter's errors into the domain's refusals or the app's
errors. The mapping lives in the service's private mapping module: an exhaustive `match` per
enum (T4), so a member added on either side fails the type check. Construction goes through
each value's own classmethod.
- Why: with the mapping in one place, neither model knows the other, and the one place that
  knows both is small and type-checked.
- Too much: a script under the global guardrail keeps one module.
- Held by: the critic (the plan's trace names the mapping); the reviewer (a domain value built
  in an adapter, or a stored value in the domain).

## Don't repeat yourself (R)

Global: every value has one owner, an invariant lives in one place, validation is not repeated
(`CLAUDE.md`; `/solid-design` §§ 3–5).

**R1 · Shape · One source per piece of knowledge.** A rule, a limit, a mapping or a wording is
defined in one place, and everything else derives from it. A copy kept across owners on
purpose has an ADR and a guard that the copies agree.
- Why: two sources drift, and the bug is in whichever one was not updated.
- Too much: a test states its expected value itself. A test that derives it from the code proves
  nothing. An adapter's storage vocabulary is not a copy of the domain's (D2): the mapper (D3)
  is the guard that the two agree.
- Held by: the critic (the plan says where each new rule lives); the reviewer (the diff adds no
  second source). On demand, an audit for exact copies:
  `uv run --with pylint pylint <src> --disable=all --enable=duplicate-code`.

**R2 · Code · A literal that carries a rule is a named constant.** A threshold, a limit, or a
string compared against.
- Why: the name says what the number means, and a change happens in one place.
- Too much: `0`, `1`, `""` and the like; literals in tests.
- Held by: Ruff `PLR2004` (numbers compared); the reviewer for strings and for other literals.

**R3 · Code · Look-alike code that changes for different reasons stays apart.** Merge code only
when it holds the same knowledge (R1). When you are not sure, wait: the third copy decides.
- Why: merged look-alikes tie two owners together, and the next change to one grows a flag
  (K2) or breaks the other.
- Too much: —
- Held by: the reviewer. A merge across packages is a shape change: the writer raises it.

## Keep it simple; you aren't gonna need it (K)

Global: each `/solid-design` step has a guardrail, patterns by demand, every line a test can see
(`/mutants`), no compatibility hacks (`CLAUDE.md` Refactoring).

**K1 · Code · Size limits are split signals.** In source (tests are exempt): at most 5
arguments, 6 returns, 12 branches, 50 statements, and complexity 10.
- Why: past these sizes a function holds more than one idea, and its tests multiply.
- Too much: the limits are signals, not targets; a breach that a private helper in the same
  module fixes, the writer fixes. A breach that needs a new shape is left failing and raised.
  The user lists existing breaches per file when a project adopts the baseline.
- Held by: Ruff `PLR0913`, `PLR0911`, `PLR0912`, `PLR0915`, `C901`.

**K2 · Code · No flag arguments.** A `bool` parameter that picks a behavior becomes two functions,
or an enum when the choice is data.
- Why: a flag hides two functions behind one name, and every caller must know what `True` means.
- Too much: a `bool` that is a fact passed through (a value's field), not a choice of path; a
  keyword a framework passes to a subclass it builds (argparse's `color=`).
- Held by: Ruff `FBT001`, `FBT002` (positional flags); the reviewer for keyword-only flags.

**K3 · Shape · No parameter, setting or hook with one value in use.** A knob waits for its second
real value.
- Why: each knob is a branch to test and to understand; a knob with one value is a guess.
- Too much: an injected dependency (a clock, a reader) is not a knob, it is a seam for tests.
- Held by: the critic (the plan's settings and signatures); the reviewer (a parameter that the
  diff adds and that every caller passes with the same value).

**K4 · Shape · A value holds only the states the spec allows.** A case the spec leaves out of
scope cannot be represented: one field, not a collection; a required field, not an optional one.
It is not handled by code that no scenario reaches.
- Why: each extra state needs a branch, the branch has no scenario, so no test sees it, and the
  state spreads into the adapters and the callers that must build or read it.
- Too much: a wire shape that must accept more than the domain allows; its parser refuses the
  rest at the edge.
- Held by: the critic (each value's fields against the spec's scope and its "Out of scope"); the
  reviewer (a branch for a state no scenario makes).

## Tests by layer (V)

Global: unit and integration tests are two kinds, kept apart; most tests are unit tests
(`CLAUDE.md` TDD; `/solid-tdd` "Unit or integration").

**V1 · Shape · Each layer is tested where its behavior is.**

| Layer | Tests |
|---|---|
| Domain | Pure unit tests, no mocks: values in, a value or a refusal out |
| Service | Unit tests, each adapter's `Protocol` mocked by autospec: the mapping, the unit of work, the error mapping |
| Boundary | Unit tests, the service's `Protocol` mocked: parsing, wording, exit codes |
| Adapter | None of its own. A unit test of it tests the engine. |
| Composition | Integration tests of the wired program against its real dependencies (a real records file), run in-process (`main(argv)`), never in a subprocess |

The composition tests hold everything the adapter does beyond the engine. They hold the
deterministic guards of `/solid-design` § 2: races between two writers, a refused or failed
command writes nothing, the statement budget (a tracing connection passed in at the wiring),
fault injection, idempotency and the unavailable store. They also hold one end-to-end path per
use case.
- Why: an adapter with no rules has nothing a unit test can decide, and a test of it alone
  proves the engine works. A subprocess hides the code from coverage and from a mutation sweep,
  and here these tests are the adapter's only coverage.
- Too much: a parser or a client with real logic of its own (a wire format with cross-references)
  is a boundary, not a pure adapter. Its parsing rules get unit tests.
- Held by: the critic (the plan's steps put each test at its layer); the reviewer (an adapter
  test, a unit test that opens a file or a database, a composition test that starts a
  subprocess).
