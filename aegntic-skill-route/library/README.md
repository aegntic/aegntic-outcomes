# Library

This plugin has no library assets. It is a router: it selects among other
skills rather than carrying its own domain knowledge.

Durable reference material lives in `../references/`:

| File | Contents |
| :--- | :--- |
| `ROUTES.md` | intent → skill table plus disambiguation rules for every contested cluster |
| `COMPOUND.md` | named chains with the artifact passed between steps and the gate that must pass |
| `CONSOLIDATION.md` | which corpus skills are safe to merge, which are generated build output, and why |

`vendor/` is gitignored by design. It holds third-party skills under their own
upstream licenses; `./install.sh --bundle` rebuilds it from `manifest.json`.
