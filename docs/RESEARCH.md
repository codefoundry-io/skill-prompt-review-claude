# Research references

The criteria in `skills/skill-prompt-review/references/` are distilled from the
first-party prompt-engineering guidance published by the three model vendors, and were
verified against those primary sources rather than second-hand summaries. This document
lists what each reference draws on.

## Why this skill exists at all

Source code has a deterministic oracle: a test passes or it fails. Prompt and skill text
has none — the linter here can flag mechanical candidates (a baked date, a pinned model
name, a run-on description) but it cannot tell you whether the *instructions are correct*.
The strongest correctness signal available, short of a human who knows the ground truth,
is an **adversarial fresh-eye review across model families**: each reviewer told to assume
a defect is present and to enumerate what it checked, so a bare "looks fine" cannot pass
and different families catch different misses. This skill is the checklist and the method
for running that review.

## Sources

### Anthropic (`references/anthropic.md`, criteria A1-A7)
- Agent Skills authoring best practices (skill structure, `name`/`description` as the
  trigger signal, progressive disclosure).
- Claude prompt-engineering guidance (being clear and direct, positive framing, ordering
  long context, letting a capable model reason rather than over-scaffolding).
- Per-model prompting and extended-thinking guidance (reasoning-effort control; not
  hand-writing chain-of-thought a modern model produces itself).

### OpenAI (`references/openai.md`, criteria O1-O6)
- GPT-5 / reasoning-model prompting guidance (reasoning effort, verbosity, the
  developer-vs-system message hierarchy, outcome-first prompts, tool documentation).
- Structured Outputs guidance (API-level; N-A to a prompt a CLI loads).
- The no-pinned-model-name discipline (capability/alias, never a dated model ID).

### Google (`references/google.md`, criteria G1-G6)
- Gemini prompting strategies (constraint placement at the end of long context, default
  brevity, avoiding blanket epistemic negatives that degrade the model).
- Thinking / thinking-level guidance (a ceiling, not a target; prefer the level control
  over a hand-set budget).
- Function-calling guidance (descriptive parameter names, a small curated tool set,
  grounding and code execution over trusting the model to compute).

## Criteria -> source at a glance

| Criteria | Source |
|---|---|
| C0-C16 (`common.md`) | shared shape across all three vendors' guidance |
| A1-A7 (`anthropic.md`) | Anthropic Agent Skills + Claude prompting docs |
| O1-O6 (`openai.md`) | OpenAI GPT-5 / reasoning prompting docs |
| G1-G6 (`google.md`) | Google Gemini prompting / thinking / function-calling docs |

## A standing caution

Vendor guidance changes. Model names, reasoning-tier names, and default behaviors move;
the criteria that pin to a moving target (a reasoning flag, a thinking-level name) carry a
note to re-verify against the live first-party page before quoting them. When this skill's
own advice and a current vendor page disagree, the live page wins.
