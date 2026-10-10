# ROUTES — intent → skill

Generated intent table. `skill-route` implements this as regex patterns in
`bin/skill-route`; this file is the human-readable source of truth for it.

## Decision table

| Intent | Skill | Not this, because |
|---|---|---|
| root cause, why broken, stack trace, regression, flaky | `investigate` | — |
| build broken, type error, compile failure, lint error | `build-fix` | not a mystery; mechanical |
| security, threat model, CVEs, authz, injection, secrets | `cso` | `review` checks correctness, not posture |
| pre-landing diff review, "ready to merge?" | `review` | — |
| ship, open PR, release | `ship` | ends at PR |
| merge, deploy, promote | `land-and-deploy` | consumes a PR |
| post-deploy monitoring | `canary` | phase of land-and-deploy |
| QA the app, dogfood, what's broken in the app | `qa` | a process, not a tool |
| screenshot, click, fill form, browser automation | `browse` | no bug-hunting intent |
| pull data from a page | `scrape` | read-only extraction |
| make it bolder/quieter/cleaner/more polished | `impeccable` (+ verb) | verb is a modifier, not a router |
| design system, palette, brand guidelines | `design-consultation` | system-level, not screen-level |
| design review, WCAG, contrast, visual audit | `design-review` | judgment, no edits |
| think bigger, ambitious, challenge scope | `plan-ceo-review` | on a *given* plan |
| architecture review, data flow, eng review | `plan-eng-review` | plan-time, not code-time |
| auto-review everything | `autoplan` | runs all four |
| deep research, exhaustive, multi-source | `deep-research` | — |
| research, find out, what's true, cite | `research` | bounded |
| spec this out, write a ticket | `spec` | vague intent → executable |
| TDD, test first, coverage gap | `tdd` | — |
| create a skill | `skill-creator` | — |
| audit my skills | `skill-stocktake` | — |
| which skills does this repo need | `agent-sort` | install-time, not audit |
| generate video/image/thumbnail | `higgsfield-generate` | absorbs 15 seedance variants |
| SEO, not ranking, search console | `seo` | — |
| save progress, hand off, checkpoint, resume | `context-save` | — |
| poke holes, what could go wrong | `hate` | — |
| give me ideas, brainstorm | `ideate` | no plan yet |
| how does this codebase work, dependency graph | `graphify` | structural, not a failure |
| run this, prove it worked, CI red | `terminal-ops` | — |

## Disambiguation

**Debug family** — `investigate`, `ce-debug`, `diagnosing-bugs`,
`systematic-debugging`, `fpef-analyzer`, `diagnose-crash`, `validation-gates`.
All find root cause. `investigate` wins (1075L vs 253/139/134/375/98/27, and it's
the only one with an explicit evidence discipline). The others are subsets or
language specializations. Route everything to `investigate`.

**Review family** — `review` (correctness of a diff), `cso` (security posture of
a system). Different detectors, both stand. `prism`, `red-team-tribunal`,
`security-bounty-hunter` are lenses, not entry points.

**Design family** — `impeccable` (change it), `design-review` (judge a built UI),
`plan-design-review` (judge a plan's direction before building), `critique` /
`audit` (lenses inside design-review).

**Browser family** — `browse` (tool), `qa` (process), `scrape` (extraction).
`qa-only` is a *flag* on `qa`, not a skill.

**Tests family** — `tdd` (router) → `tdd-workflow` (engine). The `*-testing` /
`*-tdd` skills are reference material loaded *after* the router fires.

**Session family** — `context-save` / `context-restore`. `handoff` (17L) is an
output format, `checkpoint` is a subset, `strategic-compact` is advice.

**Skill authoring** — `skill-creator` (write), `skill-stocktake` (audit),
`agent-sort` (install-time selection). Three directions, three skills.

## Reference material (never route here directly)

`*-patterns`, `*-security`, `*-testing`, `*-tdd`, `*-verification`,
`*-coding-standards`, `*-conventions`, `*-migrations`.

These are answers, not decisions. Load them *after* a router fires. They already
only load on trigger — the problem is they shouldn't compete for a routing slot.

## Modifiers (fold into their parent)

`bolder`, `quieter`, `colorize`, `distill`, `delight`, `animate`, `adapt`,
`harden`, `optimize`, `typeset`, `clarify`, `overdrive`, `polish`, `critique`,
`audit`, `extract`, `make-interfaces-feel-better`.

Verified: every one opens with the identical sentence *"Invoke /impeccable —
it contains design principles, anti-patterns, and the Context Gathering Protocol."*
They are verbs, not skills.
