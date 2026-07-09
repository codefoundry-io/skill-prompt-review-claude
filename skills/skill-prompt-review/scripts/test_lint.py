#!/usr/bin/env python3
"""RED/GREEN tests for lint.py doctor-mode changes (C0 load-check, target_kind, C9 gate).

Run: python3 test_lint.py   (exit 0 = GREEN, 1 = RED). Python 3.12, no deps.
Before the doctor-mode patches these FAIL (functions/behaviour absent); after, they pass.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import lint  # noqa: E402

FAILS: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        FAILS.append(msg)


def _write(root: str, rel: str, text: str) -> Path:
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


FM = "---\nname: {name}\ndescription: does a thing, and when to use it\n---\n\n# body\n"

with tempfile.TemporaryDirectory() as td:
    skill = _write(td, "my-skill/SKILL.md", FM.format(name="my-skill"))
    ref = _write(td, "my-skill/references/common.md", "# ref\n")
    prompt = _write(td, "my-skill/prompt.txt", "a prompt\n")

    # --- target_kind ---
    check(hasattr(lint, "target_kind"), "lint.target_kind exists")
    if hasattr(lint, "target_kind"):
        check(lint.target_kind(skill) == "skill", "target_kind: SKILL.md -> skill")
        check(lint.target_kind(ref) == "reference", "target_kind: references/ -> reference")
        check(lint.target_kind(prompt) == "prompt", "target_kind: other -> prompt")

    # --- C0 frontmatter_load_issue ---
    check(hasattr(lint, "frontmatter_load_issue"), "lint.frontmatter_load_issue exists")
    if hasattr(lint, "frontmatter_load_issue"):
        f = lint.frontmatter_load_issue
        check(f(skill.read_text(), skill) is None, "C0: valid SKILL.md -> None")
        bad_blank = _write(td, "bad1/SKILL.md", "\n" + FM.format(name="bad1"))
        check(f(bad_blank.read_text(), bad_blank) is not None, "C0: leading blank line -> issue")
        bad_name = _write(td, "bad2/SKILL.md", FM.format(name="wrong-name"))
        check(f(bad_name.read_text(), bad_name) is not None, "C0: name != folder -> issue")
        bad_noname = _write(td, "bad3/SKILL.md", "---\ndescription: x\n---\n\nbody\n")
        check(f(bad_noname.read_text(), bad_noname) is not None, "C0: missing name -> issue")

    # --- C0 surfaces through lint() for a skill, not for a prompt ---
    bad_name2 = _write(td, "bad4/SKILL.md", FM.format(name="not-bad4"))
    crits_skill = [c for c, _, _ in lint.lint(bad_name2)]
    check(any(c.startswith("C0") for c in crits_skill), "lint() flags C0 on a broken SKILL.md")
    crits_prompt = [c for c, _, _ in lint.lint(prompt)]
    check(not any(c.startswith("C0") for c in crits_prompt), "lint() no C0 on a prompt")

    # --- C9 body-length gated to skill: a long PROMPT must NOT get the 'move to references/' flag ---
    long_prompt = _write(td, "lp/big.txt", "\n".join(f"line {i}" for i in range(260)))
    crits_lp = [c for c, _, _ in lint.lint(long_prompt)]
    check(not any("C9 body length" in c for c in crits_lp), "long prompt -> no C9 body-length flag")

    # --- regression: a long SKILL.md still flags C9 body-length ---
    long_skill = _write(td, "ls/SKILL.md", FM.format(name="ls") + "\n".join(f"x{i}" for i in range(260)))
    crits_ls = [c for c, _, _ in lint.lint(long_skill)]
    check(any("C9 body length" in c for c in crits_ls), "long SKILL.md -> C9 body-length flag (regression)")

    # --- C8 model-pin regex must catch current Anthropic codenames (Fable / Mythos), not only OpenAI's ---
    fable = _write(td, "fb/references/ref.md", "Use Claude Fable 5 and Mythos 5 here.\n")
    crits_fb = [c for c, _, _ in lint.lint(fable)]
    check(any("model pin" in c.lower() for c in crits_fb), "C8 flags a Fable/Mythos model pin")

    # --- BLOCKER regression: emitted line numbers must be FILE-relative, not body-relative ---
    dt_content = "---\nname: dt\ndescription: does a thing, and when\n---\n\nfiller line\ntoken 2020-01-01 end\n"
    dt = _write(td, "dt/SKILL.md", dt_content)
    date_file_line = dt_content[: dt_content.index("2020-01-01")].count("\n") + 1
    c8_locs = [locs for crit, _, locs in lint.lint(dt) if crit.startswith("C8 time")]
    check(bool(c8_locs) and f"L{date_file_line}" in c8_locs[0],
          f"C8 date reported at file line L{date_file_line} (not body-relative)")

    # --- C0 must not false-positive on an inline YAML comment on the name field ---
    ic = _write(td, "ic/SKILL.md", "---\nname: ic  # a comment\ndescription: does x, and when\n---\n\nbody\n")
    check(lint.frontmatter_load_issue(ic.read_text(), ic) is None, "C0: inline comment on name -> no false load-fail")

    # --- C0 must not false-fail on CRLF line endings ---
    crlf = _write(td, "cr/SKILL.md", "---\r\nname: cr\r\ndescription: does x, and when\r\n---\r\n\r\nbody\r\n")
    check(lint.frontmatter_load_issue(crlf.read_text(), crlf) is None, "C0: CRLF file -> no false load-fail")

    # --- C6/C10 density must not trip on a short prompt (the skill's primary target) ---
    shortp = _write(td, "sp/p.txt", "\n".join(["MUST do a thing", "you MUST be careful"] + [f"line {i}" for i in range(8)]))
    check(not any("C6 imperative" in c for c, _, _ in lint.lint(shortp)), "short prompt -> no spurious C6 density")

    # --- C8 dates: slash + month-name forms ---
    dref = _write(td, "d2/references/r.md", "on 2026/07/09 and July 9, 2026 it changed\n")
    check(any("time-stamped" in c for c, _, _ in lint.lint(dref)), "C8 flags slash + month-name dates")

    # --- C8 version: v-prefixed semver ---
    vref = _write(td, "v2/references/r.md", "pinned to v1.2.3 in code\n")
    check(any(crit.startswith("C8 version") for crit, _, _ in lint.lint(vref)), "C8 flags a v-prefixed version")

    # --- C8 codenames: bare 'Fable' flagged; lowercase 'terra firma'/'luna' NOT over-matched ---
    cn = _write(td, "cn/references/r.md", "The Fable model is here.\n")
    check(any("model pin" in c for c, _, _ in lint.lint(cn)), "C8 flags bare 'Fable' codename")
    tf = _write(td, "tf/references/r.md", "walking on terra firma under the luna sky\n")
    check(not any("model pin" in c for c, _, _ in lint.lint(tf)), "C8 does NOT over-match lowercase 'terra firma' / 'luna'")

    # --- C10 curly-apostrophe don't is counted ---
    ap = _write(td, "ap/references/r.md", "\n".join(["don’t do this"] * 5 + [f"x{i}" for i in range(30)]))
    check(any("negation density" in c for c, _, _ in lint.lint(ap)), "C10 counts a curly-apostrophe don't")

if FAILS:
    print(f"RED — {len(FAILS)} failing test(s):")
    for m in FAILS:
        print("  FAIL:", m)
    sys.exit(1)
print("GREEN — all lint doctor-mode tests pass.")
sys.exit(0)
