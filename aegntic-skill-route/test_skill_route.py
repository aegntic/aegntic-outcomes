"""Test skill-route. Run: python3 test_skill_route.py
Exit 0 = all pass. No network; writes only to a temp cache."""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BIN = str(Path(__file__).parent / "bin" / "skill-route")

# (query, expected_first_skill or None if any-acceptable)
CASES = [
    # debugging
    ("why is my test failing", "investigate"),
    ("this is broken", "investigate"),
    ("stack trace from the worker", "investigate"),
    ("it's been flaky since friday", "investigate"),
    ("debug this error", "investigate"),
    # security
    ("is this secure", "cso"),
    ("audit for vulnerabilities", "cso"),
    ("threat model for the payment service", "cso"),
    ("check for SQL injection", "cso"),
    # review vs ship
    ("review my diff", "review"),
    ("is this ready to merge", "review"),
    ("ship it", "ship"),
    ("open a PR", "ship"),
    ("deploy to prod", "land-and-deploy"),
    # browser
    ("take a screenshot of the dashboard", "browse"),
    ("QA the site", "qa"),
    ("scrape the pricing table", "scrape"),
    # design
    ("make this bolder", "bolder"),          # modifier, then impeccable
    ("make it more polished", "impeccable"),
    ("too loud, tone it down", "quieter"),
    ("we need a design system", "design-consultation"),
    ("does this pass WCAG", "design-review"),
    # plan
    ("think bigger on this scope", "plan-ceo-review"),
    ("review the architecture", "plan-eng-review"),
    ("write me a spec", "spec"),
    # test-first
    ("write the tests first", "tdd"),
    ("add test coverage", "tdd"),
    # skills
    ("create a new skill", "skill-creator"),
    ("audit my skills", "skill-stocktake"),
    ("which skills does this repo need", "agent-sort"),
    # context
    ("save my progress", "context-save"),
    ("pick up where I left off", "context-save"),
    # research
    ("research the market for X", "research"),
    ("deep dive on X", "deep-research"),
    # generation
    ("make me a youtube thumbnail", "higgsfield-generate"),
    ("generate a video", "higgsfield-generate"),
    # adversarial
    ("poke holes in this plan", "hate"),
    ("give me ideas", "ideate"),
    # exact-name path
    ("run context-restore", "context-restore"),
    ("use skill-creator", "skill-creator"),
]

# queries that must NOT route to a wrong-but-plausible skill
NEGATIVE = [
    ("audit my skills", "audit"),       # must not hit the design audit skill
    ("make me a youtube thumbnail", "youtube"),
    ("create a skill", "skill"),
]


def run(*args):
    p = subprocess.run([BIN, *args], capture_output=True, text=True, check=False)
    return p.returncode, p.stdout


def first_skill(out):
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("→ "):
            return s[2:].split(" ")[0].strip()
    return None


def want_hint(q):
    return "an intent-matched skill"


# ── gates 2–4: edge cases, cache, installer ─────────────────────────────────

EDGE = [
    # (args, must_contain, expected_rc)
    ([""], "no route", 2),
    (["   "], "no route", 2),
    (["zzzz qqqq gibberish"], "no route", 2),
    (["why is this broken 🔥 测试"], "investigate", 0),   # unicode must not crash
    (["--index"], "skills across", 0),
    (["--contested"], "have >1 path", 0),
    (["--dead"], "import stubs", 0),
    (["--", "--index"], "no route", 2),   # -- must stop flag parsing
    (["--", "ship it"], "ship", 0),
    (["--resolve", "review"], "copies:", 0),
    (["--resolve", "definitely-not-a-real-skill-xyz"], "no skill named", 1),
    (["--doctor"], "routers resolve", 0),
    (["--bundle"], "generated dep", 0),
]


def edge_cases(fails):
    for args, needle, want_rc in EDGE:
        rc, out = run(*args)
        if rc != want_rc:
            fails.append(f"EDGE   {args!r}: rc={rc} want={want_rc}")
        if needle not in out:
            fails.append(f"EDGE   {args!r}: output missing {needle!r}")


def bounded_output(fails):
    """A 20k-char query must not echo 20k chars back to the terminal."""
    long_q = "review the architecture " * 800
    rc, out = run(long_q)
    if len(out.splitlines()[0]) > 120:
        fails.append(f"BOUND  query echo not bounded ({len(out.splitlines()[0])} chars)")
    if "…" not in out.splitlines()[0]:
        fails.append("BOUND  long query not truncated with ellipsis")
    if time.time() - t0 > 10:
        fails.append("PERF   20k-char query took >10s (possible ReDoS)")
    _ = rc


def cache_resilience(fails):
    """Corrupt, truncated, and empty cache must all self-heal."""
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "skill-route" / "index.json"
    if not cache.exists():
        return
    backup = cache.read_text()
    try:
        for label, payload in (("corrupt", "not json{{{"),
                              ("truncated", backup[:500]),
                              ("empty", "")):
            cache.write_text(payload)
            rc, out = run("ship it")
            if rc != 0 or "ship" not in out:
                fails.append(f"CACHE  {label} cache did not self-heal (rc={rc})")
    finally:
        cache.write_text(backup)


def read_only(fails):
    """Prove the tool never writes into a skill root."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "ro-root"
        root.mkdir()
        (root / "dummyskill").mkdir()
        (root / "dummyskill" / "SKILL.md").write_text(
            "---\nname: dummyskill\ndescription: A dummy skill for read-only testing.\n---\nbody\n")
        os.chmod(root, 0o555)
        try:
            env = dict(os.environ, XDG_CACHE_HOME=str(Path(td) / "cache"))
            p = subprocess.run([sys.executable, BIN, "--refresh"],
                               capture_output=True, text=True, check=False, env=env)
            if p.returncode != 0:
                fails.append(f"RO     --refresh failed on read-only root: rc={p.returncode}")
            if not (root / "dummyskill" / "SKILL.md").exists():
                fails.append("RO     read-only root was modified")
        finally:
            os.chmod(root, 0o755)


def installer(fails):
    """Install must be idempotent and must never clobber a pre-existing skill."""
    inst = Path(__file__).parent / "install.sh"
    if not inst.exists():
        return
    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / "home"
        (home / ".agents" / "skills" / "skill-route").mkdir(parents=True)
        precious = home / ".agents" / "skills" / "skill-route" / "SKILL.md"
        precious.write_text("PRECIOUS")
        env = dict(os.environ, HOME=str(home))
        p = None
        for i in range(2):
            p = subprocess.run(["bash", str(inst)], capture_output=True,
                               text=True, check=False, env=env)
            if p.returncode != 0:
                fails.append(f"INST   install run {i} exited {p.returncode}")
        if precious.read_text() != "PRECIOUS":
            fails.append("INST   install CLOBBERED a pre-existing skill-route")
        if "SKIP" not in (p.stdout + p.stderr):
            fails.append("INST   install did not report SKIP on collision")
        p = subprocess.run(["bash", str(inst), "--uninstall"],
                           capture_output=True, text=True, check=False, env=env)
        if p.returncode != 0:
            fails.append(f"INST   uninstall exited {p.returncode}")
        if not precious.exists():
            fails.append("INST   uninstall DELETED a skill it did not create")


def no_phantoms(fails):
    """Every skill the router can emit must be declared in manifest.json.

    A phantom is the worst failure mode here: the router confidently sends the
    user to a skill that does not exist. --doctor exits non-zero when any
    routed-to skill is neither installed nor vendored.
    """
    import json
    mf = Path(__file__).parent / "manifest.json"
    if not mf.exists():
        fails.append("DEPS   manifest.json missing")
        return
    try:
        json.loads(mf.read_text())
    except json.JSONDecodeError as e:
        fails.append(f"DEPS   manifest.json is not valid JSON: {e}")
        return
    rc, out = run("--doctor")
    if rc != 0:
        fails.append(f"DEPS   --doctor exited {rc}; unresolved:\n"
                     + "\n".join("         " + l for l in out.splitlines()
                                 if l.strip().startswith("✗")))
    if "UNDECLARED" in out:
        fails.append("DEPS   a routed-to skill is undeclared in manifest.json")
    if "WARN declared but never routed" in out:
        fails.append("DEPS   manifest declares a skill the router never emits")


def bundle_self_contained(fails):
    """With no corpus at all, the plugin must still resolve vendored skills and
    hard-block the rest (rc=3) rather than naming something absent."""
    plugin = Path(__file__).parent
    if not (plugin / "vendor").is_dir():
        return  # bundling is optional; skip unless the operator ran --bundle
    with tempfile.TemporaryDirectory() as td:
        env = dict(os.environ, HOME=str(Path(td) / "home"),
                   XDG_CACHE_HOME=str(Path(td) / "cache"))
        (Path(td) / "home").mkdir()
        p = subprocess.run([sys.executable, str(plugin / "bin" / "skill-route"),
                            "--refresh"], capture_output=True, text=True,
                           check=False, env=env)
        if p.returncode != 0:
            fails.append(f"BUNDLE clean-room --refresh failed: {p.returncode}")

        p = subprocess.run([sys.executable, str(plugin / "bin" / "skill-route"),
                            "make it bolder"], capture_output=True, text=True,
                           check=False, env=env)
        if "vendor/" not in p.stdout and "(from vendor/)" not in p.stdout:
            fails.append("BUNDLE vendored skill did not resolve with no corpus:\n"
                         + p.stdout[:200])

        p = subprocess.run([sys.executable, str(plugin / "bin" / "skill-route"),
                            "ship it"], capture_output=True, text=True,
                           check=False, env=env)
        if p.returncode != 3:
            fails.append(f"BUNDLE missing generated dep: rc={p.returncode} want 3 "
                         "(must hard-block, not name a phantom)")
        if "no installed skill" not in p.stdout:
            fails.append("BUNDLE missing dep did not explain itself")


def no_dangling(fails):
    """Every indexed path must be readable.

    Regression: a stale symlink (e.g. a plugin link pointing at a vendor/ tree
    that was deleted and rebuilt) used to be indexed as if present, so the
    router reported skills it could not actually load.
    """
    cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "skill-route" / "index.json"
    if not cache.exists():
        return
    import json
    idx = json.loads(cache.read_text())
    dead = [c for v in idx["skills"].values() for c in v["copies"]
            if not os.path.isfile(c)]
    if dead:
        fails.append(f"DANGLING index lists {len(dead)} unreadable path(s): "
                     + "; ".join(d[:60] for d in dead[:3]))


def main():
    subprocess.run([BIN, "--refresh"], capture_output=True, check=False)
    fails: list[str] = []
    for q, want in CASES:
        _, out = run(q)
        got = first_skill(out)
        if got != want:
            fails.append(f"ROUTE  {q!r}\n       want={want}  got={got}")

    for q, forbidden in NEGATIVE:
        _, out = run(q)
        got = first_skill(out)
        if got == forbidden:
            fails.append(f"NEG    {q!r} resolved to {forbidden!r} (should be {want_hint(q)})")

    # graceful failure
    rc, out = run("zzzz qqqq wwww unrelated gibberish")
    if rc != 2 or "no route" not in out:
        fails.append(f"DEGRADE gibberish: rc={rc} expected rc=2 + 'no route'")

    # explainability: every answer must carry a reason
    for q, _ in CASES[:10]:
        _, out = run(q)
        if not any(k in out for k in ("intent", "named explicitly", "design verb")):
            fails.append(f"EXPLAIN {q!r}: no reason line")

    _, idx_out = run("--index")
    if "skills across" not in idx_out:
        fails.append("INDEX: --index did not report stats")

    edge_cases(fails)
    bounded_output(fails)
    cache_resilience(fails)
    read_only(fails)
    installer(fails)
    no_phantoms(fails)
    no_dangling(fails)
    bundle_self_contained(fails)

    print(f"{len(CASES)} routing · {len(NEGATIVE)} negative · {len(EDGE)} edge "
          f"· 8 invariant gates")
    if fails:
        print(f"\n{len(fails)} FAILED:\n")
        for f in fails:
            print("  " + f)
        return 1
    print("all pass ✓")
    return 0


t0 = time.time()

if __name__ == "__main__":
    sys.exit(main())
