# Common criteria — applies to every target

The checks below hold for any skill or prompt regardless of vendor. Each names how
it is checked: **[script]** for the mechanical checks `scripts/lint.py` runs, or
**[judge]** for a reading a fresh-eye reviewer must do. Some are both — the script
flags candidates, the reviewer confirms. A `[script]` detector flags COMMON high-signal
candidates, not an exhaustive set; a phrase it does not catch is the reviewer's `[judge]`
catch, not a linter defect.

Isolation (C3), trigger quality (C1), and single responsibility (C2) are the same
concepts a dedicated sub-agent reviewer checks on sub-agent `.md` files; this file
states them for skills and prompts.

## Contents
- C0 Frontmatter loads (a SKILL.md must register)
- C1 Description says what AND when
- C2 One job
- C3 Isolation — mostly inputs, actions, outputs
- C4 No priming (the pink-elephant check)
- C5 Lean
- C6 Calm imperatives
- C7 No over-scaffolding
- C8 No time-stamped facts
- C9 Progressive disclosure
- C10 Positive framing
- C11 Distribution hygiene
- C12 Tool and skill authoring universals
- C13 Gate irreversible actions
- C14 Order long context
- C15 No self-contradiction
- C16 Invocation construction (a dispatch skill's CLI call)

---

## C0 — Frontmatter loads  [script] + [judge]
Before any other check, a SKILL.md must actually LOAD, or every other criterion is
moot. The script checks the structural basics — the file begins with `---` on line 1
(no blank line or BOM before it), the block is closed, `name` and `description` are
present, and `name` matches the containing directory (case-sensitive). The Agent Skills
spec requires that match (after NFKC normalization), so a distributed or API-uploaded
skill with a mismatch is rejected; Claude Code's local filesystem loader is more lenient —
it derives the command from the directory and treats `name` as an optional display
default, so locally a mismatch changes only the display name. Flag a mismatch: it breaks
the spec and distribution. The reviewer confirms the frontmatter is valid YAML beyond that
shape. Fix: correct the delimiter, the YAML, or the
name-to-folder match. A bare prompt has no frontmatter, so this applies to a SKILL.md
only.

## C1 — Description says what AND when  [judge]
The description is the whole trigger signal. It should state what the target does
*and* the concrete situations to reach for it, in the reader's own language. A
description that only says what it does (no "when") under-triggers; one that is vague
over-triggers. Fix: add the missing half — the missing "when" contexts, or a sharper
"what".

## C2 — One job  [judge]
The target should do one thing. If describing it needs an "and also", or the body
does two unrelated jobs, it is two targets. Guidance for the invoker plus a procedure
for the executor of the same job is still one job. Fix: split, or cut the second job.

## C3 — Isolation: mostly inputs, actions, outputs  [judge] + [script assists]
Strip the role line and headers; most of what remains should describe an input the
target receives, an action it takes, or an output it returns. A brief reason,
constraint, or example that makes an instruction land is welcome, not a violation.
What to cut is the *world the target lives in* but does not act on: another tool's
cost, its "usage caps", a version history, an incident story. Fix: delete a world-fact,
or move a load-bearing one to where it is used. The script flags likely offenders
("price" and usage-limit phrasings); the reviewer decides whether a sentence earns its
place.

## C4 — No priming: the pink-elephant check  [script] + [judge]
Naming a thing makes it salient. A prompt that lists the rationalizations for
skipping a step plants them as options the model might not have weighed; a prompt
that narrates a past failure primes that failure. Fix: state the wanted behavior
once, with its reason, and leave out the catalog of ways to get it wrong. Exception:
when the target's own job is to recognize a hazard or a forbidden input (safety,
security, compliance), naming it once — paired with the wanted action — is required,
not priming. Second exception: a "Gotchas" or "Troubleshooting" section that states a
known failure point as positive corrective guidance ("close the handle after reading —
a common miss that leaks descriptors") is high-signal skill content, not priming — vendor
skill-authoring guidance explicitly recommends capturing common mistakes as reusable
context. What C4 flags is NARRATING the past failure ("the model kept forgetting to close
the handle"), not documenting the correct behavior with its reason. The script flags common
excuse and past-incident phrasings; the reviewer catches subtler priming and confirms the
exceptions.

## C5 — Lean  [judge]
Include only what the model does not already know; assume it is capable. Cut
duplicated blocks (the same rule restated in prose and again in a table), padding,
and anything not pulling its weight. Fix: delete; if a rule matters, once is enough.
Spotting a rule restated in two places, or padding, is the reviewer's call; the raw
length signal it leans on is reported by C9.

## C6 — Calm imperatives  [script] + [judge]
On capable models, a wall of `CRITICAL` / `you MUST` / `NEVER` / `MANDATORY`
back-fires — it inflates attention and over-triggers, and a brief instruction steers
just as well. Express a rule as "Use X when Y" plus a one-line why. Reserve emphasis
for the rare genuinely-destructive case. The script reports capitalized-imperative
density; a high density is the flag, not any single word.

## C7 — No over-scaffolding  [judge]
Prescriptive step-by-step lists a capable model does not need, and anti-laziness
padding ("be thorough", "don't be lazy"), waste context and can degrade output.
Trust instruction-following; give the goal and the constraints, and prescribe an
exact sequence only where the path genuinely matters (fragile or irreversible
operations). Fix: replace the step list with the goal and its reason. A tool-heavy or
agentic workflow still needs a clear stopping condition or definition of done so it does
not loop — that is a constraint to keep, not scaffolding to cut.

## C8 — No time-stamped facts  [script] + [judge]
Hardcoded dates, pinned version numbers, and pinned model names or codenames in a
prompt go stale and read as noise, and a word that marks a release as recent ages the
moment it is written. Phrase around the moving target — "the current flagship
reasoning tier" rather than a pinned name. This criterion scores the TARGET's instruction
text, not these vendor references (which name a model family or capability only to define
when they apply); the linter flags candidates in any file, so confirm a reference-file hit
is a real pin in instruction text, not scoping language. Provenance — a build date, a re-probed
version — belongs in commit history, or a dedicated `changelog:` block in the
frontmatter (read as a version ledger, not as live instruction); a rule or criterion
body stays de-dated. Deprecated guidance belongs in an "old patterns" section, not
stamped with when it changed. This bans *stale* baked-in values, not a
date the running app must pass at call time (a business timezone, a user's local
date). Fix: remove the stale date, version, or model pin, or move it out of the
prompt.

## C9 — Progressive disclosure  [script] + [judge]
A SKILL.md should be a lean overview that points to detail in `references/`, not a
place that inlines everything. Keep the body a reasonable length, keep references one
level deep, and give a reference file over ~100 lines a table of contents. Fix: move
inlined detail into a reference and link to it. The script reports body length and a
missing table of contents on a long reference; one-level-deep is the reviewer's check.

## C10 — Positive framing  [script] + [judge]
Tell the model what to do, not what to avoid — a positive instruction is clearer and
side-steps the priming in C4. The flag is a dense run of "do not" / "never", not a
single honest clarification ("dispatch to a separate agent, not the author's"). A
scope-bounding constraint ("do exactly what is asked; do not add unrequested work or
refactor beyond the task") is the vendor-endorsed scope-discipline lever (OpenAI O4,
Anthropic A6) that counters a capable model's tendency to over-build — keep it; the flag is
a DENSE RUN of prohibitions, not any single bounded one. Fix: rewrite each gratuitous
prohibition as the wanted action; keep a named hazard only where C4's exception allows,
and a scope bound where it earns its place. The script reports negation density.

## C11 — Distribution hygiene  [script] + [judge]
A target shipped outside its home follows the consumer's language and mental model. A
distributed description in a non-consumer language mis-targets the trigger; internal
file paths and local jargon leak context the consumer cannot use. This applies to a
target that ships — a purely local skill may keep local framing. **Trigger keywords are
exempt**: the phrases a skill fires on (usually quoted in the description) may be in the
user's language even when the skill ships, because they must match how the user phrases
the request — so the check is on the description's PROSE, not its trigger keywords. Fix:
for a shipped target, translate the PROSE to the consumer's language and replace internal
references with consumer-facing ones, but keep the trigger keywords in whatever language
the user types. The script strips quoted spans and flags non-Latin PROSE only; the
reviewer judges whether that prose language is wrong for the consumer.

## C12 — Tool and skill authoring universals  [judge]
Where the target defines or invokes tools: names are clear and each description says
what the tool does *and* when to use it; the active tool set is small and curated
(consolidate frequently-chained calls rather than exposing every endpoint); tool
parameters are strongly typed and validated; parameters use semantic identifiers a
model can reason about rather than raw UUIDs or opaque hashes (an opaque identifier is
the single biggest cause of tool-call hallucination); a tool failure returns actionable
natural-language feedback, not a bare error code; one term is used per concept throughout.
These hold across all three vendors — the vendor files add only what is specific to
each, and where a vendor gives a concrete number, this general rule ("prefer fewer")
is the tie-breaker.

## C13 — Gate irreversible actions  [judge]
If the target can delete, deploy, spend money, change permissions, or send data outside
its boundary, it should require explicit approval — or a clear stop condition — before
the action, rather than acting on its own. This is a place a named hazard belongs (C4's
exception): pair the risky capability with the approval it needs. Fix: add the approval
gate or stop rule; for a sensitive skill, prefer explicit invocation over automatic
triggering. This reviews the target's *text* — whether the prompt or skill asks for the
gate — not the runtime that enforces it.

## C14 — Order long context  [judge]
When a prompt carries a large document or data block, place it first and put the specific
instruction or question at the very end, with a short anchor to the material above. A
query placed before or inside a long context measurably degrades the answer. Fix: move
the instruction to the end and anchor it ("based on the material above, …"). Vendor files
may add the house anchor phrasing, but the ordering itself is universal.

## C15 — No self-contradiction  [judge]
The instructions should agree with each other — no conflicting rules, priorities, output
formats, or stop conditions. A reasoning model spends tokens reconciling a contradiction
and often resolves it the wrong way. Fix: reconcile or remove the conflicting instruction
so a single reading is possible.

## C16 — Invocation construction  [judge]
When the target builds a CLI or subprocess invocation (a dispatch skill assembling a
command for codex / gemini / claude), the constructed command must be
quoting-safe — an argument with spaces, quotes, or newlines survives intact — the flags
must match the CLI's actual contract, and untrusted input must not be able to inject
shell or an extra flag. Fix: build the command as an argv array or quote every
substitution, and verify flags by reference lookup (the CLI's documented interface —
this skill reviews text, it does not run the target). Separately from shell safety,
untrusted input embedded in a built prompt should be fenced with delimiters or tags so
it cannot be read as instructions (prompt-injection isolation). This is the worker axis
for a transport-only dispatch skill that builds no fixed prompt.
