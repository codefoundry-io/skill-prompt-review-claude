# skill-prompt-review (Claude Code edition)

**A prompt or a skill has no unit tests — so there is no automatic signal when one is
wrong.** AI-authored prompts fail in a characteristic way: they carry the authoring
conversation's framing into the artifact, bake in dates and one-off specifics, state
plausible flags that do not exist, and pile on decoration the reader never needs — and the
author, re-reading its own text, cannot see any of it. `skill-prompt-review` is the missing
check. It reads a `SKILL.md` or a prompt, compares it against a checklist distilled from
Anthropic, OpenAI, and Google's own prompt-engineering guidance (see
[docs/RESEARCH.md](docs/RESEARCH.md)), and returns a per-criterion PASS / FAIL / N-A report
with evidence and a concrete fix.

It runs on Claude Code: you give it a target and it reviews the text. It does **not** run the
target, and a clean pass is not a security clearance.

## Why a *fresh eye*

The one rule that makes this work: **never review your own draft.** An author reads their
own intent into the gaps. Hand the review to a separate fresh-eye sub-agent (an `Agent`, not your own session) — a reader that did not write
the target. For anything you will ship, fan the review out across model families (a
Claude-family, an OpenAI-family, and a Google-family reviewer) and consolidate: a FAIL
from any one family stands, because different families catch different misses. A single
fresh-eye reviewer is the floor.

## Install

### As a plugin (recommended)

This repo is a single-plugin Claude Code marketplace:

```
/plugin marketplace add <github-owner>/<this-repo>     # or a local path to this repo
/plugin install skill-prompt-review@skill-prompt-review
```

### As a personal or project skill

Copy the skill directory to a location Claude Code scans:

```bash
cp -r skills/skill-prompt-review ~/.claude/skills/            # personal (all projects)
cp -r skills/skill-prompt-review <your-repo>/.claude/skills/  # project (shared via git)
```

After install, in a normal turn, ask the assistant to review a skill or prompt — e.g.
*"Run skill-prompt-review on `path/to/SKILL.md`."* It loads the criteria from
`references/`, runs the deterministic linter, and reports.

## What it checks

- **`references/common.md`** — C0-C16, the criteria that hold for any skill or prompt
  (frontmatter loads, description says what AND when, one job, isolation, no priming,
  lean, calm imperatives, no over-scaffolding, no time-stamped facts, progressive
  disclosure, positive framing, distribution hygiene, tool/skill universals, gate
  irreversible actions, order long context, no self-contradiction, invocation
  construction).
- **`references/anthropic.md` / `openai.md` / `google.md`** — the vendor-specific
  criteria for a prompt written for a Claude / OpenAI / Gemini model, each preamble
  stating which criteria are structure, body-as-prompt, or N-A per target kind.
- **`references/ai-authorship.md`** — AA1-AA6, the chat-register signature to check when
  the target may have been written BY an AI (increasingly the default): authoring-
  conversation carryover, chat-register padding, sycophantic softeners, confabulated
  specifics, decoration overload, and language drift.
- **`scripts/lint.py`** — a deterministic linter that flags the *mechanical* candidates
  (baked dates and bare-year anchors, pinned models/versions and release-aging words,
  density, length, chat-register phrases — with quoted/backticked examples recognized as
  scoping language, not violations). A candidate list, never a verdict; the [judge]
  criteria still need a fresh-eye reviewer.
- **`scripts/score.py`** — a deterministic scoreboard and round-over-round delta over the
  report's verdicts (no model call, no invented numbers): applicable / PASS / FAIL tally,
  pass-rate, criteria that flipped, residual FAILs always printed above the rate.

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
5. **Adjudicate contradictions by evidence.** When two families disagree, decide with a
   probe or the vendor's own current documentation (trace the shell parse, grep the
   source, read the official page) — not by vote and not by the author's confidence.
6. **Prove it BEHAVES before you ship.** A clean text review is necessary but not
   sufficient. Plant known defects in a test target so you have a ground-truth oracle,
   and confirm the skill catches them and stays quiet on a clean control.
   `scripts/test_lint.py`, `scripts/test_score.py`, and `tests/test_lint_fixtures.py`
   are that check for the deterministic half.

## Report format

```
# Review — <path or prompt label>
axes: <host / worker / model / AI-authored?, as applicable>
## Summary
<N FAIL; name the load-bearing one.>
pass-rate <p%>   (always printed BELOW the named FAIL)
## Assessment
| Criterion | Verdict | Note                          |
|-----------|---------|-------------------------------|
| C0        | PASS    | loads; name == folder         |
| C8        | FAIL    | baked date at L12             |
| O2        | N-A     | API-only, not this CLI prompt |
## Fixes  (one per FAIL — positive form, each with why it helps)
## Recommended additions
```

On a re-review round, `scripts/score.py '<before>' '<after>'` appends the deterministic
delta: criteria that flipped, residual FAILs, newly-surfaced FAILs, before/after counts.
No letter grade, no per-criterion invented number, no cross-family averaging.

## Scope & limits

- **English targets.** The criteria and the linter presuppose English text; work from an
  English translation for every criterion EXCEPT C11 and AI-authorship AA6 — those check
  language distribution, so judge them against the original.
- **It reads, it does not run.** No malware scan of bundled `scripts/`; a clean pass is
  not a security clearance.
- **Adversarial review has a noise floor.** Even on clean input a thorough reviewer will
  surface *something*; consolidate across families and adjudicate by probe or official
  documentation rather than chasing every note to zero. Stop at the plateau — when a
  verdict flip-flops, a resolved finding returns, or a reviewer reports something not in
  the text.

## Verify the install

```bash
python3 skills/skill-prompt-review/scripts/test_lint.py    # linter self-test
python3 skills/skill-prompt-review/scripts/test_score.py   # scoreboard/delta self-test
python3 tests/test_lint_fixtures.py                        # planted-defect functional test
```

All three print GREEN when the deterministic half catches every planted defect and stays
clean on the control.

## License

MIT — see [LICENSE](LICENSE).
