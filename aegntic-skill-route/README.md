# Install

## What this is

`skill-route` — one read-only router over a ~2,000-skill corpus.

The problem it solves: the corpus is large enough that an agent guessing which
skill to load is the dominant failure mode. Not missing capability — wasted turns.

It **never modifies, moves, or deletes a skill.** Consolidation is a separate,
explicit, reversible operation.

## Install

```bash
cd ~/.skill-distill/plugin      # or wherever you put it

./install.sh          # symlink the skill into .agents/, .claude/, .hermes/
./install.sh --bundle # vendor deps → self-contained (recommended)
./install.sh --link   # also put `skill-route` on PATH (~/.local/bin)
./install.sh --doctor # verify every dependency resolves
./install.sh --check  # status, changes nothing
./install.sh --uninstall
```

Symlinks only. Re-running is a no-op. Uninstall removes exactly what it created
(marked with `.skill-route-install`) and nothing else. `--bundle` writes only to
`$HERE/vendor/`, inside the plugin — never to a corpus root.

## Dependencies & the bundle

The router routes to **41 skills**. It does not implement them, so the honest
question is: what happens when one is missing?

**`manifest.json` declares every one of them**, with provenance:

| Provenance | Count | Handling |
|---|---|---|
| `generated` | 9 | gstack build output. **Not vendored** — a copy goes stale on the next upstream update and loses host-specific frontmatter. Declared with its install command. |
| `vendored` | 32 | Hand-authored, stable. **Copied into `vendor/`** by `--bundle`, making the plugin self-contained. |

```
./install.sh --bundle     # copy the 32 hand-authored deps into vendor/ (488 KB)
./install.sh --doctor     # verify all 41 resolve; exits 1 if any don't
```

**Why not vendor everything.** gstack's 9 skills are built by
`hosts/*.ts` from `.tmpl` templates — 44 host variants each, with different
frontmatter schemas and baked-in root paths. Copying one freezes a build
artifact. Declaring them is correct; copying them is the trap this whole
audit exists to avoid.

**Phantom protection.** A router that confidently sends you to a skill that
doesn't exist is worse than no router. So:

- `--doctor` exits **1** if any routed-to skill is neither installed nor vendored
- a query whose only match is missing exits **3** and prints the install command
- the `no_phantoms` test gate fails the suite on any undeclared router

This caught a real one: `build-fix` never existed as a skill — only a
content-free stub. Build failures now route to `investigate`, which handles
root cause and exists. **41/41 resolve.**

**With no corpus at all** (fresh machine, empty `HOME`):

```
$ skill-route --doctor
32/41 routers resolve.
9 MISSING — the router can emit these but cannot run them.
  9 come from the 'gstack' plugin:
    git clone https://github.com/garrytan/gstack && cd gstack && ./setup --host auto

$ skill-route "make it bolder"
  → bolder   (from vendor/)          ← works, self-contained

$ skill-route "ship it"; echo $?
  ✗ no installed skill for this request.
    would route to: ship
    run 'skill-route --doctor' for how to install...
3                                  ← hard-block, never a phantom
```

## Verify

```bash
python3 test_skill_route.py                    # 62 checks
uvx ruff check bin/ test_*.py                  # lint
bash -n install.sh                             # shell syntax
./install.sh --doctor                          # dependency health
```

Test coverage:

| Gate | What it proves |
|---|---|
| 40 routing cases | each intent resolves to the right skill |
| 3 negative cases | generic words don't hijack (`audit my skills` ≠ design-audit) |
| 13 edge cases | empty, whitespace, unicode, `--` separator, all flags, bad `--resolve`, doctor, bundle |
| bounded output | a 20k-char query doesn't echo 20k chars; no ReDoS |
| cache resilience | corrupt / truncated / empty cache all self-heal |
| read-only | runs against a `chmod 555` root without modifying it |
| installer | idempotent; refuses to clobber a pre-existing `skill-route`; uninstall never deletes what it didn't create |
| **no phantoms** | every routed-to skill is declared, and `--doctor` exits 0 |
| **self-contained** | with no corpus, vendored skills resolve and missing ones hard-block with rc=3 |

Measured: **58ms** warm query, **2.5s** cold index, **25MB** peak RSS.
Zero dependencies beyond the Python stdlib.

## Files

```
plugin/
├── SKILL.md                       the router skill (frontmatter + rules)
├── bin/skill-route                the tool — intent table + corpus index + deps
├── manifest.json                  every dependency, with provenance
├── vendor/                        32 self-contained deps (488 KB, --bundle)
├── install.sh                     symlink installer
├── test_skill_route.py            62 checks across 9 gates
└── references/
    ├── ROUTES.md                  intent→skill table + disambiguation
    ├── COMPOUND.md                chains with artifacts and gates
    └── CONSOLIDATION.md           what merges safely, what doesn't, why
```

~500 lines of Python, zero dependencies beyond stdlib.

## Design decisions

**Runtime index, not a baked list.** The corpus is 2,081 skills across 22 roots
and changes whenever a plugin updates. `skill-route` reads roots from
`~/.hermes/config.yaml` plus the three primary dirs, and caches for an hour.
Editing a routing rule takes effect immediately; no regeneration step.

**Nested roots are pruned.** `~/AE` contains `~/AE/skills`, `~/AE/agent-forge/skills`,
etc. Without pruning, a broad root silently absorbs every narrower one beneath it
and the count inflates ~3×.

**Everything is explainable.** Every answer carries the matched phrase. A
non-match exits 2 with `no route` — it never guesses.

**Single-word names are opt-in.** `audit my skills` must not resolve to the
design-audit skill. Only multi-hyphen names, plus a vetted list of design verbs,
get exact-match priority. Intent phrases that *contain* a named token win, so
"review the architecture" routes to `plan-eng-review`, not `review`.

## Cost

| | |
|---|---|
| warm query | ~58ms |
| cold index build | ~2.5s (7,640 files) |
| peak RSS | ~25 MB |
| cache | 1.3 MB, `~/.cache/skill-route/` |
| refresh | `--refresh`, or automatic after 1h |
| deps | stdlib only |

## Optional: wire into AGENTS.md

Add this to your `AGENTS.md` so the router is consulted before guessing:

```markdown
## Skill routing

This machine has ~2,000 installed skills. Before loading one by guess, run:

    skill-route "<the user's request>"

It returns ranked candidates with the reason for each. Take the first unless the
reason says otherwise. A design-verb hit (bolder, quieter, typeset…) means run the
modifier, then `impeccable`, which it delegates to. `no route` means the corpus
genuinely doesn't cover it — say so rather than guessing.

Framework skills (`*-patterns`, `*-security`, `*-testing`) are answers, not
decisions: never route to one directly, load it after the router fires.
```

## What it will not do

It will not tell you to delete anything, and it will not consolidate anything.
`references/CONSOLIDATION.md` explains the trap: most multi-path skills are
**generated host variants** (gstack builds 10+ per skill via `hosts/*.ts`, each
with its own frontmatter schema and root paths). Symlinking or deleting them
breaks the hosts that need them. `setup` regenerates them anyway.

Fix duplication at the generator — `.tmpl`, `gen-skill-docs.ts`, `hosts/*.ts` —
not in the generated trees.
