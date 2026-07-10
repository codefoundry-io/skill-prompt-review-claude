# OpenAI criteria

Apply these when the target is a prompt an OpenAI model reads — a codex worker prompt, a
direct-API call, or a codex-*host* SKILL body (codex reads the body as a prompt) — in
addition to `common.md`. A codex-host skill's file STRUCTURE is governed by the common
criteria, not these (O5 covers how it documents its tools); but the O prompt-text criteria
(O2 output shape, O3 reasoning-shape, O4 outcome-first) DO apply to its body, with the
API/config subparts of O1/O2 N-A for that non-API target (see the next paragraph). Sources:
OpenAI's prompt-guidance and reasoning best-practices documentation.

When the target is a CLI worker/dispatch prompt (codex invoked through a CLI, not a
direct API call), the CONFIG aspect of O1 (reasoning effort) and O2 (verbosity, Structured
Outputs) is set by the CLI flag or config, not the prompt text — mark those subparts N-A,
as G1 does for the sampler. Both keep a live PROMPT-TEXT check: O1 FAILs if the prompt
forces a mode, max effort, or hidden reasoning; O2 judges whether the prompt states its
output shape — a CLI worker has no Structured Outputs API, though `codex exec` accepts an
`--output-schema` file, so absent that flag the shape lives in the prompt text.

## Contents
- O1 Reasoning effort is a lever, not a dial to max
- O2 Verbosity and output shape
- O3 Reasoning-model prompt shape
- O4 Outcome-first, not step-by-step
- O5 Tool definitions: API surface vs skill text
- O6 The current flagship tier — check the capability, not the version

## O1 — Reasoning effort is a lever, not a dial to max  [judge]
The reasoning-effort control should be set deliberately — its exact field differs by
surface (verify it against the current guide for that API or CLI rather than pinning a
name, per O6), and it is an API/config control, not something the prompt text sets — so for
a CLI or bare prompt the config aspect is N-A (per the header), while the prompt-text aspect
stays a live check. On a direct-API prompt the effort/mode belong in `reasoning.effort` /
`reasoning.mode` (`pro` is an API mode, not a CLI control), not the prose. On a Codex/CLI
prompt, documented task-scoped steering is legitimate — subagent delegation, or high/max/ultra
effort for a hard, quality-first task — so FAIL only GLOBAL, unbounded, or unjustified
"always use max / hidden reasoning" language, or prose asking for a mode the target surface
does not document, not a scoped, reasoned choice. The default on the current model is the balanced middle — higher effort is not automatically better and can
cause overthinking or unnecessary searching. Flag prompts that always reach for the
top setting, or that never consider a lower one for latency-sensitive work.

## O2 — Verbosity and output shape  [judge]
When output length matters, control it explicitly with the verbosity control plus an
explicit output shape, and keep that separate from reasoning effort (a longer answer is
not more reasoning). For an API target, remove output-schema definitions from the prompt
and use Structured Outputs (or `codex exec --output-schema`); for a bare CLI prompt with no
schema mechanism, state the output shape in the text. Do not bake a STALE "today is …" date
literal into the prompt; a current date the running app injects at call time (a business
timezone, a policy-effective date, the user's local date) is legitimate (this mirrors C8,
and Gemini's G4 recommends the same runtime date anchor for recency-dependent prompts).

## O3 — Reasoning-model prompt shape  [judge]
For reasoning models: keep prompts simple and direct; do not ask for chain-of-thought
("think step by step" is unnecessary and can hurt); use delimiters; try zero-shot
first and add examples only if needed; place instructions at the right hierarchy level — use developer messages (or the
`instructions` field) for application steering, and where a surface exposes both system and
developer roles keep them distinct and follow that surface's documented hierarchy (reserve
system for the top-level policy/metadata the surface documents as system-level); include only the most relevant context (dumping everything degrades
reasoning). If the model suppresses markdown and you need it, the developer message opts
back in with the exact phrase "Formatting re-enabled" on its first line.

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
orchestration, and drive the Responses API directly when you need manual control of the
model loop and state. When the target is a codex-host skill, tool behavior documented in the
skill text is expected — apply C12 (clear names, small curated set), not the
API-field rule.

## O6 — The current flagship tier — check the capability, not the version  [judge]
OpenAI's current flagship tier keeps adding capabilities (higher reasoning-effort
tiers, subagent / multi-agent modes, explicit prompt-cache breakpoints); the exact names
and surfaces move and differ between the direct API and the Codex CLI. Review by
capability against the current official guide for that surface, not by release name: if
the target uses a top-effort setting, a subagent / multi-agent mode, or explicit cache
breakpoints, apply the current guidance (O1–O5) and put stable content first so a
breakpoint lands on it. De-pin reusable prompt PROSE and shipped trigger text — name the
capability, not a version or codename (C8); but an exact model ID, tier, or API field is
correct in a verified API/config/model-router context, so do not flag those. Where a
capability has no published guidance yet, mark the claim unverified or bounded-uncertain —
apply adjacent current guidance only as a labelled inference; do not invent rules or treat
a vague "flagship doctrine" as if it were documented.
