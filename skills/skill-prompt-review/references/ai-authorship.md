# AI-authorship criteria — the chat-register signature

Apply these when the target may have been authored BY an AI — increasingly the default,
since people have a model write the prompt or skill for them. The common and vendor
criteria are organized by prompt *defect symptom* (leanness, priming, stale dates); these
are organized by the *authorship signature* — the residue a model leaves when it writes a
shipped instruction the way it writes a chat reply. They catch what the symptom criteria
only partially cover. Load them in addition to `common.md`.

The one question behind all of them: does this read like an assistant's chat reply, or
like a cold, standalone instruction? A shipped prompt is the latter. Sources: prior
reviewed AI-authored prompts and skills (each item below is a defect an AI author committed
and a review caught) plus the published prompt-hygiene literature on AI-generated-prompt
slop, controlling-text-that-adds-variance, sycophancy, and over-formatting.

## Contents
- AA1 No authoring-conversation carryover (user-framing)
- AA2 No chat-register padding
- AA3 Calibrated imperatives, not sycophantic softeners
- AA4 No confabulated specifics
- AA5 No decoration overload
- AA6 One language — the consumer's, not the chat's

## AA1 — No authoring-conversation carryover  [script] + [judge]
The prompt must stand alone, not point back at the conversation that produced it. Flag
deixis that references a vanished chat: "as you requested", "the file / task we
discussed", "you asked me to", "per our conversation", "like you mentioned", and a
second-person "you / your" that means the *author* rather than the runtime user. The
consumer never saw that conversation, so every such reference resolves to nothing. Say
the thing directly: not "analyze the file we discussed" but "analyze `<path>`". The linter
flags the fixed carryover phrases; whether a bare "you / your" addresses the author or the
runtime user is the reviewer's judgment.

## AA2 — No chat-register padding  [script] + [judge]
The assistant's reply register bleeds into the artifact: conversational openers ("Great
question!", "Sure!", "I'll help you", "Let me…"), self-reference ("as an AI", "as a
language model", "I want to be careful here"), apology ("sorry", "I apologize"),
sign-offs ("I hope this helps", "let me know if…"), and restating the request back before
acting on it. A shipped prompt states the task; it does not converse about it. Cut the
padding to the instruction itself.

## AA3 — Calibrated imperatives, not sycophantic softeners  [script] + [judge]
Over-politeness from the chat register produces imperatives too weak to steer: "you might
want to consider maybe", "if you'd like, please try to", "it would be great if you could
perhaps". State the instruction directly — "Validate the input." This is C6's mirror
image: C6 flags shouting (ALL-CAPS / MANDATORY), AA3 flags whispering. Both miss the
calm, direct middle a good instruction lives in.

## AA4 — No confabulated specifics  [judge]
Fluent invention is cheaper for a model than verification, so an AI author states
plausible specifics it never confirmed — a CLI flag that does not exist, an API field, a
numeric limit, a model version. Every concrete flag, limit, field, or capability the
prompt asserts must be checkable against an official source; if the author could not
verify it, the prompt must not state it as fact (phrase around the unknown, or drop it).
This is the authorship *why* behind C16 (verify flags by reference lookup) and O6 (do not
invent rules) — the same defect, named at its source.

## AA5 — No decoration overload  [script] + [judge]
An AI over-formats to signal effort and helpfulness: emoji, bolding whole phrases,
decorative headers, ornamental markdown. Decoration inflates attention and adds noise
without adding instruction. Keep formatting functional — structure that a reader acts on,
not ornament that says "I tried". The linter flags emoji and decorative glyphs
mechanically; whole-phrase bolding and ornamental headers are the reviewer's judgment (a
bolded key term is functional, a bolded whole sentence is decoration).

## AA6 — One language — the consumer's, not the chat's  [script] + [judge]
An AI authors in whatever language the conversation is running in. A prompt meant for an
English-consuming worker, or a distributed consumer, must not inherit the authoring
chat's language anywhere in its body (C11 governs the description specifically; this
extends it to the whole artifact). Write the shipped PROSE in the consumer's language.
**Quoted trigger phrases and example user-input strings are exempt** — a skill lists the
phrases that fire it, which may legitimately be in the user's language; the check is on
unquoted prose, not on the quoted triggers/examples the skill teaches. The linter's
`[script]` candidate is an unquoted non-Latin-script scan of the body; a Latin-script drift
(a stray French or Spanish line in an English body) has no crisp signature and is the
reviewer's `[judge]` catch.
