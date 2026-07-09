# OpenAI criteria

Apply these when the target is a prompt written for an OpenAI model — a codex worker
prompt or a direct-API call — in addition to `common.md`. (A codex-*host* skill's file
structure is governed by the common criteria, not these; O5 covers how a codex-host
skill documents its tools.) Sources: OpenAI's prompt-guidance and reasoning
best-practices documentation.

When the target is a CLI worker/dispatch prompt (codex invoked through a CLI, not a
direct API call), O1 (reasoning effort) and O2's API parts (verbosity, Structured
Outputs) are set by the CLI flag or config, not the prompt text — mark those N-A, as G1
does for the sampler. O2's prompt-level check still applies: judge whether the prompt
states its output shape (a CLI worker has no Structured Outputs API, so the shape lives
in the text).

## Contents
- O1 Reasoning effort is a lever, not a dial to max
- O2 Verbosity and output shape
- O3 Reasoning-model prompt shape
- O4 Outcome-first, not step-by-step
- O5 Tool definitions: API surface vs skill text
- O6 The current flagship tier — check the capability, not the version

## O1 — Reasoning effort is a lever, not a dial to max  [judge]
A prompt should set reasoning effort deliberately, and the default on the current
model is the balanced middle — higher effort is not automatically better and can
cause overthinking or unnecessary searching. Flag prompts that always reach for the
top setting, or that never consider a lower one for latency-sensitive work.

## O2 — Verbosity and output shape  [judge]
When output length matters, control it explicitly with the verbosity control plus an
explicit output shape, and keep that separate from reasoning effort (a longer answer is
not more reasoning). Remove
output-schema definitions from the prompt and use Structured Outputs instead. Do not
bake a stale "today is …" date into the prompt — the model knows the current date; a
date the running app must pass at call time (a business timezone, a policy-effective
date, the user's local date) is legitimate.

## O3 — Reasoning-model prompt shape  [judge]
For reasoning models: keep prompts simple and direct; do not ask for chain-of-thought
("think step by step" is unnecessary and can hurt); use delimiters; try zero-shot
first and add examples only if needed; place instructions at the right hierarchy level (developer messages for application
steering, system messages for stable top-level policy and role); include only the most relevant context (dumping everything degrades
reasoning). If the model suppresses markdown and you need it, the developer message
opts back in on its first line.

## O4 — Outcome-first, not step-by-step  [judge]
Describe the target outcome, success criteria, allowed side effects, evidence rules,
and output shape; leave the path to the model unless the exact path matters.
Contradictory or vague instructions are especially damaging here — the model spends
reasoning tokens reconciling them. For agentic work, persistence framing ("keep going
until resolved") and tool preambles are deliberate levers; scope discipline
("implement exactly what is asked") counters the model's tendency to add unrequested
work.

## O5 — Tool definitions: API surface vs skill text  [judge]
When the target calls OpenAI's API directly, define tools through the API `tools`
field with clear names and a one- or two-sentence description of what each does and
when to use it — not a schema pasted into the prompt; for recurring tool loops,
handoffs, guardrails, and tracing, prefer the Agents SDK over hand-rolled
orchestration. When the target is a codex-host skill, tool behavior documented in the
skill text is expected — apply C12 (clear names, small curated set), not the
API-field rule.

## O6 — The current flagship tier — check the capability, not the version  [judge]
OpenAI's current flagship tier can add a top/`max` reasoning effort, a subagent-backed
"ultra" mode, and explicit prompt-cache breakpoints. Review by capability, not by
release name: if the target uses a max-effort setting, a subagent mode, or explicit
cache breakpoints, apply the current flagship's guidance (O1–O5) and put stable
content first so a breakpoint lands on it. Do not pin a version number or codename in
the prompt (C8) — name the capability. Where a capability has no published guidance
yet, the current flagship's doctrine is the operative one; do not invent rules that
are not in an official source.
