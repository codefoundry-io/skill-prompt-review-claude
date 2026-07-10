# Repair — turn a review into a mechanical, tiered fix (optional)

Load this when the user opts into repairing a reviewed target. The review REPORTS; it does
not edit. Repair runs as a spec → implement → review loop (the shape a plan-driven
implementation skill uses), tiered by cost so the mechanical work goes to a cheap model and
the check goes to a stronger one. The orchestrator picks the tier per role and never pins a
model id — ids churn, the tier is the durable choice. Offer it after the report; recommend
it for the mechanical fixes (exact text swaps) and leave judgment-heavy rewrites to the
author, who holds the intent.

1. **Spec the fixes.** Turn each confirmed FAIL's fix into a line-level, MECHANICAL change:
   an exact `old → new` replacement carrying the precise current text and its replacement,
   not a prose instruction to "improve" something. Collect these into ONE throwaway
   spec/plan file (a temporary artifact, not part of the target or this skill). A fix that
   cannot be reduced to a deterministic replacement — a genuine rewrite or restructure — is
   flagged for the author instead; it is not mechanical repair.
2. **Implement with a LOW-tier writer sub-agent.** Dispatch a small, fast model (a low
   reasoning tier — e.g. a Haiku-class model, or an OpenAI nano/mini tier; the orchestrator
   selects) to apply the spec EXACTLY: each `old → new` replacement verbatim, nothing
   outside the spec, no creative rewriting. Mechanical replacement needs no strong model —
   the judgment already happened in the review.
3. **Verify with a MID-tier reviewer sub-agent.** Dispatch a mid reasoning tier (e.g. a
   Sonnet-class model; the orchestrator's choice) to check the implementation against the
   spec: every replacement applied, applied correctly, and nothing else touched or broken.
   On a mismatch it reports back and the writer re-applies — the same write → review loop a
   subagent-driven implementation uses. Do NOT let the writer self-certify; the reviewer is
   a separate agent.
4. **Clean up, then re-review.** Once the reviewer confirms the implementation, DELETE the
   throwaway spec/plan file — it is a transient artifact, never a shipped part of the
   target. Then, because you have now EDITED the target, run the fresh-eye review again on
   the changed files: the "do not review your own draft" rule applies to a repair too, and
   a mechanical edit can still introduce a new defect.

Tier discipline in one line: mechanical writing → low tier, verification → mid tier, and
the final fresh-eye re-review stays at whatever tier the review itself warrants — the
orchestrator routes each role, and no model id is hard-pinned anywhere in the spec.

Spawn every repair sub-agent with a FRESH context — no inherited orchestrator history (on
codex, `spawn_agent` with `fork_context=false` and `reasoning_effort` at the role's tier;
a claude Agent already starts fresh). No pre-defined per-role agent config file is required:
the orchestrator spawns each sub-agent ad hoc with its tier and hands it only its own packet
(the spec for the writer, the spec + edited target for the verifier), so nothing beyond the
skill itself needs installing.
