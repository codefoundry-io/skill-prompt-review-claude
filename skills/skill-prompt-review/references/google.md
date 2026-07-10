# Google / Gemini criteria

Apply these when the target is a prompt a Gemini model reads — a gemini worker
prompt, a direct-API call, or a gemini-*host* SKILL body — in addition to `common.md`. A
gemini-host skill (one the Gemini CLI loads from `skills/<name>/SKILL.md` via a
`gemini-extension.json` manifest) has its file STRUCTURE governed by the common criteria,
not these; but the G prompt-text criteria (G3 ordering/brevity, G4-G6) DO apply to its body,
with the API/config subparts (G1 sampler, G2 thinking_level) N-A for that non-API target.
Sources: Google's Gemini prompting-strategies, thinking, and function-calling documentation.

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
Gemini thinks dynamically by default — it adjusts reasoning effort to the request's
complexity — up to a ceiling set by `thinking_level`; set low for retrieval/classification
and high for coding/math/multi-step. `thinking_level` (values minimal/low/medium/high) is
the current documented control; the older `thinking_budget` token-count knob is the
`Gemini 2.5-series` control while `thinking_level` is the `3.0-series` control, and the two
cannot be combined — pairing them in one request returns an HTTP 400 (a Gemini-specific
error, kept distinct from Anthropic's separate `budget_tokens` 400 in A4), so match the
parameter to the model version and flag a prompt that sets both. For a CLI worker prompt `thinking_level` is set by the CLI,
not the prompt text — mark that part N-A (as G1 does); the prompt-shape half below still
applies. Let the model reason natively rather than forcing chain-of-thought with
hand-written scaffolding; if that was needed on an older model, raise the thinking level
and simplify the prompt. Verbose legacy prompt-engineering can make the model
over-analyze; be concise and direct.

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
over custom ones. For a time-sensitive query, Google explicitly recommends giving Gemini the current
date/year (its own prompting guidance bakes the current year into the system
instruction), so a current-date or -year anchor on a recency-dependent Gemini prompt
follows vendor guidance — do NOT flag it as a C8 violation. Prefer runtime injection where
the app can pass the date (it never ages); flag only a STALE or wrong baked date, or one
on a query that needs no recency.

## G5 — Function declarations  [judge]
Use descriptive `snake_case` or `camelCase` names — for the function and its parameters — with no spaces, and keep the
active tool set to a maximum of ten to twenty (Google's stated ceiling; C12's "small and
curated" is the general rule). The rest — clear descriptions, strong typing, validate-before-action — is C12.

## G6 — Avoid blanket epistemic negatives  [judge]
A lone "do not infer" / "do not guess" over-indexes Gemini and can make it fail basic
logic or arithmetic — this is the one spot C10's single-clarification exemption does not
hold, because the phrasing itself degrades the model. Reframe as a positive grounding
instruction: "use the provided context for deductions; avoid outside knowledge."
