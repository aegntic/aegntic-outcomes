# CONSOLIDATION — what is safe to merge, and what isn't

Findings from the corpus audit. **Nothing here was executed.** Read before
consolidating anything.

## The trap: generated host variants

A skill with 20 installed paths is almost certainly **generated**, not duplicated.

```
.agents/skills/gstack/.hermes/skills/gstack-review/SKILL.md   1499L
.agents/skills/gstack/.kiro/skills/gstack-review/SKILL.md     1838L
.agents/skills/gstack/review/SKILL.md                         1853L
```

They are not byte-identical. Differences:

| Difference | Example |
|---|---|
| Frontmatter schema | `.hermes` uses `description: <block>`. `.agents` uses `preamble-tier`, `allowed-tools:`, `triggers:`. |
| Feature blocks | gbrain health check present in `.hermes`, absent in `.slate` |
| Root resolution | `$HOME/.hermes/skills/gstack` vs `$HOME/.kiro/skills/gstack` |

Root cause — `~/.agents/skills/gstack/setup:441`:

```bash
# .agents/ is no longer committed — generated at setup time from .tmpl templates.
# bun run build already does this...
AGENTS_DIR="$SOURCE_GSTACK_DIR/.agents/skills"
NEEDS_AGENTS_GEN=1
```

Ten host adapters in `hosts/{claude,codex,cursor,factory,gbrain,hermes,kiro,
openclaw,opencode,slate}.ts` generate them via `bun run gen:skill-docs --host <host>`.

**Consequence:** symlinking or deleting host variants breaks them. Each host needs
its own frontmatter schema and its own root path baked into the body. Deleting the
copies just makes `setup` regenerate them.

**Fix duplication at the source instead** — `.tmpl` templates, `gen-skill-docs.ts`,
and `hosts/*.ts`. Duplicate *there* propagates to all ten hosts.

**Also:** check which hosts are actually installed. `setup --host auto` only
generates for detected binaries. Running with explicit `--host` flags creates the
extras. Those regenerating every upgrade are dead weight.

## Safe to consolidate

**1. The 121 content-free import stubs.** Description is literally
`"Migrated source command \`X\`"`; the body is a pasted upstream markdown file.
Move to `references/imported-commands/`. Pure move, zero risk, biggest
search-cost win — any keyword search for "review"/"plan"/"build" hits these first.

Find them: `skill-route --dead`

**2. The 18 design modifiers → `impeccable`.** Verified in file bodies: all open
with the same *"Invoke /impeccable"* sentence. Move bodies to
`impeccable/references/modifiers/<verb>.md` + a routing table. Bodies preserved verbatim.

**3. The 15 seedance variants → `higgsfield-generate`.** `01-cinematic` …
`15-real-estate` are one prompt skill with a style table. "Make a video" currently
fires all 15.

**4. The session-context family → `context-save`/`context-restore`.** `handoff`
(17L) is an output format; `checkpoint` (826L) is a strict subset of `context-save`
(1029L); `strategic-compact` is advice, not a mechanism.

**5. The 64 real-description `source-command-*` orphans.** Not renames — only
`learn` has a non-prefixed twin. They split three ways:

| Group | Verdict |
|---|---|
| `jira`, 5× flow-nexus, `react-test`, `kotlin-test`, `cost-report`, `save-session`, hookify×4 | ABSORB — supersets exist |
| `build-fix`, `go-build`, `rust-build`, `cpp-build`, `kotlin-build`, `gradle-build`, `flutter-build` | REFERENCE — language-specific |
| `skill-health`, instinct family (`import/export/status`, `promote`, `prune`, `projects`) | KEEP — genuine sub-surfaces |

## Do not consolidate

**~400 framework reference skills.** `django-patterns`, `springboot-security`,
`quarkus-tdd`, `postgres-patterns`, `cisco-ios-patterns`,
`carrier-relationship-management`. These are *answers*, not decisions — they load
only when their trigger fires. Merging Django into Spring loses detail.

The fix isn't deletion, it's **exclusion from the routing surface**: mark them
`kind: reference` in frontmatter so they don't compete for a decision slot.

**`.hermes/skills`.** Only 2 names overlap with `.agents`; 66 are hermes-only
(the seedance set, the Higgsfield suite). A separate product surface, not
duplication.

**A wide root like `~/AE`.** 4,526 of the 7,638 files sit under
`/mnt/ubuntu/home/ae/AE`. That's a vault, not a skill root. If it's in your
config, every scan pays for it.

## Verify before merging

```bash
skill-route --contested          # >1 installed path
skill-route --resolve <name>     # where exactly?
skill-route --refresh            # after installing skills
```

If a skill was installed by a generator (`hosts/*.ts`, `setup`, a `.tmpl`), do not
consolidate it. Find the generator and fix it there.
