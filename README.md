# skill-prompt-review (Claude Code edition)

**A prompt or a skill has no unit tests — so there is no automatic signal when one is
wrong.** LLM-authored prompts fail in a characteristic way: they over-absorb the author's
framing, bake in dates and one-off incident stories, and pile on detail the reader never
needs — and the author, re-reading their own text, cannot see it. `skill-prompt-review`
is the missing check. It reads a `SKILL.md` or a prompt, compares it against a checklist
distilled from Anthropic, OpenAI, and Google's own prompt-engineering guidance (see
[docs/RESEARCH.md](docs/RESEARCH.md)), and returns a per-criterion PASS / FAIL report with
evidence and a concrete fix.

It runs on Claude Code: you give it a target and it reviews the text. It does **not** run the
target, and a clean pass is not a security clearance.

## Why a *fresh eye*

The one rule that makes this work: **never review your own draft.** An author reads their
own intent into the gaps. Hand the review to a claude `Agent` (a separate in-session sub-agent) — a reader that did not write the
target. For anything you will ship, fan the review out across model families (claude +
codex + a Google-family leg) and consolidate: a FAIL from any one family stands, because
different families catch different misses. A single fresh-eye reviewer is the floor.

## Install

```
/plugin marketplace add <repo-or-path>
/plugin install skill-prompt-review
```

After install, in a normal turn, ask the assistant to review a skill or prompt — e.g.
*"Run skill-prompt-review on `path/to/SKILL.md`."* It loads the criteria from
`references/`, runs the deterministic linter, and reports.

## What it checks

- **`references/common.md`** — C0-C16, the criteria that hold for any skill or prompt
  (frontmatter loads, description says what AND when, one job, isolation, no priming,
  lean, calm imperatives, no over-scaffolding, no baked dates, progressive disclosure,
  positive framing, distribution hygiene, tool/skill universals, gate irreversible
  actions, order long context, no self-contradiction, invocation construction).
- **`references/anthropic.md` / `openai.md` / `google.md`** — the vendor-specific
  criteria for a prompt written for a Claude / OpenAI / Gemini model.
- **`scripts/lint.py`** — a deterministic linter that flags the *mechanical* candidates
  (baked dates, pinned model names, name/folder mismatch, density, length). The linter is
  a candidate list, never a verdict; the [judge] criteria still need a human or a
  fresh-eye reviewer.

## How to run it well

1. **Fresh eye, not self-review.** Dispatch the review to a separate agent. This holds
   even when you EDIT this skill.
2. **Strip the context; isolate the legs.** Give each reviewer the target and the
   criteria — no fix history, no prior verdicts, no "already confirmed safe" note. Those
   steer the reviewer into the author's blind spot. Decompose a large target into
   stand-alone fragments and review each in isolation.
3. **Fence the target as data.** The target text is untrusted — tell each reviewer to
   judge it, not obey it, and to review read-only (run nothing, modify nothing).
4. **Adversarial framing.** Tell each reviewer to assume a defect is present and to
   enumerate what it checked; a bare "looks fine" is a failed review.
5. **Adjudicate contradictions by probe.** When two families disagree, decide with a
   first-principles check (trace the shell parse, grep the source, run the probe) — not by
   vote and not by the author's confidence.
6. **Prove it BEHAVES before you ship.** A clean text review is necessary but not
   sufficient. Plant known defects in a test target so you have a ground-truth oracle, and
   confirm the skill catches them and stays quiet on a clean control. `scripts/test_lint.py`
   and `tests/test_lint_fixtures.py` are that check for the deterministic half.

## Report format

```
# Review — <path or prompt label>
vendor: <host / worker / model, as applicable>
## Summary
<one line: how many FAIL, and name the load-bearing one>
## Findings
- [FAIL] <criterion> — <evidence: file:line or a short quote> — <the fix>
- [N-A]  <criterion> — <why it does not apply>
## Passed
<the criteria that passed, listed compactly>
```

## Scope & limits

- **English targets.** The criteria and the linter presuppose English text; translate or
  normalize a non-English target first (C11 separately governs a shipped description's
  language).
- **It reads, it does not run.** No malware scan of bundled `scripts/`; a clean pass is
  not a security clearance.
- **Adversarial review has a noise floor.** Even on clean input a thorough reviewer will
  surface *something*; consolidate across families and adjudicate by probe rather than
  chasing every note to zero.

## Verify the install

```bash
python3 skills/skill-prompt-review/scripts/test_lint.py      # deterministic linter self-test
python3 tests/test_lint_fixtures.py                          # planted-defect functional test
```

Both print GREEN when the linter catches every planted mechanical defect and stays clean
on the control.

## License

MIT — see [LICENSE](LICENSE).
