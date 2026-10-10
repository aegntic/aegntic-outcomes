---
name: skill-route
description: Route any request to the right skill in a 2000+ skill corpus. Use when the user asks "which skill", when several skills plausibly match, or when a task spans multiple skills. Read-only; never modifies skills.
version: 1.0.0
license: MIT
---

# skill-route

A **router**, not a skill library. This corpus has ~2,000 installed skills across
~20 roots. The failure mode is not missing capability — it's an agent guessing
wrong and burning a turn. This skill turns intent into one named skill.

## Use it

```bash
skill-route "why is my test failing"      # → investigate (+ why it chose that)
skill-route "make this bolder"            # → bolder, then impeccable
skill-route --index                       # corpus stats + per-root counts
skill-route --doctor                      # verify every dependency resolves
skill-route --bundle                      # vendor deps → self-contained
skill-route --contested                   # skills with >1 installed path
skill-route --dead                        # content-free import stubs
skill-route --resolve <name>              # canonical path + all copies
skill-route --refresh                     # rebuild cache after installing skills
```

## Dependencies

This router routes to 41 skills; it does not implement them. `manifest.json`
declares every one with provenance:

- **generated (9)** — gstack build output, not vendored. A copy would go stale
  on the next upstream update and lose host-specific frontmatter. Run
  `skill-route --doctor` for the install command.
- **vendored (32)** — hand-authored, copied into `vendor/` by `--bundle`.

**A missing dependency never becomes a phantom.** If a query's only match isn't
installed or vendored, `skill-route` exits **3** and prints how to get it.
Exit **2** means no route at all; exit **0** means you have a working answer.

## How to read the answer

The tool prints up to 5 candidates with a reason for each. It never returns a
silent guess — if nothing matches it says `no route` and exits non-zero.

- **Take the first candidate** unless the reason says otherwise.
- **Two exact-name hits** means the user named two skills. Chain them; that's
  usually a compound request, not an ambiguity.
- **An `impeccable`-adjacent hit** (bolder, quieter, colorize, distill, animate,
  adapt, harden, typeset, clarify, delight, overdrive, polish) means the verb
  modifier is real but it delegates — run the modifier, then `impeccable`.
- **`no route`** means the corpus genuinely doesn't cover it. Say so, don't guess.

## Rules

1. **One router per turn.** If two routers match, that's a chain, not a choice.
2. **Modifiers are not routers.** "Make it bolder" is an instruction *to* the
   design skill, not a second skill to load alongside it.
3. **Router first, reference second.** Framework skills (`django-patterns`,
   `springboot-security`) are answers, not decisions. Never route to one directly —
   load it *after* the router says "yes, we're building Django."
4. **Nothing here deletes or edits skills.** This tool only reads. Any
   consolidation is a separate, explicit, reversible operation.

## When the corpus changes

`--refresh` rebuilds the index. The cache auto-expires after an hour, so a
routine `skill-route <query>` is always current without ceremony. Run
`--contested` or `--dead` to audit duplication.

> **Caution on consolidation.** Skills with multiple paths are often *generated*
> host variants (gstack builds 10+ per skill via `hosts/*.ts`, each with its own
> frontmatter schema and root paths). Symlinking or deleting them breaks the
> hosts. Verify a skill is a genuine duplicate before consolidating it. See
> `references/CONSOLIDATION.md`.

## Files

- `references/ROUTES.md` — the full intent→skill table with disambiguation rules
- `references/COMPOUND.md` — named chains with artifacts and gates
- `references/CONSOLIDATION.md` — what's safe to merge, what isn't, and why
