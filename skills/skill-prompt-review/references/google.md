# Google / Gemini criteria

Apply these when the target is a prompt written for a Gemini model (e.g. a gemini worker prompt) — in addition to `common.md`. Sources: Google's Gemini
prompting-strategies, thinking, and function-calling documentation.

## Contents
- G1 Sampler settings (API-target only; reference)
- G2 Thinking level is a ceiling, not a target
- G3 Long-context ordering, constraint placement, and default brevity
- G4 Ground and compute with tools
- G5 Function declarations
- G6 Avoid blanket epistemic negatives

## G1 — Sampler settings (API-target only; reference)  [judge]
This applies only when the target is a direct API call or its config — not a CLI
worker/dispatch prompt, which has no access to the sampler. When it applies, keep temperature,
top_p, and top_k at their defaults; non-default sampling can cause looping or degraded
reasoning. For a CLI worker prompt, mark this N-A — the sampler is fixed by the CLI, not
the prompt text.

## G2 — Thinking level is a ceiling, not a target  [judge]
Gemini thinks dynamically up to a ceiling set by `thinking_level` (default high; use low
for retrieval/classification, high for coding/math/multi-step). Prefer `thinking_level`
over a hand-set `thinking_budget` — use one, not both. For a CLI
worker prompt these are set by the CLI, not the prompt text — mark that part N-A (as G1
does); the prompt-shape half below still applies. Do not force
chain-of-thought with hand-written scaffolding; if that was needed on an older model,
raise the thinking level and simplify the prompt. Verbose legacy prompt-engineering can
make the model over-analyze; be concise and direct.

## G3 — Long-context ordering, constraint placement, and default brevity  [judge]
Long-context ordering is the common rule (C14); for Gemini, anchor the closing
instruction with a phrase like "Based on the preceding information". Gemini also drops
constraints that appear too early in a complex request, so put negative rules,
formatting instructions, and numeric limits at the very end — after the context and
just before the closing instruction (C14). Gemini is also direct and brief by default — if you need a fuller or more conversational
answer, ask for it explicitly.

## G4 — Ground and compute with tools  [judge]
Enable grounding with search when the model may need recent or obscure facts, and
enable code execution for arithmetic or counting rather than trusting the model to
compute in its head. Prefer widely recognized output formats (JSON, XML, Markdown)
over custom ones. For a time-sensitive query a current-date or -year anchor is fine when
the running app passes it at call time (C8's call-time-date exception); a baked-in year
still ages and violates C8 — flag the baked one, not the runtime one.

## G5 — Function declarations  [judge]
Use descriptive `snake_case` or `camelCase` parameter names with no spaces, and keep the
active tool set to roughly ten to twenty (C12's "small and curated" is the general
rule). The rest — clear descriptions, strong typing, validate-before-action — is C12.

## G6 — Avoid blanket epistemic negatives  [judge]
A lone "do not infer" / "do not guess" over-indexes Gemini and can make it fail basic
logic or arithmetic — this is the one spot C10's single-clarification exemption does not
hold, because the phrasing itself degrades the model. Reframe as a positive grounding
instruction: "use the provided context for deductions; avoid outside knowledge."
