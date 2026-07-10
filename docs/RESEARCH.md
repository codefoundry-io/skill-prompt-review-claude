# Research references

The criteria in `skills/skill-prompt-review/references/` are distilled from the
first-party prompt-engineering guidance published by the three model vendors, and were
verified against those primary sources rather than second-hand summaries. This document
lists what each reference draws on.

## Why this skill exists at all

Source code has a deterministic oracle: a test passes or it fails. Prompt and skill text
has none — the linter here can flag mechanical candidates (a baked date, a pinned model
name, a chat-register phrase) but it cannot tell you whether the *instructions are
correct*. The strongest correctness signal available, short of a human who knows the
ground truth, is an **adversarial fresh-eye review across model families**: each reviewer
told to assume a defect is present and to enumerate what it checked, so a bare "looks
fine" cannot pass and different families catch different misses. This skill is the
checklist and the method for running that review.

## Sources

### Anthropic (`references/anthropic.md`, criteria A1-A7)
- Agent Skills authoring best practices and the Agent Skills specification (skill
  structure, `name`/`description` as the trigger signal, the reserved-word and
  name-to-directory rules, progressive disclosure).
- Claude prompt-engineering guidance (being clear and direct, positive framing, ordering
  long context, letting a capable model reason rather than over-scaffolding).
- Per-model prompting and extended-thinking guidance (effort as the primary lever; not
  hand-managing thinking budgets a current model rejects).

### OpenAI (`references/openai.md`, criteria O1-O6)
- Reasoning-model prompting guidance (reasoning effort, verbosity, the
  developer-vs-system message hierarchy per surface, outcome-first prompts, tool
  documentation, the exact markdown opt-in phrase for reasoning models).
- Structured Outputs guidance (API-level; a CLI prompt states its shape in text unless
  the invocation supplies a schema).
- The no-pinned-model-name discipline for prompt prose (capability, never a dated model
  ID — while exact IDs remain correct in config/router contexts).

### Google (`references/google.md`, criteria G1-G6)
- Gemini prompting strategies (constraint placement at the end of long context, default
  brevity, avoiding blanket epistemic negatives that degrade the model).
- Thinking / thinking-level guidance (dynamic thinking up to a level ceiling; the
  generation-specific thinking controls must not be mixed in one request).
- Function-calling guidance (descriptive function and parameter names, a small curated
  tool set, grounding and code execution over trusting the model to compute).

### AI-authorship (`references/ai-authorship.md`, criteria AA1-AA6)
- The published prompt-hygiene literature on AI-generated-prompt slop, sycophancy,
  over-formatting, and controlling text that adds variance.
- Reviewed AI-authored prompts and skills: every AA item is a defect class an AI author
  actually committed and an independent review caught — authoring-conversation carryover,
  chat-register padding, sycophantic softeners, confabulated specifics, decoration
  overload, and language drift.

## Criteria -> source at a glance

| Criteria | Source |
|---|---|
| C0-C16 (`common.md`) | shared shape across all three vendors' guidance |
| A1-A7 (`anthropic.md`) | Anthropic Agent Skills spec + Claude prompting docs |
| O1-O6 (`openai.md`) | OpenAI reasoning-model prompting docs |
| G1-G6 (`google.md`) | Google Gemini prompting / thinking / function-calling docs |
| AA1-AA6 (`ai-authorship.md`) | prompt-hygiene literature + review-caught AI-author defects |

## A standing caution

Vendor guidance changes. Model names, reasoning-tier names, and default behaviors move;
the criteria that pin to a moving target (a reasoning control, a thinking-level name)
carry a note to re-verify against the live first-party page before quoting them. When
this skill's own advice and a current vendor page disagree, the live page wins.
