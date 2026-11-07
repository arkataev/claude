---
description: The solid flow's TDD — red, green, refactor, one scenario at a time, gate at the end; tests by layer, with adapters tested only at the composition layer, in-process. Preloaded by solid-writer
user_invocable: true
argument: The scenarios or behavior to implement (a spec folder, a brief, or a description)
---

# Solid TDD

You are building behavior test-first. Follow these rules exactly.

This is `/tdd` for the solid flow (`/solid-workflow`), with the catalog `solid-principles`.
Where this skill differs from the global TDD conventions, it wins in the solid flow ("Unit or
integration" below; `solid-principles` V1).

## Input

The scenarios come from the feature's spec (`specs/<feature>/*.feature`, and the "Affected specs"
its `spec.md` lists) or a brief that names them. With no spec, ask whether one should be written
first (`/bdd`); a one-off fix may go without.

## The cycle (per behavior)

### 1. Red
- Write the simplest test that captures the next piece of behavior (ZOMBIES below).
- Test at the level the scenario describes: a screen, bot or API scenario gets a gateway test,
  not only a service test.
- Decide unit or integration first (below), and put it in that tree.
- Follow the project's test conventions (naming, citing the scenario, fixtures) and
  given-when-then with blank lines between the sections.
- **Ambient state** (clock, randomness, env, filesystem): a thin subclass over the public seam,
  never module-namespace patching (`/solid-design` § 5).
- Run that test alone and see it **fail for the right reason**.

### 2. Green
- The **minimum code** that passes it. No untested code, and no line a test can't see
  (`/mutants`).
- Re-run the affected test files.

### 3. Refactor (only when green)
- Duplicate code, unclear names, mixed abstraction levels, dead code; one change at a time.
- Never change a test's assertions, never add behavior (back to Red for that).

### A test that passes at once
It proves nothing until it fails. Break the code on purpose, see the test fail, restore it. In
Python run these checks with `PYTHONDONTWRITEBYTECODE=1`: a restored file of the same size within
the same second can keep the mutant's stale `.pyc`. Count these tests in the report.

### Cadence
- Each cycle: the new test, then the affected files.
- After each section of the work (a brief's numbered change, a group of scenarios): the full
  test suite.
- At the end: the project's gate (lint, types, tests). Fix what it finds before reporting.

## Unit or integration

Two kinds of test, kept in two trees (`tests/unit/`, `tests/integration/`, each mirroring the source tree) so the kind shows in the path and the unit suite runs alone, fast, with no infrastructure.

**Unit test** — business logic, nothing else.
- Opens no database (an in-memory one is still a database), file, socket, subprocess or real model; reads no real clock or environment. The unit tree's conftest makes those fail, so a slip is caught, not trusted.
- What the code under test calls across a boundary is an autospec mock of its interface: an adapter's own `Protocol`, the service's `Protocol`, I/O callables (`create_autospec(StoreProtocol, instance=True)`, the `Protocol`, never the implementation). It is never a hand-written fake of the adapter: a fake re-implements the adapter's behavior and drifts from it. A unit of work's mock hands over a mock of the unit's `Protocol`.
- Arrange a service's mocks to return the adapter's stored values, the way the adapter would. Assert on what comes back and on the **writes** handed to the mocks: a write is the code's output, a stored value the service mapped from the domain's decision. Never assert on which reads happened or in what order. A test that has to script many reads is pointing at logic that belongs in a domain value: move the rule there and test it directly.
- Layers (`solid-principles` V1):
  - **Domain:** rules on values, no mocks at all; the domain calls nothing.
  - **Service:** adapters mocked; the mapping, the unit of work, the error mapping.
  - **Boundary:** the service mocked; assert on what is rendered or sent and on the exit code.

**Integration test** — the composition layer: the wired program against its real dependencies.
- **An adapter has no tests of its own.** With no rules in it, a test of it alone tests the engine.
- **The composition tests drive the program in-process:** `main(argv)`, or the composition root's entry function, against a real records file in `tmp_path`. A subprocess hides the code from coverage and from a mutation sweep, and these tests are the adapter's only coverage. A test that must start a process (a real second process for a race) is the one exception, and the mutation setting lists it.
- **They hold what the adapter does beyond the engine:** the deterministic guards of `/solid-design` § 2 "Guard it", and one end-to-end path per use case.
  - races between two writers;
  - a refused or failed command writes nothing;
  - the statement budget, through a tracing connection passed in at the wiring;
  - fault injection;
  - idempotency;
  - the unavailable store.
- **A parser or client with real logic of its own** (a wire format with cross-references) is a boundary, and its rules get unit tests. Its run against real files is a composition test.
- **Guards that read the source tree** (static checks, the import graph) live here too.

**Choosing.** A rule is tested at unit level: on the domain value, or on the service with the adapter mocked. What carries it (the SQL, the serialization, the wiring) is tested at the composition level. Never test a business rule only through the database. Most tests are unit tests: if the integration tree outgrows the unit tree, rules are being tested in the wrong place.

## Fixtures and types

Tests are type-checked with the source's rules, so a test cannot build a value the code never
receives.

**A fixture is a value.** It returns one object of a real class, or a fake typed by the
`Protocol` it implements. It never returns a function, and its body defines no function or
lambda. The one exception is a lambda handed to a class of the code as that class's own seam,
such as `Household(db, clock, lambda: model, lang)`.
- **What varies is a fixture too.** Make it a "knob" fixture (`model`, `lang`, `db`) that the
  value fixture takes. One test turns a knob with `@pytest.mark.parametrize("model", [...])`.
  pytest applies the value even when the test takes only the fixture built on the knob. A group
  of tests turns a knob by overriding the knob fixture in its class.
- **An action is a plain function**, not a fixture. Examples are `press(bot, button)` and
  `send(bot, text)`, with typed parameters.
- **A recorder is a small class.** A fixture that collects what happened returns an object
  with typed methods, not a closure.
- **A double's behavior lives in a fake class, a recorder class or a module-level function.**
  It is not a `side_effect = lambda ...` or an inner function written in the fixture.
- **No `None` stands in for a collaborator.** Use a fake that fails the test and names the
  call. No fixture has a parameter that no test passes.
- **A test body defines no class and no function.** A fake, a recorder or a subclass a test
  needs (a connection that records what it opened, a model that fails) is a module-level class,
  and a helper is a module-level function. The test may build an instance of it like any value
  (`FakeInterpreter(...)`); a fixture hands it over when it needs other fixtures to be set up or
  a teardown. A lambda in a test body is fine (`lambda: model` as a seam, a one-line
  `side_effect`).
- **A double reaches the code through a seam, never by overriding a builtin.** A `list` subclass
  whose `__getitem__` runs something when the code slices it depends on how the code reads a
  value it is given, and breaks for the wrong reasons. Reach the moment through a parameter of the
  code or a hook the driver offers (a connection's trace callback runs as each statement starts).
  Nothing in a test is `@overload`ed: a helper with two signatures is two helpers.
- **A fake that records calls is never shared between tests.** A `parametrize` value is built
  once, at collection. So never set a recording fake in a class-level `parametrize`, and never
  use one module-level fake in two decorators. A class-level override of the knob builds one
  fake per test.

**A `# type: ignore` only for a value that is invalid on purpose.** This is the line that
passes a wrong type to see the code refuse it. It names exactly one error code and says what the
test checks: `# type: ignore[arg-type]  # refused: <what the code refuses>`. Every other type
error is fixed, never ignored. Tests use no `cast` (narrow with `isinstance` and `assert`), no
`@no_type_check` and no inline `# mypy:` comment. Nor do they use another way to turn a value
into `Any` and hand it to a typed name, such as `operator.methodcaller`, `attrgetter` or
`getattr` with a constant. A fake that has to stand in for several ports takes one part per
port, each typed by its `Protocol`.

## Test discovery (ZOMBIES)
**Z**ero, **O**ne, **M**any, **B**oundaries, **I**nterface, **E**xceptions (happy paths first),
**S**imple scenarios first.

## Report (once, at the end)
- Tests added, by scenario; the test count before and after.
- Tests that passed at once and were checked by breaking the code.
- The gate result.
- **Design touchpoints** (surface, don't act): new modules (the module map, `/solid-design` § 2);
  non-obvious choices that may need an ADR (`/solid-design` § 6); a scenario that turned out wrong or
  missing (back to the spec, `/bdd`).
