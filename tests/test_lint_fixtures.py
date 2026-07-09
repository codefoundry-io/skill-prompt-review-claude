#!/usr/bin/env python3
"""DETERMINISTIC functional test — skill-prompt-review's mechanical core (scripts/lint.py).

Ground-truth oracle: each fixture is a realistic mini target with ONE planted mechanical
defect mapped to a specific criterion; the test asserts lint.py surfaces that criterion,
and that a clean control raises none. This is the deterministic half of "prove the skill
BEHAVES" — the [judge]-only criteria (C15/C16/C4/C1/C2) are tested separately by AI legs
with deterministic scoring, because they cannot be made deterministic.

Exit 0 = every planted defect caught + control clean; 1 = a miss or a false positive.
Python 3.12 stdlib only.
"""
from __future__ import annotations
import subprocess
import sys
import tempfile
from pathlib import Path

LINT = Path(__file__).resolve().parent.parent / "skills" / "skill-prompt-review" / "scripts" / "lint.py"

FM = "---\nname: {name}\ndescription: {desc}\n---\n\n# {name}\n\n{body}\n"
GOOD_DESC = "Use when you need the widget dispatched; triggers when the leader is about to run it."

# Each fixture: (dirname, filename, text, expected-criterion-substring in lint output,
#               should_flag)  — should_flag False = clean control (expect the criterion absent)
def fixtures() -> list[tuple[str, str, str, str, bool]]:
    filler = "\n".join(f"operational line {i} describing what to do." for i in range(20))
    long_body = "\n".join(f"line {i}" for i in range(230))
    dense_neg = "\n".join(
        ["Do not run it.", "Do not skip.", "Never inline.", "Do not guess.", "Never assume."]
        + [f"pad line {i}" for i in range(25)]
    )
    dense_caps = "\n".join(
        ["You MUST do this.", "This is MANDATORY.", "NEVER skip it.", "It is REQUIRED.",
         "Do it NOW.", "This is CRITICAL."] + [f"pad line {i}" for i in range(25)]
    )
    excuses = ("Always surface it. \"I have other work\", \"the call already failed\", "
               "\"looks like a one-off\" are never valid reasons to skip.\n" + filler)
    return [
        ("f_c8date", "SKILL.md",
         FM.format(name="f_c8date", desc=GOOD_DESC, body="The check was spike-verified 2026-05-01 on the rig.\n" + filler),
         "C8 time", True),
        ("f_c8pin", "SKILL.md",
         FM.format(name="f_c8pin", desc=GOOD_DESC, body="Route the prompt to Claude Fable 5 for this step.\n" + filler),
         "C8", True),
        ("f_c0name", "SKILL.md",
         FM.format(name="wrong-slug", desc=GOOD_DESC, body="Body content here.\n" + filler),
         "C0", True),
        ("f_c11ko", "SKILL.md",
         FM.format(name="f_c11ko", desc='Use when 위젯을 한 번 불러줘 or 위젯으로 X 처리 is asked; and when to run it.',
                   body="Body content.\n" + filler),
         "C11", True),
        ("f_c9len", "SKILL.md",
         FM.format(name="f_c9len", desc=GOOD_DESC, body=long_body),
         "C9 body length", True),
        ("f_c10neg", "SKILL.md",
         FM.format(name="f_c10neg", desc=GOOD_DESC, body=dense_neg),
         "C10", True),
        ("f_c6caps", "SKILL.md",
         FM.format(name="f_c6caps", desc=GOOD_DESC, body=dense_caps),
         "C6", True),
        ("f_c4excuse", "SKILL.md",
         FM.format(name="f_c4excuse", desc=GOOD_DESC, body=excuses),
         "C4", True),
        # clean control — a well-formed short skill; the criteria above must NOT fire
        ("f_clean", "SKILL.md",
         FM.format(name="f_clean", desc=GOOD_DESC, body="State the wanted action once, with a one-line reason.\n" + filler),
         None, False),
    ]


def lint_output(path: Path) -> str:
    r = subprocess.run([sys.executable, str(LINT), str(path)], capture_output=True, text=True, timeout=60)
    return r.stdout + r.stderr


def main() -> int:
    fails: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        for dirname, fname, text, crit, should in fixtures():
            p = Path(td) / dirname / fname
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            out = lint_output(p)
            if should:
                ok = crit in out
                print(f"  {dirname:14s} expect {crit!r:20s} -> {'CAUGHT' if ok else 'MISSED'}")
                if not ok:
                    fails.append(f"[{dirname}] planted {crit!r} NOT flagged. lint said:\n    " + out.strip().replace('\n', '\n    '))
            else:
                # control: none of the flaggable criteria should appear
                bad = [c for c in ("C8", "C0", "C11", "C9 body", "C10", "C6", "C4") if c in out]
                print(f"  {dirname:14s} control              -> {'CLEAN' if not bad else 'FALSE-POS ' + str(bad)}")
                if bad:
                    fails.append(f"[{dirname}] control false-positives: {bad}. lint said:\n    " + out.strip().replace('\n', '\n    '))
    if fails:
        print("\nFAILURES:")
        for f in fails:
            print("  " + f)
        return 1
    print("\nGREEN — lint.py caught every planted mechanical defect and stayed clean on the control.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
