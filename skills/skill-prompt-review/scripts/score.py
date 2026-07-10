#!/usr/bin/env python3
"""Deterministic scoreboard + round-over-round delta for a skill-prompt-review pass.

There is NO model call here and NO per-criterion numeric score — a prompt has no oracle
for the [judge] criteria, so PASS / FAIL / N-A stays the atomic verdict. This tool only
makes the EXISTING verdicts countable: it parses one or two review reports (in this
skill's report format) and prints deterministic aggregates + the delta.

    score.py <after.md>                 # one report -> scoreboard only
    score.py <before.md> <after.md>     # two reports -> scoreboard + DELTA block

Aggregates (all arithmetic, all deterministic):
  - applicable = PASS + FAIL  (N-A excluded from the denominator)
  - pass-rate  = PASS / applicable
  - flips FAIL->PASS, residual FAILs, newly-surfaced FAILs, before->after counts

Guardrails baked in: every residual FAIL is listed ABOVE the pass-rate (a 94% never hides a
fatal C0); the list is in criterion order — with no severity signal, score.py does not rank
by load-bearing-ness (a deterministic tool must not launder that judgment; the report
author names the load-bearing FAIL in the `## Summary`). NO letter grade; verdicts are never
averaged across reports/families (a FAIL is a FAIL). Python 3.12, stdlib only.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

# Every criterion family the report format can carry: C0-C16, A1-A7, O1-O6, G1-G6, AND the
# AA1-AA6 AI-authorship family. AA must be listed BEFORE the single-letter class in the
# alternation, and matched without a leading \b — "AA4" has no word boundary before its
# inner "A4", so a bare [CAOG]\d pattern silently drops the whole AA family (an AA-only FAIL
# would then score as 0 FAIL / 100%, inverting the guardrail — the R5 regression).
CRIT = re.compile(r"\b(AA\d{1,2}|[CAOG]\d{1,2})\b")
CRIT_CELL = re.compile(r"AA\d{1,2}|[CAOG]\d{1,2}")   # a table cell that is ONLY a criterion token
VERDICT_CELL = re.compile(r"(?i)^(PASS|FAIL|N-?/?A)$")


def _set(verdict: dict[str, str], crit: str, v: str) -> None:
    """FAIL-wins: a FAIL on any row/axis sticks and is never overwritten by a later PASS/N-A
    for the same criterion. host==worker can legitimately produce a PASS on one axis and a
    FAIL on the other for one criterion; last-write-wins would erase the FAIL and hide it
    from the residual-FAIL block. FAIL-wins keeps the guardrail intact."""
    if verdict.get(crit) == "FAIL":
        return
    if v == "FAIL" or crit not in verdict:
        verdict[crit] = v


def parse(report: str) -> dict[str, str]:
    """Report text -> {criterion: 'PASS'|'FAIL'|'N-A'}. Reads TWO shapes, so a report in
    the documented '## Assessment' TABLE format scores correctly (the primary deliverable):
    a table row '| C8 | FAIL | note |', and the alternate '- [FAIL] C8 …' finding lines +
    a '## Passed' list. Later mentions do not override a verdict already set (findings and
    table rows are authoritative). Later PASS/N-A mentions do not override an existing
    verdict; a FAIL always wins (see _set)."""
    verdict: dict[str, str] = {}
    in_passed = False
    for line in report.splitlines():
        s = line.strip()
        low = s.lower()
        # an Assessment table row: "| C8 | FAIL | note |" (the report format SKILL.md mandates).
        # The header ("| Criterion | Verdict |") and separator ("|---|---|") rows fail the
        # criterion/verdict cell match and are skipped.
        if s.startswith("|"):
            cells = [c.strip().strip("`*") for c in s.strip("|").split("|")]
            if len(cells) >= 2:
                # tolerate an optional [host]/[worker] axis tag on the criterion cell, so a
                # host==worker report ("| A4 [worker] | FAIL |") is scored, not dropped.
                crit = re.sub(r"\s*\[(?:host|worker)\]\s*$", "", cells[0], flags=re.I).strip()
                if CRIT_CELL.fullmatch(crit) and VERDICT_CELL.match(cells[1]):
                    v = cells[1].upper().replace("/", "-")
                    _set(verdict, crit, "N-A" if v.startswith("N") else v)
            continue
        # a findings line: "- [FAIL] C8 — …" / "- [N-A] O2 — …"
        m = re.match(r"-?\s*\[(FAIL|N-?A)\]\s*(.*)", s, re.I)
        if m:
            tag = "FAIL" if m.group(1).upper() == "FAIL" else "N-A"
            c = CRIT.search(m.group(2))
            if c:
                _set(verdict, c.group(1), tag)
            continue
        # the "## Passed" section — collect every criterion token until the next header
        if low.startswith("## passed") or low.startswith("passed:"):
            in_passed = True
            for c in CRIT.findall(s):
                _set(verdict, c, "PASS")
            continue
        if in_passed:
            if s.startswith("#"):
                in_passed = False
            else:
                for c in CRIT.findall(s):
                    _set(verdict, c, "PASS")
    return verdict


def tally(v: dict[str, str]) -> tuple[int, int, int]:
    p = sum(1 for x in v.values() if x == "PASS")
    f = sum(1 for x in v.values() if x == "FAIL")
    return p, f, p + f  # PASS, FAIL, applicable


def rate(p: int, app: int) -> str:
    return f"{100 * p // app if app else 0}%"


def scoreboard(after: dict[str, str], before: dict[str, str] | None) -> str:
    pa, fa, appa = tally(after)
    fails_a = sorted(c for c, x in after.items() if x == "FAIL")
    out: list[str] = []
    # Guardrail: every residual FAIL is listed above the pass-rate so none is hidden.
    out.append("## Residual FAIL (every FAIL, criterion order — all above the pass-rate so none is hidden)")
    out.append("  " + (", ".join(fails_a) if fails_a else "(none)"))
    out.append("")
    out.append("## Scoreboard  (verdicts, not a quality score; N-A excluded)")
    if before is not None:
        pb, fb, appb = tally(before)
        out.append(f"{'':12s}{'BEFORE':>8s}{'AFTER':>8s}")
        out.append(f"{'applicable':12s}{appb:>8d}{appa:>8d}")
        out.append(f"{'PASS':12s}{pb:>8d}{pa:>8d}")
        out.append(f"{'FAIL':12s}{fb:>8d}{fa:>8d}")
        out.append(f"{'pass-rate':12s}{rate(pb, appb):>8s}{rate(pa, appa):>8s}")
        # DELTA
        flips = sorted(c for c in after if before.get(c) == "FAIL" and after[c] == "PASS")
        newf = sorted(c for c, x in after.items() if x == "FAIL" and before.get(c) != "FAIL")
        out.append("")
        out.append("## Flipped FAIL -> PASS")
        out.append("  " + (", ".join(flips) if flips else "(none)"))
        out.append("## Newly-surfaced FAIL (a subtler finding this round is normal — not a regression per se)")
        out.append("  " + (", ".join(newf) if newf else "(none)"))
    else:
        out.append(f"applicable {appa}   PASS {pa}   FAIL {fa}   pass-rate {rate(pa, appa)}")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if not argv or len(argv) > 2:
        print(__doc__.strip().splitlines()[0])
        print("usage: score.py <after.md> | score.py <before.md> <after.md>")
        return 2
    if len(argv) == 1:
        after = parse(Path(argv[0]).read_text(encoding="utf-8"))
        print(scoreboard(after, None))
    else:
        before = parse(Path(argv[0]).read_text(encoding="utf-8"))
        after = parse(Path(argv[1]).read_text(encoding="utf-8"))
        print(scoreboard(after, before))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
