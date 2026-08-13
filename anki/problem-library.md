# Problem Library

Quick-reference index of useful posts/articles, organized by the *symptom* that should make you think of them — not by topic name. When debugging or designing, scan the symptoms first.

---

## Distributed race on a scarce resource (double-sell / double-book)

**Symptom:** Multiple servers/processes each independently check "is this available?", both see yes, both act — because there's no shared state across servers. Classic case: two users buy the last ticket/seat/inventory unit at the same time and both succeed.

**Reach for:** [BookMyShow interview — distributed locking + fencing tokens (LinkedIn)](https://www.linkedin.com/posts/rajatgajbhiye_bookmyshow-interviewer-how-do-you-stop-two-share-7492087600590032897-ZGV7/)

**One-line insight:** A Redis-based distributed lock (`SET key val NX PX <ttl>`) fixes the naive race, but the TTL itself creates a new failure mode — a lock holder can stall past expiry (GC pause, CPU spike, network delay), lose the lock to another process, then wake up and act anyway ("zombie" writer). The real fix isn't a longer TTL, it's **fencing tokens**: every lock grant carries a monotonically increasing number, every write must include it, and the datastore rejects any write whose token is older than the last one it accepted.

**Details worth keeping:**
- Redis primitive: `SET ticket_45 "server_A" NX PX 5000` — `NX` = only set if key doesn't exist (mutual exclusion), `PX 5000` = auto-expire in 5000ms (prevents permanent deadlock if holder crashes)
- Zombie sequence: A acquires lock → A stalls 6s → lock TTL (5s) expires → B acquires lock and writes → A wakes up, still thinks it holds the lock, writes too → both succeeded
- Why TTL-only locking is fundamentally unsafe: it's making a promise about *time* ("I'll finish before the timer"), and distributed systems can't guarantee bounded pause/delay
- Fencing token fix: lock service hands out token #33, #34, #35... on each grant. DB/store enforces "reject writes with token < highest token seen." A's stale token #33 gets rejected even after B's #34 already committed.
- This generalizes beyond Redis: any lease-based coordination (Zookeeper, etcd, Chubby-style locks) needs the same fencing-token discipline to be safe against pauses.

**When this should fire in your head:** any system-design or debugging scenario involving inventory/seat/ticket allocation, "only one worker should process this job," leader election with a lease, or any bug report shaped like "duplicate processing happened even though we have a lock."

---
