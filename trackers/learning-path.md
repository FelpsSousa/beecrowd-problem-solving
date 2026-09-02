# Learning Path

This tracker turns the repository's category and difficulty structure into an actual study plan. The goal is constant, balanced learning across every level of the Beecrowd judge — not grinding one category or camping at one difficulty.

## Principle: spiral sweep

Beecrowd assigns difficulty dynamically (an ELO-like score based on solve/attempt ratio, rebalanced periodically into 10 levels, ~10% of all problems per level). Because of this:

- difficulty is not fixed to a category — every category has problems across most levels
- a problem's exact level can shift over time, so we plan by **tier**, not by exact level number

A **cycle** = one pass through all 9 categories at the same tier before moving to the next tier. This gives breadth immediately (every category touched early) while still allowing enough repetition per category to build real pattern recognition before mixing gets harder. Don't force strict order within a cycle — pick whatever's available in a category at that tier.

## Difficulty tiers

| Tier | Beecrowd levels | Typical doc level |
|------|------------------|--------------------|
| A — Foundations | 1–3 | L1 |
| B — Core | 4–6 | L1 / L2 |
| C — Advanced | 7–8 | L2 / L3 |
| D — Elite | 9–10 | L3 |

## Category weight per cycle

- **High priority (2 problems/cycle):** Data Structures and Libraries, Mathematics, Graphs — these build the memory/structure/graph intuition that feeds directly into the AppSec specialization goal.
- **Standard (1 problem/cycle):** Ad-Hoc, Strings, Paradigms
- **Light (1 problem, can skip a cycle if unavailable):** Beginner (mostly only populated at Tier A — expect it to phase out naturally by Tier C/D), Computational Geometry, SQL

If a light category has nothing left at a given tier, redistribute that slot to a high-priority category instead of forcing it.

## Cycle checklist

Fill in the problem ID once selected, check it off once documented (not just accepted on the platform).

### Tier A — Foundations (levels 1–3)

- [ ] Beginner — `____`
- [ ] Ad-Hoc — `____`
- [ ] Strings — `____`
- [ ] Data Structures and Libraries (1/2) — `____`
- [ ] Data Structures and Libraries (2/2) — `____`
- [ ] Mathematics (1/2) — `____`
- [ ] Mathematics (2/2) — `____`
- [ ] Paradigms — `____`
- [ ] Graphs (1/2) — `____`
- [ ] Graphs (2/2) — `____`
- [ ] Computational Geometry — `____`
- [ ] SQL — `____`

### Tier B — Core (levels 4–6)

- [ ] Beginner — `____`
- [ ] Ad-Hoc — `____`
- [ ] Strings — `____`
- [ ] Data Structures and Libraries (1/2) — `____`
- [ ] Data Structures and Libraries (2/2) — `____`
- [ ] Mathematics (1/2) — `____`
- [ ] Mathematics (2/2) — `____`
- [ ] Paradigms — `____`
- [ ] Graphs (1/2) — `____`
- [ ] Graphs (2/2) — `____`
- [ ] Computational Geometry — `____`
- [ ] SQL — `____`

### Tier C — Advanced (levels 7–8)

- [ ] Ad-Hoc — `____`
- [ ] Strings — `____`
- [ ] Data Structures and Libraries (1/2) — `____`
- [ ] Data Structures and Libraries (2/2) — `____`
- [ ] Mathematics (1/2) — `____`
- [ ] Mathematics (2/2) — `____`
- [ ] Paradigms — `____`
- [ ] Graphs (1/2) — `____`
- [ ] Graphs (2/2) — `____`
- [ ] Computational Geometry — `____`
- [ ] SQL — `____`

### Tier D — Elite (levels 9–10)

- [ ] Ad-Hoc — `____`
- [ ] Strings — `____`
- [ ] Data Structures and Libraries (1/2) — `____`
- [ ] Data Structures and Libraries (2/2) — `____`
- [ ] Mathematics (1/2) — `____`
- [ ] Mathematics (2/2) — `____`
- [ ] Paradigms — `____`
- [ ] Graphs (1/2) — `____`
- [ ] Graphs (2/2) — `____`
- [ ] Computational Geometry — `____`
- [ ] SQL — `____`

## Revisit queue (spaced repetition)

Every problem marked `Review Priority: High` or `Revisit later: [x]` in its README goes here. After every 2–3 completed cycles, run a dedicated revisit pass on this list before starting the next tier.

- {id} — {title} — {why it's worth revisiting}

## Cycle review

After finishing a full tier (all categories above checked), do a short review here — same spirit as `trackers/weekly-review.md` but scoped to the tier:

- Tier completed:
- What patterns became automatic:
- What still needs deliberate practice before advancing:
- Adjustments for the next tier (e.g. rebalance category weights):
