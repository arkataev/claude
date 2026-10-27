---
description: Measure performance — save a baseline, audit for N+1, scans, hot code, leaked memory and handles, prompt size, lock time and contention, tail and cold latency, write cost, and costs that grow with one axis; prototype a fix, prove equal results, compare against the baseline
user_invocable: true
argument: "audit", a change to check, or a path that feels slow
---

# Performance: measure, don't guess

This is the method. When it runs inside a feature is `/validate`'s: a full comparison before the
merge, and a quick one on each step the plan marks hot path. Use this skill directly for:
- **Planning a hot path:** a loop over stored data, a new query, matching against a whole catalog, a replay of a log. Prototype the fix and measure it (§ 3) before the plan rests on it.
- **An audit:** "where does it struggle", after a large feature, or now and then. Findings become roadmap items, each with its prototype number.
- **A symptom:** "slow after months of use", "the bot lags on big receipts".

## Ground rules
- **Before and after, on one machine, against a saved run.** A number without a baseline is an
  anecdote. Never delete a saved run a comparison depends on.
- **Benchmarks stay outside the gate.** Timings are noisy and belong to one machine. The gate keeps the
  deterministic guards: a statement budget and an external-call budget per operation, query-plan
  tests for the lookups that must seek, and `ResourceWarning` raised as an error. Those guards,
  and the correctness ones (fault injection, idempotency), are in `/design` § 2 "Guard it". This
  skill measures cost.
- **Generated data only.** Seed it and write it through the app's own writes (no SQL fixtures that
  bypass the rules), never with real user data. Make it deterministic: same seed, same database.
- **Each size grows one axis.** Name the axes an operation's cost can grow with:
  - items it touches;
  - catalog size;
  - history per entity;
  - input length;
  - concurrent writers.

  Give each axis a size of its own, besides the sizes that grow everything. A cost that is
  linear in history hides behind sizes that grow the catalog and the history together.
- **Give the worlds the states that bound a read**, not only sizes: a reset, a clear or a merge
  near the end of the log. A read bounded by "since the last reset" can be fast on a log that
  never resets and walk the whole history just after one; only a world with that state shows it.
- **Local is not remote.** A variant that waits a fixed time before each statement (1 ms) turns
  round trips into time, with no network.
- **A finding needs a measurement.** A profile beats intuition, and a prototype beats a profile.

## 1. Baseline
Save a run on the commit before the change (`pytest --benchmark-autosave`, or the project's
`make bench`). Write down the commit it belongs to; for a feature, that is the branch point,
and the roadmap's "Now" names the run.

## 2. Audit: ten sweeps, one defect class each

| Sweep | Finds | How |
|---|---|---|
| Statement count at two sizes | N+1 | Count each operation's statements with a connection subclass or a trace hook. A count that grows with the size is a query per item. |
| External calls at two sizes | N+1 over the network: too many requests | Count the model, HTTP and messaging calls per operation with the fakes. A count that grows with the input breaks a rate limit (a chat API's messages per second, a model's requests per minute). |
| `EXPLAIN` of every statement shape | Scans that should be seeks | Collect each distinct SQL statement seen during the count sweep. Explain it on the larger database (details below). |
| Profile | Hot code | cProfile per benchmark, by cumulative time. Run the per-statement timing report as a separate pass: instrumenting every fetched row inflates the profile (3× seen). |
| Long run | Leaked memory and handles, and growth over time | Drive the real entry point (bot, API, CLI loop) for hundreds of rounds in one process (details below). |
| Request size at two sizes | Cost and latency that grow with the data | Measure the tokens (or bytes) of each model or API request the app builds. A prompt that lists the catalog grows with it; set a ceiling, or send a relevant subset. |
| Lock hold time and contention | Long transactions, and writers that block each other | Time each unit of work from taking the write lock to commit. Run 2–4 processes writing at once and count the retries, the busy errors and the wait. |
| Tail and cold start | The slow call the mean hides | Report p95 and max beside the mean. Time the first call of a process on its own: a model load, a migration, a cache fill. |
| Write cost and file growth | The price of indexes and logs | Benchmark the bare append or insert after adding an index; it pays for every index. Record the database and journal (WAL) size per 1,000 records, and check that the journal is checkpointed. |
| One axis at a time | Costs that grow too fast | Compare time with data across sizes and across the long run. Ten times the data and much more than ten times the time means quadratic. |

What to flag in the `EXPLAIN` output:
- a `SCAN` inside a loop or a correlated subquery;
- a lookup on a column with no index;
- `TEMP B-TREE` over a large set;
- **a bound applied as a filter after a walk instead of as the index range.** The plan says
  `rowid>?` with the wrong bound, or a join order puts the bounding table after the scanned one.

How to read the long run:
- Compare `tracemalloc` snapshots filtered to the project's own source frames.
- Clear the test doubles' own records each round. A fake that records calls looks like a leak.
- Use maxrss as a cross-check.
- Count what the heap doesn't show, at the start and the end: open file descriptors, database
  connections, threads, temp files, child processes. A long-running process fails on these, not
  on memory.

Rank findings by how they grow, not by today's milliseconds. A finding left for later gets its
prototype number when it is found, or the reason it has none, and keeps its rank by growth: the
current data being small is no reason to park it. A "later" list ranked by today's milliseconds
carries a linear cost through audit after audit.

## 3. Prototype the fix before planning it
Put the candidate into the long run or a benchmark from a script outside the repo (patch a
method, swap a query) and measure it. The expected gain is a hypothesis. A profile once showed 95% of the
time in one function, but decoding in SQL saved 35%, because the cost was the rows, not the
decoding. Plan the fix the measurement supports, and say in the plan which prototype numbers it
rests on.

**Prototype against the real dependency, not the tests' fake.** A fake carries the tests'
assumptions. A test helper built an HTTP error with the URL in its message; a real one carries
only the reason, and a "the token leaks into the warning" finding rested on the helper. Use the
real library's error from a local server, a real file or connection, or the real SDK on a mock
transport.

**Time it in the states that bound what it reads,** not only on the benchmark sizes:
- just after a reset, a clear or a merge;
- on empty data, and with one item;
- at the smallest input the operation is called with, as well as the largest (one receipt line
  read, not only forty). An index or a cache built per call costs more than it saves when the
  input is small: a word index that made 40 lines 7 times faster made 1 line 25–36% slower.

A seek whose bound is a filter applied after the walk (`id > last_reset` on an index ordered by
date) is flat on a world with no reset and walks every product's history just after one. Run the
equality check of § 4 on the prototype's worlds before trusting its timings: a wrong fast path
times nothing useful, and its varied worlds are where the slow states turn up.

**An index is part of the fix.** Before adding or replacing one:
- list the statements whose plans use that table's indexes (the `EXPLAIN` sweep's collection),
  and check each still seeks;
- benchmark the bare append or insert with it: every write pays for every index.

An index that looks like it covers another may not answer the other's query: `(a, b, c)` gives
`ORDER BY c` within `(a, b)`, but `MAX(id)` within `(a, b)` needs `(a, b)`, which carries the
rowid at its end.

## 4. Prove the results are the same
A fast path must give what the slow path gives, and a test proves it:
- **A pure rule** (a cut, a cache, a shortcut): an exhaustive test over every input sequence up
  to a small length. Build the alphabet from the enum, so that a new member joins the test with
  no edit.
- **A prefilter or an upper bound:** a brute-force check of random inputs outside the repo,
  with 0 mismatches, before trusting it.
- **A query:** compare it with the slow form on a varied generated world, then on a copy of real
  data. A parameter that turns the cut off (an empty set) gives the slow form for free.
- **An index or a seek:** a query-plan test in the gate. Assert the index name exactly
  (`INDEX name (`), never as a substring of a longer name.
- A test that a mutation cannot fail is not proving anything. Break the fast path once and see it fail.

## 5. Compare, and read the numbers honestly
- Compare against the baseline, with a threshold on the mean (20% is a sane default).
- **Rerun a flagged benchmark alone** before believing it, and look at the stddev of both runs.
- **When benchmarks you didn't touch move together** (every remote benchmark +15%), it's the machine.
  To prove it, run an interleaved A/B: the old commit in a worktree and the new code, alternated
  three times or more in one session, each selection with a control (a benchmark the change
  cannot reach). Drift moves both sides and the control; the change moves only its own. Check
  that the old side imports the old code: a shared virtualenv's editable install points at the
  main tree, so put the worktree's source first on the path (`PYTHONPATH=<worktree>/src`) and
  print a module's `__file__` once. An A/B whose sides run the same code agrees with anything.
- **Save a run only from a commit.** An autosaved run is named after the checked-out commit, so a
  run of uncommitted code carries the previous commit's name and becomes a wrong baseline. Commit,
  then save.
- **When the benchmarks show no gain but the long run does**, the benchmarks lack that axis: add a
  size.
- Report every change over 10% in either direction, with before and after, in the commit message.
- Say what is still linear, and why it is left that way.

## Python defaults
- `pytest-benchmark`: `benchmark.pedantic(setup=...)` and a fresh database copy per round for any
  benchmark that writes; `--benchmark-autosave`; `--benchmark-compare --benchmark-compare-fail=mean:20%`;
  `--benchmark-cprofile=cumtime`.
- SQLite:
  - `sqlite3.Connection.backup` makes the copies.
  - A `factory=` connection subclass counts or delays statements.
  - `EXPLAIN QUERY PLAN` shows the plan.
  - `AS MATERIALIZED` keeps a CTE's bound from being flattened into a filter.
- Memory: `tracemalloc.take_snapshot().filter_traces(...)`, `compare_to(..., "traceback")`.
- Handles:
  - open file descriptors: `len(os.listdir("/dev/fd"))` on macOS, `/proc/self/fd` on Linux;
  - `threading.active_count()`;
  - `pytest -W error::ResourceWarning` for an unclosed file or connection.
- Tail: `benchmark.stats` keeps `max` and the quartiles. For p95, keep the raw rounds
  (`--benchmark-save-data`) or time the long run's rounds yourself.
- Request size: the model SDK's token counter, or the request's byte length when there is none.
- Contention: `multiprocessing` writers on one file database, each counting its `Busy` retries.
- `difflib`: `real_quick_ratio()` and `quick_ratio()` are upper bounds of `ratio()`. Check them
  first, and keep the argument order (`ratio` is not guaranteed symmetric).

## What this skill is NOT
- Not optimizing without a measurement, and not trading clarity for a gain no benchmark shows.
- Not a gate: timings never fail `make test`.
- Not a behavior change: results stay equal (§4). New behavior goes through `/tdd`.

## See also
- `/design` § 2, data access as if remote, and what each cost grows with.
- `/tdd`, for the tests in §4.
- `/validate`, which runs §5 for a feature and for a hot-path step.
