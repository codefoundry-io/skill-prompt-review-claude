#!/usr/bin/env python3
"""RED/GREEN tests for score.py — deterministic verdict parsing + round delta.

Run: python3 test_score.py   (exit 0 = GREEN, 1 = RED). Python 3.12, no deps.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import score  # noqa: E402

FAILS: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        FAILS.append(msg)


BEFORE = """# Review — target
## Findings
- [FAIL] C8 time-stamped facts — a baked date — de-date it
- [FAIL] C16 invocation construction — unquoted path — quote it
- [N-A]  O2 verbosity — API only, N-A to a CLI prompt
## Passed
C1, C2
"""

AFTER = """# Review — target
## Findings
- [FAIL] C16 invocation construction — still unquoted — quote it
- [FAIL] C5 lean — a dedup reopened a restated rule — remove it
- [N-A]  O2 verbosity — API only, N-A to a CLI prompt
## Passed
C1, C2, C8
"""

# --- parse() maps each verdict class ---
vb = score.parse(BEFORE)
check(vb.get("C8") == "FAIL", "parse: C8 -> FAIL")
check(vb.get("C16") == "FAIL", "parse: C16 -> FAIL")
check(vb.get("O2") == "N-A", "parse: O2 -> N-A")
check(vb.get("C1") == "PASS" and vb.get("C2") == "PASS", "parse: Passed list -> PASS")
check("O2" not in [k for k, x in vb.items() if x == "PASS"], "parse: N-A is not counted as PASS")

va = score.parse(AFTER)
check(va.get("C8") == "PASS", "parse: C8 flipped to PASS in AFTER")
check(va.get("C5") == "FAIL", "parse: C5 -> FAIL in AFTER")

# --- tally(): N-A excluded from the denominator ---
pb, fb, appb = score.tally(vb)
check((pb, fb, appb) == (2, 2, 4), f"tally(before) = (PASS 2, FAIL 2, app 4), got {(pb, fb, appb)}")
pa, fa, appa = score.tally(va)
check((pa, fa, appa) == (3, 2, 5), f"tally(after) = (PASS 3, FAIL 2, app 5), got {(pa, fa, appa)}")
check(score.rate(pb, appb) == "50%" and score.rate(pa, appa) == "60%", "pass-rate 50% -> 60%")

# --- scoreboard delta: flips / new / residual, with guardrails ---
board = score.scoreboard(va, vb)
# residual FAIL section is FIRST (guardrail: load-bearing above the rate)
resid_i = board.index("Residual FAIL")
rate_i = board.index("pass-rate")
check(resid_i < rate_i, "guardrail: residual FAIL is printed ABOVE the pass-rate")
check("C16" in board and "C5" in board, "residual FAIL names C16 and C5 (both still failing)")
flip_line = [ln for ln in board.splitlines() if "Flipped FAIL" in ln]
flip_body = board.splitlines()[board.splitlines().index(flip_line[0]) + 1]
check("C8" in flip_body and "C16" not in flip_body, "flip: C8 flipped FAIL->PASS; C16 did not")
new_line = [ln for ln in board.splitlines() if "Newly-surfaced" in ln]
new_body = board.splitlines()[board.splitlines().index(new_line[0]) + 1]
check("C5" in new_body and "C16" not in new_body, "new FAIL: C5 is new; C16 is a carried residual, not new")
# no letter grade anywhere (guardrail)
check(not any(g in board for g in ("Grade:", "grade A", " A (", "/100")), "guardrail: no A-F letter grade / 100-pt total")

# --- one-report mode: scoreboard only, no delta ---
solo = score.scoreboard(va, None)
check("pass-rate" in solo and "Flipped" not in solo, "one-report mode: scoreboard, no delta block")

# --- REGRESSION (claude-skeptic R3): the report shape SKILL.md MANDATES is an Assessment
#     TABLE. parse() must read '| Crit | VERDICT | note |' rows, or a report written to the
#     documented format scores every FAIL as zero — inverting the 'never hide a fatal C0'
#     guardrail. Fixture is verbatim the SKILL.md '## Report format' block. ---
SKILL_FORMAT = """# Review — target
axes: host codex
## Summary
1 FAIL; C8 is load-bearing.
pass-rate 50%
## Assessment
| Criterion | Verdict | Note                              |
|-----------|---------|-----------------------------------|
| C0        | PASS    | loads; name == folder             |
| C8        | FAIL    | baked date at L12                 |
| O2        | N-A     | API-only, not this CLI prompt     |
## Fixes  (one per FAIL — positive form, each with why it helps)
- **C8** — L12 "spike-verified 2026" — Fix: delete the date. *Why this helps:* stops going stale.
"""
vt = score.parse(SKILL_FORMAT)
check(vt.get("C0") == "PASS", "table: C0 -> PASS")
check(vt.get("C8") == "FAIL", "table: C8 -> FAIL")
check(vt.get("O2") == "N-A", "table: O2 -> N-A")
pt, ft, appt = score.tally(vt)
check((pt, ft, appt) == (1, 1, 2), f"table tally = (PASS 1, FAIL 1, app 2), got {(pt, ft, appt)}")
# the exact guardrail the skeptic flagged: a fatal FAIL in the table must NOT vanish to zero.
board_t = score.scoreboard(vt, None)
check("C8" in board_t.split("Scoreboard")[0], "table: residual-FAIL section names C8 (not hidden as a 0-finding pass)")
# header row + separator row must NOT be mis-parsed as criteria
check("Criterion" not in "".join(vt.keys()) and len(vt) == 3, f"table: only 3 real verdicts parsed, got {vt}")

# --- REGRESSION (R5 claude-logic/skeptic): the AA (AI-authorship) family must score too. It
#     is the 'increasingly default' target class; before this both parse paths dropped AA,
#     so an AA-only FAIL scored 0 FAIL / 100% — the same guardrail inversion as the R3 bug. ---
AA_REPORT = """# Review — ai-authored target
## Assessment
| AA4 | FAIL | confabulated CLI flag |
| AA6 | FAIL | Korean in an English body |
| C1  | PASS | trigger ok |
## Fixes  (one per FAIL)
- **AA4** — invented flag — Fix: drop it.
"""
vaa = score.parse(AA_REPORT)
check(vaa.get("AA4") == "FAIL", "AA4 table row -> FAIL")
check(vaa.get("AA6") == "FAIL", "AA6 table row -> FAIL")
paa, faa, appaa = score.tally(vaa)
check((paa, faa) == (1, 2), f"AA tally counts the AA FAILs: PASS 1 FAIL 2, got {(paa, faa)}")
board_aa = score.scoreboard(vaa, None)
head_aa = board_aa.split("Scoreboard")[0]
check("AA4" in head_aa and "AA6" in head_aa, "AA FAILs are named in the Residual-FAIL block (guardrail holds for AI-authored targets)")
# findings-line path too ('- [FAIL] AA2 ...')
aa_find = score.parse("## Findings\n- [FAIL] AA2 chat-register padding — cut it\n## Passed\nC1\n")
check(aa_find.get("AA2") == "FAIL", "AA2 findings-line -> FAIL")

# --- REGRESSION (R6 claude-logic): host==worker can give ONE criterion a PASS on one axis
#     and a FAIL on the other. FAIL must WIN, or last-write-wins erases the FAIL and the
#     residual-FAIL block hides it — the same guardrail inversion class as R3/R5. ---
vc = score.parse("## Assessment\n| A4 | PASS | host: effort fine |\n| A4 | FAIL | worker: pins max |\n| C1 | PASS | ok |\n")
check(vc.get("A4") == "FAIL", "FAIL-wins: A4 PASS then FAIL -> FAIL (not overwritten)")
vc2 = score.parse("## Assessment\n| A4 | FAIL | worker |\n| A4 | PASS | host |\n")
check(vc2.get("A4") == "FAIL", "FAIL-wins: A4 FAIL then PASS -> stays FAIL")
check("A4" in score.scoreboard(vc, None).split("Scoreboard")[0], "FAIL-wins: A4 named in the Residual-FAIL block")

# --- REGRESSION (R8 codex-consist): a host==worker report tags rows [host]/[worker]; a tag
#     appended to the criterion CELL must not drop the row from the score. ---
vtag = score.parse("## Assessment\n| A4 [host] | PASS | ok |\n| A4 [worker] | FAIL | pins max |\n")
check(vtag.get("A4") == "FAIL", "tagged cell '| A4 [worker] | FAIL |' parses (FAIL-wins), not dropped")
check(score.parse("| C8 [host] | FAIL | x |\n").get("C8") == "FAIL", "single tagged cell parses")

if FAILS:
    print(f"RED — {len(FAILS)} failing:")
    for m in FAILS:
        print("  FAIL:", m)
    sys.exit(1)
print("GREEN — score.py deterministic delta tests pass.")
sys.exit(0)
