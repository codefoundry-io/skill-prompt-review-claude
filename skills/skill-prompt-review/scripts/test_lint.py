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

    # --- C0 full-value name match: a trailing token must NOT pass folder-match ---
    tj = _write(td, "goodname/SKILL.md", "---\nname: goodname trailing\ndescription: does x, and when\n---\n\nbody\n")
    check(lint.frontmatter_load_issue(tj.read_text(), tj) is not None, "C0: name with a trailing token -> load issue (full-value match, not first token)")

    # --- C8: tool/runtime version pins beyond three-part semver (Python 3.12, Node 22) ---
    tv = _write(td, "tv/references/r.md", "Requires Python 3.12 and Node 22 on the host.\n")
    check(any(crit.startswith("C8 version") for crit, _, _ in lint.lint(tv)), "C8 flags a tool/runtime version pin (Python 3.12 / Node 22)")

    # --- C8: hyphen-suffixed o-series model pins (o4-mini) flagged; O1 label + bare o3 NOT ---
    osx = _write(td, "osx/references/r.md", "route this to o4-mini for speed\n")
    check(any("model pin" in c for c, _, _ in lint.lint(osx)), "C8 flags a hyphen-suffixed o-series pin (o4-mini)")
    # R4 codex-lint: a bare lowercase o-series IS a [script] candidate now; uppercase 'O1' labels are NOT.
    olabel = _write(td, "ol/references/r.md", "See O1 and O2 above (criterion labels).\n")
    check(not any("model pin" in c for c, _, _ in lint.lint(olabel)), "C8 does NOT over-match uppercase 'O1'/'O2' criterion labels")
    obare = _write(td, "ob/references/r.md", "route this to o3 for cost.\n")
    check(any("model pin" in c for c, _, _ in lint.lint(obare)), "C8 flags a bare lowercase o-series pin (o3)")

    # --- R4 codex-lint: C8 scans the shipped DESCRIPTION, not just the body ---
    descpin = _write(td, "dp/SKILL.md", "---\nname: dp\ndescription: routes to gpt-4o for X, and when to use it\n---\n\nbody\n")
    check(any(c.startswith("C8") for c, _, _ in lint.lint(descpin)), "C8 flags a model pin in the frontmatter description")
    descclean = _write(td, "dc/SKILL.md", "---\nname: dc\ndescription: dispatches to codex, gemini, or claude, and when\n---\n\nbody\n")
    check(not any(c.startswith("C8") for c, _, _ in lint.lint(descclean)), "C8 does NOT flag bare CLI names (codex/gemini/claude, no version) in a description")

    # --- R4 codex-lint: context-anchored bare current-year (not any 4-digit number) ---
    byear = _write(td, "by/references/r.md", "assume the current year is 2026 for grounding.\n")
    check(any(c.startswith("C8 time") for c, _, _ in lint.lint(byear)), "C8 flags a context-anchored bare year ('current year is 2026')")
    noyear = _write(td, "ny/references/r.md", "see issue 2026 and read line 2026 in the log.\n")
    check(not any(c.startswith("C8 time") for c, _, _ in lint.lint(noyear)), "C8 does NOT flag a bare 2026 with no temporal anchor")

    # --- R5 codex-lint: C0 must NOT false-fail a valid block-scalar / indented description ---
    blockdesc = _write(td, "bd/SKILL.md", "---\nname: bd\ndescription: |\n  A multi-line description\n  spanning lines, with when to use it.\n---\n\nbody\n")
    check(lint.frontmatter_load_issue(blockdesc.read_text(), blockdesc) is None, "C0: block-scalar (|) description -> no false load-fail")
    plaindesc = _write(td, "pd2/SKILL.md", "---\nname: pd2\ndescription:\n  indented description on the next line, and when\n---\n\nbody\n")
    check(lint.frontmatter_load_issue(plaindesc.read_text(), plaindesc) is None, "C0: indented-continuation description -> no false load-fail")
    emptydesc = _write(td, "ed/SKILL.md", "---\nname: ed\ndescription:\n---\n\nbody\n")
    check(lint.frontmatter_load_issue(emptydesc.read_text(), emptydesc) is not None, "C0: truly empty description -> load issue")

    # --- R5 codex-lint: C4 [script] must flag common excuse + past-failure narratives ---
    c4a = _write(td, "c4a/references/r.md", "The model kept forgetting to close the file. Do not skip this because it previously failed.\n")
    check(any(c.startswith("C4") for c, _, _ in lint.lint(c4a)), "C4 flags 'kept forgetting' / 'previously failed' / 'do not skip because'")
    c4b = _write(td, "c4b/references/r.md", "There is no excuse and it is not a good reason to omit the step.\n")
    check(any(c.startswith("C4") for c, _, _ in lint.lint(c4b)), "C4 flags 'no excuse' / 'not a good reason'")

    # --- R7 codex-lint: C8 recency words, anchored to a release/model/version noun ---
    rec = _write(td, "rec/references/r.md", "route to the newest model for this.\n")
    check(any(c.startswith("C8") for c, _, _ in lint.lint(rec)), "C8 flags a recency word anchored to a release noun ('newest model')")
    recn = _write(td, "recn/references/r.md", "a new file and a recent commit are in the log.\n")
    check(not any(c.startswith("C8") for c, _, _ in lint.lint(recn)), "C8 does NOT flag 'new file' / 'recent commit' (no release noun)")

    # --- R7 codex-lint: AA2 general 'Let me ...' opener (not only 'let me help') ---
    lm = _write(td, "lm/references/r.md", "Let me analyze this input for you.\n")
    check(any(c.startswith("AA2") for c, _, _ in lint.lint(lm)), "AA2 flags a general 'Let me ...' opener")

    # --- R7 codex-lint: AA5 flags decorative dingbats, NOT functional ✓/✗ or → arrows ---
    ding = _write(td, "dg/references/r.md", "Section ❖ header with ✦ decoration.\n")
    check(any(c.startswith("AA5") for c, _, _ in lint.lint(ding)), "AA5 flags decorative dingbats (❖ ✦)")
    fglyph = _write(td, "fg/references/r.md", "status ✓ done, ✗ failed, → next step.\n")
    check(not any(c.startswith("AA5") for c, _, _ in lint.lint(fglyph)), "AA5 does NOT flag functional ✓/✗ or a → arrow")

    # --- R9 codex-lint: a `backticked` model/version id is scoping language (naming it) and is
    #     suppressed deterministically; the SAME id UNbacked is a real pin and still flags. ---
    bt = _write(td, "bt/references/r.md", "the `Gemini 2.5-series` control vs `thinking_level`.\n")
    check(not any("model pin" in c for c, _, _ in lint.lint(bt)), "C8 does NOT flag a backticked `Gemini 2.5-series` (scoping language)")
    ubt = _write(td, "ubt/references/r.md", "always route to Gemini 2.5-series for this.\n")
    check(any("model pin" in c for c, _, _ in lint.lint(ubt)), "C8 flags an UNbacked 'Gemini 2.5-series' pin")

    # --- C3: cost/usage-limit phrasings the criterion names (price, cost, usage cap/limit) ---
    c3 = _write(td, "c3/references/r.md", "The price is high and there is a usage cap per account.\n")
    check(any("world-fact" in c for c, _, _ in lint.lint(c3)), "C3 flags 'price' / 'usage cap' phrasings")

    # --- AA (AI-authorship signature): chat-register detectors + no arrow/em-dash false-flag ---
    aa = _write(td, "aa/references/r.md",
                "Great question! As an AI, I hope this helps.\n"
                "Analyze the file we discussed, as you requested.\n"
                "You might want to maybe validate the input 🎉\n")
    caa = [c for c, _, _ in lint.lint(aa)]
    check(any(c.startswith("AA1") for c in caa), "AA1 flags authoring-conversation carryover ('we discussed' / 'as you requested')")
    check(any(c.startswith("AA2") for c in caa), "AA2 flags chat-register padding ('Great question!' / 'as an AI')")
    check(any(c.startswith("AA3") for c in caa), "AA3 flags a sycophantic softener ('you might want to')")
    check(any(c.startswith("AA5") for c in caa), "AA5 flags an emoji")
    arrow = _write(td, "ar/references/r.md", "A verdict flips FAIL → PASS across the em-dash — this round.\n")
    check(not any(c.startswith("AA5") for c, _, _ in lint.lint(arrow)), "AA5 does NOT flag → arrow or an em-dash as an emoji")

    # --- R5 codex-lint: a QUOTED example phrase is scoping language (a reference teaching a
    #     rule), not real prompt residue — suppressed; the SAME phrase unquoted still fires. ---
    quoted = _write(td, "qx/references/r.md", 'Flag conversational openers like "Great question!" and "as you requested".\n')
    check(not any(c.startswith("AA") for c, _, _ in lint.lint(quoted)), "AA does NOT flag a double-quoted example phrase (scoping language)")
    unq = _write(td, "uq/references/r.md", "Great question! As you requested, here is the plan.\n")
    check(any(c.startswith("AA") for c, _, _ in lint.lint(unq)), "AA still flags the same phrase UNQUOTED (real residue)")

    # --- AA2 (R3 codex-lint): apology + 'I want to be careful here' were named but not detected ---
    aa2b = _write(td, "aa2b/references/r.md",
                  "I'm sorry, I want to be careful here about the config.\n" + "\n".join(f"x{i}" for i in range(4)))
    check(any(c.startswith("AA2") for c, _, _ in lint.lint(aa2b)), "AA2 flags apology 'sorry' / 'I want to be careful here'")

    # --- AA6 (R3 codex-lint): body-language scan — non-consumer-language script in the BODY,
    #     not just the description (C11). A candidate; quoted examples are the reviewer's call. ---
    aa6 = _write(td, "aa6/references/r.md", "# ref\nSome English guidance.\n분석 대상은 한국어 본문.\n")
    check(any(c.startswith("AA6") for c, _, _ in lint.lint(aa6)), "AA6 flags non-consumer-language (Korean) in the body")
    clean6 = _write(td, "cl6/references/r.md", "# ref\nAll English here, arrows → and an em-dash — included.\n")
    check(not any(c.startswith("AA6") for c, _, _ in lint.lint(clean6)), "AA6 does NOT flag an all-English body (arrows/em-dash are not scripts)")

    # --- Trigger-language exemption: a skill's TRIGGER keywords/phrases are intentionally in
    #     the user's language even when it ships (they must match how the user phrases the
    #     request), so the language check exempts QUOTED trigger text and flags only PROSE drift.
    #     AA6 (body): a quoted trigger-phrase line is EXEMPT; unquoted prose still flags.
    trig_body = _write(td, "tb/SKILL.md", FM.format(name="tb") + '## When to use\n- "세션정리"\n- "compact 하자"\n')
    check(not any(c.startswith("AA6") for c, _, _ in lint.lint(trig_body)),
          "AA6 does NOT flag a QUOTED trigger phrase in the body (intentional user-language trigger)")
    prose_body = _write(td, "pb/SKILL.md", FM.format(name="pb") + "This carries 한국어 산문 unquoted in the body.\n")
    check(any(c.startswith("AA6") for c, _, _ in lint.lint(prose_body)),
          "AA6 still flags UNQUOTED non-Latin prose in the body")
    # C11 (description): quoted trigger keywords are EXEMPT; unquoted description prose flags.
    trig_desc = _write(td, "trd/SKILL.md", '---\nname: trd\ndescription: Use when the user says "세션정리" or "정리하자", the trigger phrases.\n---\n\nbody\n')
    check(not any(c.startswith("C11") for c, _, _ in lint.lint(trig_desc)),
          "C11 does NOT flag QUOTED trigger keywords in the description")
    prose_desc = _write(td, "prd/SKILL.md", "---\nname: prd\ndescription: 한국어 설명 without quotes, and when to use it.\n---\n\nbody\n")
    check(any(c.startswith("C11") for c, _, _ in lint.lint(prose_desc)),
          "C11 still flags UNQUOTED non-Latin prose in the description")
    # AA6 robustness: an earlier UNBALANCED quote (e.g. 6" inches) must NOT exempt a later
    # unquoted non-Latin prose line — the per-line balanced strip fails toward flagging,
    # unlike a body-start parity count that a lone " would invert for the whole remainder.
    unbal = _write(td, "unbal/SKILL.md", FM.format(name="unbal") + 'The screen is 6" wide.\n한국어 산문 line here.\n')
    check(any(c.startswith("AA6") for c, _, _ in lint.lint(unbal)),
          "AA6 flags non-Latin prose AFTER an unbalanced quote (no body-start-parity false-exempt)")

if FAILS:
    print(f"RED — {len(FAILS)} failing test(s):")
    for m in FAILS:
        print("  FAIL:", m)
    sys.exit(1)
print("GREEN — all lint doctor-mode tests pass.")
sys.exit(0)
