# Anthropic / Claude criteria

Apply these when the target is a Claude SKILL.md (a claude host loads it) or a
prompt written for a Claude model — in addition to `common.md`. A1 (frontmatter) and A2
(progressive disclosure) are claude-HOST STRUCTURE criteria — check them on any claude-host
SKILL.md. A3-A6 are BODY-as-prompt criteria: they govern a bare Claude prompt and, because
a claude-host body is itself a Claude prompt, that body too. Within A4, split by target as
the OpenAI/Gemini preambles do for O1/O2/G1: for a non-API target (a claude-host SKILL body
or a CLI prompt) the CONFIG subpart — the effort setting, `budget_tokens`, last-turn prefill
— is N-A, since a SKILL body cannot set them; only A4's prompt-text half stays live (do not
echo internal reasoning; the `think`/`ultrathink` harness keywords). Full A4 applies to a
bare Claude prompt that is an actual API call. A7 applies only where the target defines or
documents tools. Sources: the Anthropic Agent Skills best-practices, the per-model prompting
pages, and the context-engineering guidance.

## Contents
- A1 SKILL.md frontmatter conforms to the spec
- A2 Progressive disclosure the Anthropic way
- A3 Right degrees of freedom
- A4 Effort and thinking, not manual budgets
- A5 Structure with XML, steer with examples and a role
- A6 Refactor prompts built for older models
- A7 Tool authoring

## A1 — SKILL.md frontmatter conforms to the spec  [judge]
`name`: lowercase letters, numbers, hyphens; within the length limit; matches the
containing directory (the Agent Skills spec requires it — a distributed/uploaded skill is
rejected on mismatch; a local Claude Code skill still loads, deriving its command from the
directory — see C0); and must not CONTAIN the reserved words "anthropic" or "claude" anywhere in it — the Agent Skills spec rejects
a name that contains either as a substring (`claude-tools` and `anthropic-helper` are both
invalid), not only the bare words; prefer a gerund ("processing-pdfs") over a vague noun
("helper"). `description`: third person, states what it does *and* when to use it,
within the length limit, no XML tags. These two fields are the whole trigger signal;
load-ability itself (`---` on line 1, valid YAML) is C0.

## A2 — Progressive disclosure the Anthropic way  [judge]
SKILL.md is a table-of-contents overview; detail lives in bundled files loaded on
demand. Keep the body lean, references one level deep, and a reference over ~100
lines carries a table of contents. Bundle comprehensive resources freely — a file
costs nothing until it is read.

## A3 — Right degrees of freedom  [judge]
Match freedom to the task: prose instructions when many approaches are valid;
parameterized scripts when a preferred pattern exists; exact scripts ("run this,
don't modify it") only where an operation is fragile and consistency is critical.
Over-constraining a task that has many valid solutions is as much a fault as
under-specifying a fragile one.

## A4 — Effort and thinking, not manual budgets  [judge]
On the current Claude generation, effort is the primary intelligence/latency/cost
lever and adaptive thinking decides how much to think. Set effort to the task: flag a
prompt that pins effort to max for a simple or latency-sensitive task, or never
considers a lower one (the Claude side of O1). On the current Claude generation a manual
thinking budget is rejected with a 400 and last-assistant-turn prefill is unsupported,
so flag a prompt that hand-manages a thinking budget or relies on prefill; for an older
thinking-enabled model, check the target model's card first. Also flag a prompt that asks the model to echo or transcribe its
internal reasoning as output text — that works against the model. In the Claude Code
harness the word "think" (and "think harder" / "ultrathink") can raise how much the
model thinks; prefer "consider" or "evaluate" as filler verbs where extra reasoning is
not wanted.

## A5 — Structure with XML, steer with examples and a role  [judge]
Claude responds well to XML-tagged structure (`<instructions>`, `<context>`,
`<example>`), a role set in the system prompt, and a few relevant, diverse examples
where output shape matters. For formatting, show the wanted form (a positive
example) rather than listing what to avoid. For prompt caching, keep the immutable
prefix (role, policy, tool schemas) stable and place the cache breakpoint after it; a
prompt that churns its stable prefix defeats the cache (the Claude side of O6).

## A6 — Refactor prompts built for older models  [judge]
Current Claude models need less scaffolding: they orchestrate sub-agents
natively and follow brief instructions. A prompt carried over from an older model often over-specifies — flag
aggressive anti-laziness language, blanket "default to tool X" rules, and long
prescriptive plans, and give the goal, success criteria, and constraints instead of a
hand-written step list — rely on the effort setting for depth, not on a "think harder"
instruction (A4: "think" can raise thinking in the harness).

## A7 — Tool authoring  [judge]
Write each tool description as if onboarding a new hire — make implicit context explicit,
with unambiguous parameter names. The cross-vendor tool rules (a few high-impact tools,
semantic identifiers over low-level IDs, actionable errors, consolidating
frequently-chained calls) are C12; this file adds only that onboard-a-new-hire style.
