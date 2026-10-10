# COMPOUND — how to chain

Every chain names **the artifact passed between steps** and **the gate that must pass**.
A chain without a gate is a wish, not a process — those are marked **advisory**.

Routers referenced here are the 32 in `ROSTER.md`.

---

## 1. Idea → shipped feature

```
user idea
  → 1. office-hours        produces: a direction (is this worth building?)
       GATE: a named user + a painful job exists. Else stop.
  → 2. ideate              consumes: direction
                            produces: 3–7 grounded options
       GATE: one option survives its own evaluation. Else re-ideate.
  → 3. hat                 consumes: the chosen option
                            produces: one load-bearing objection + cheapest test of it
       GATE: the objection is answered or the option dies.
  → 4. spec                consumes: the surviving option
                            produces: an executable spec in the tracker
       GATE: every acceptance criterion is testable.
  → 5. plan-eng-review     consumes: spec
                            produces: architecture + data flow + test plan
       GATE: no unresolved blocking questions.
  → 6. tdd                 consumes: the test plan
                            produces: red → green → refactored
       GATE: tests fail before the fix and pass after.
  → 7. review              consumes: the diff
                            produces: findings
       GATE: zero blocking findings.
  → 8. ship                consumes: clean branch
                            produces: a PR
  → 9. document-release    consumes: the merged PR
                            produces: docs that match what shipped
```

**Advisory** — steps 8→9 are only coupled if the project keeps docs. Otherwise 9 is
`ce-compound` on a solved problem, not a doc update.

---

## 2. Something is broken

```
symptom (stack trace / red test / wrong output)
  → 1. investigate         consumes: symptom
                            produces: a proven root cause + the evidence for it
       GATE: you can state the cause in one sentence and show the evidence.
             "Not sure yet" is a failed gate, not a pass.
  → 2. tdd                 consumes: the root cause
                            produces: a failing test that reproduces it
       GATE: the test fails for the reason you diagnosed (not a different reason).
  → 3. fix                 produces: green
       GATE: test green AND no sibling test regressed.
  → 4. review              consumes: the fix diff
       GATE: no findings that would have let the bug back in.
```

**Never** skip 1. Every "just fix it" in this corpus that skipped it produced a patch for
a symptom. `investigate`'s Iron Law is the gate.

---

## 3. Performance regression

```
"it's slow now"
  → 1. investigate         produces: a measured bottleneck, not a guess
       GATE: you have a number and a profile, not an intuition.
  → 2. latency-critical-systems   consumes: the profile
                            produces: the p95 budget and the freshness contract
       GATE: the fix has a target metric written down.
  → 3. benchmark           consumes: the target
                            produces: before/after numbers
       GATE: improvement is measured, not asserted.
```

---

## 4. Security review

```
a system or diff
  → 1. cso                 produces: secrets scan + dependency CVEs + OWASP pass
       GATE: no hardcoded secrets. This is binary.
  → 2. security-threat-model   consumes: the system
                            produces: trust boundaries + abuse paths
       GATE: every asset has an owner and a boundary.
  → 3. review              produces: injection/authorization findings on the diff
       GATE: no SQLi, no unscoped auth, no leaked error internals.
  → 4. production-audit    produces: what breaks in prod that passed CI
       GATE: the failure modes are ranked and owned.
```

---

## 5. Design iteration with real visual evidence

```
a screen or product
  → 1. design-consultation   produces: DESIGN.md (palette, type, spacing, motion)
       GATE: DESIGN.md exists and the product has a named audience.
  → 2. shape / frontend-interview   produces: a design brief
       GATE: the brief states the job, not just the aesthetic.
  → 3. impeccable           consumes: brief + DESIGN.md
                            produces: an implementation with a point of view
       GATE: it is not the generic default for this category.
  → 4. design-review        produces: P0–P3 findings with screenshots
       GATE: zero P0/P1.
  → 5. iterate              ← loop 3→4 until clean
  → 6. web-perf             produces: Core Web Vitals
       GATE: LCP/CLS/INP pass. (Design that fails CWV is not done.)
```

**The loop at 5 is the whole point.** A single design pass without a review pass is a
guess. `design-shotgun` is the parallel variant when you need options, not a correction.

---

## 6. Long-running autonomous work

```
a project larger than one session
  → 1. context-save        produces: a snapshot at every phase boundary
       GATE: snapshot exists before starting, not after.
  → 2. blueprint           produces: a dependency graph of work units,
                                  each with a cold-start context brief
       GATE: each unit can be executed by an agent with zero history.
  → 3. ralphinho-rfc-pipeline / parallel-execution-optimizer
                            produces: parallel execution across independent units
       GATE: units are truly independent. Shared files → serialize.
  → 4. review + tdd        per unit, before merge
  → 5. re0-memo            consumes: what was built and what failed
                            produces: lessons that survive into the next cycle
       GATE: the memo names at least one thing that did not work.
  → 6. context-save        ← return to 1
```

**Advisory** — step 3's parallelism is only safe when units don't share write targets.
`parallel-execution-optimizer` is where that check lives.

---

## 7. Research → decision → artifact

```
an open question
  → 1. research             produces: a cited markdown file in the repo
       GATE: every claim has a source. Uncited = not done.
  → 2. factchk              consumes: the draft
                            produces: verified claims + flagged judgments
       GATE: no claim survives on intuition alone.
  → 3. knowledge-artifacts  produces: a designed, readable HTML artifact
       GATE: a human can read it without the raw sources.
```

---

## 8. Ship a skill (dogfooding the meta)

```
an idea for a new skill
  → 1. skill-scout          produces: whether this already exists
       GATE: it does not exist. Else stop and adopt.
  → 2. skill-creator        produces: SKILL.md
       GATE: the description disambiguates from its 3 nearest neighbours.
  → 3. sip                  consumes: the new skill
                            produces: a taste-test against the existing suite
       GATE: it does not duplicate an existing trigger.
  → 4. skill-stocktake      produces: a score
       GATE: ≥ its cluster's bar, or it's retired.
```

Step 3 exists because this corpus demonstrates the failure mode: **the most common
defect here is a duplicate trigger, not a bad skill.**

---

## 9. The corpus itself (this exercise)

```
1,890 → 2,106 SKILL.md files
  → 1. inventory            produces: inventory.json (every file, one row)
       GATE: count reconciles with the filesystem.
  → 2. mirror-map           produces: body_sha groups
       GATE: identical bodies are provably identical, not assumed.
  → 3. cluster              produces: capability clusters (IDENTICAL/SUPERSET/ADJACENT)
       GATE: ADJACENT is never merged — only linked.
  → 4. verdict              produces: one verdict per skill, no orphans
  → 5. ROSTER/ROUTING/COMPOUND
  → 6. MUTATION GATE        ← STOP. No file touched without approval.
```

The gate at 6 is load-bearing. A distillation that deletes before it has shown its work
is indistinguishable from a distillation that guessed.

---

## What compound means here

Compounding is **artifact passing**, not skill chaining. The test of a chain is whether
step N's output is literally step N+1's input, and whether a gate exists that can fail.

A chain of five skills with no gates is five skills and no process.
A chain of three skills with real gates is a process.
