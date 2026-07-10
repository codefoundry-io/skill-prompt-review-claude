#!/usr/bin/env python3
"""Deterministic lint for skill-prompt-review.

Runs the mechanical candidates from references/common.md (C-series) and
references/ai-authorship.md (AA-series) against a SKILL.md or a prompt file and prints
CANDIDATE findings. It does not judge: the semantic
criteria (isolation, priming subtlety, over-scaffolding, description quality) are
for a fresh-eye reviewer. A finding here is a candidate the reviewer confirms or
dismisses — the script exists so the reviewer spends attention on judgment, not on
counting.

Usage:  lint.py [--kind skill|reference|prompt] <file> [<file> ...]
(--kind overrides the path-based classification when a file is not in a
conventionally-named location.) Runs on Python 3.12; no third-party dependencies.
"""
import re
import sys
import unicodedata
from pathlib import Path

# Tunable soft defaults. A finding is a candidate, never a verdict — the reviewer
# confirms it; adjust per project if a threshold mis-flags.
CAPS_IMPERATIVE_PER_100_LINES = 8   # above this density = a wall of imperatives (C6)
NEGATIONS_PER_100_LINES = 8         # above this density = 'what not to do' framing (C10)
BODY_LINES_SOFT = 200               # a SKILL.md body over this: consider moving detail to references/ (C9)
REF_TOC_LINES = 100                 # a reference file over this should carry a table of contents (C9)
DENSITY_MIN_LINES = 25              # C6/C10 density only flags a body at least this long (a short prompt can't trip it)

CAPS_IMPERATIVES = ("CRITICAL", "MANDATORY", "MUST", "NEVER", "ALWAYS", "REQUIRED", "DO NOT")
NEGATIONS = (r"do not", r"don't", r"never", r"must not", r"cannot")  # C10 density

# C8 detection patterns — shared by the body scan and the frontmatter-DESCRIPTION scan (a
# stale pin in the shipped `description:` would otherwise bypass C8 entirely).
C8_DATE_RX = (r"\b20\d{2}[-/]\d{2}[-/]\d{2}\b|\(20\d{2}[-)]|"
              r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+20\d{2}\b")
# A bare current-year anchor, but only next to a temporal keyword — a plain 4-digit number
# ("issue 2026", "line 2026") is not a date. G4 lets the reviewer keep a valid Gemini anchor.
C8_BARE_YEAR_RX = (r"(?i)\b(?:current year|this year|knowledge cutoff(?: date)?|as of|it is|"
                   r"today is|year is)\b.{0,15}?\b20\d{2}\b|\b20\d{2}\b.{0,6}?\bthis year\b")
# Three-part semver, but not any octet of a 4-part IP (192.168.1.1).
C8_SEMVER_RX = r"(?<![\w.])v?\d+\.\d+\.\d+\b(?!\.\d)"
C8_TOOLVER_RX = (r"(?i)\b(?:python|node(?:\.js)?|ruby|golang|rust|php|npm|pip|java|kotlin|"
                 r"swift|deno|dotnet|postgres(?:ql)?|mysql|redis|ubuntu|debian)\s+v?\d+(?:\.\d+)*\b")
# Family-prefixed model pins (gpt-5.6, claude 4.8, gemini-3.1-pro), a bare lowercase o-series
# (o3, o4-mini — case-sensitive so an uppercase 'O1' criterion label is NOT matched), and codenames.
C8_MODELPIN_RX = (r"(?i)\b(?:gpt|claude|gemini|opus|sonnet|haiku|codex|fable|mythos)[-\s]?\d+(?:\.\d+)?[a-z0-9-]*\b|"
                  r"\b(?-i:o[1-9](?:-[a-z][a-z0-9-]*)?)\b|"
                  r"\b(?-i:Sol|Terra|Luna|Fable|Mythos)\b")
# Release-aging language: a recency word ANCHORED to a release/model/version noun ("newest
# model", "latest flagship") — a word that marks a release as recent ages the moment it is
# written. The anchor avoids flagging ordinary prose ("new file", "recent commit").
C8_RECENCY_RX = (r"(?i)\b(?:new|newest|newly|latest|recent|recently|brand[- ]new|cutting[- ]edge|"
                 r"state[- ]of[- ]the[- ]art|preview|upcoming|just[- ]released)\b"
                 r"[- \w,]{0,20}?\b(?:model|release|version|tier|flagship|capabilit|api|feature)\w*")


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter, body). Frontmatter is the leading --- ... --- block."""
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    return (m.group(1), m.group(2)) if m else ("", text)


def get_description(frontmatter: str) -> str:
    m = re.search(r"(?ms)^description:[ \t]*(.*?)(?=^\w[\w-]*:|\Z)", frontmatter)
    return m.group(1).strip() if m else ""


def lines_matching(body: str, pattern: str, flags: int = 0):
    rx = re.compile(pattern, flags)
    return [(i, ln.strip()) for i, ln in enumerate(body.splitlines(), 1) if rx.search(ln)]


def _inside_quote(body: str, abs_pos: int) -> bool:
    """True if abs_pos sits inside an open double-quote (straight or curly) or backtick span,
    counting from the body start so a quote/code-span that WRAPS across lines still shields
    its content. A quoted or `backticked` phrase is scoping language a criteria/reference file
    uses to NAME or TEACH a pattern (a model id, a bad phrase), not prompt residue that
    commits it — consistent with C8/O6 allowing an exact id in a config/identifier context."""
    prefix = body[:abs_pos]
    return (prefix.count('"') % 2 == 1 or prefix.count("`") % 2 == 1
            or (prefix.count("“") - prefix.count("”")) > 0)


def lines_matching_unquoted(body: str, pattern: str, flags: int = 0):
    """lines_matching, minus matches that sit inside a quoted example (possibly a multi-line
    quote). Used by the phrase detectors (AA1/AA2/AA3, C4) so a reference file that QUOTES a
    bad phrase to define a rule is not mis-flagged as committing it. A same phrase UNQUOTED
    still fires."""
    rx = re.compile(pattern, flags)
    out, pos = [], 0
    for i, ln in enumerate(body.splitlines(keepends=True), 1):
        stripped = ln.rstrip("\n")
        if any(not _inside_quote(body, pos + m.start()) for m in rx.finditer(stripped)):
            out.append((i, stripped.strip()))
        pos += len(ln)
    return out


def target_kind(path: Path, explicit: str | None = None) -> str:
    """skill (a SKILL.md) | reference | prompt. An explicit kind (from --kind) wins;
    otherwise a SKILL.md is detected by its mandatory filename (reliable), and
    reference-vs-prompt falls back to the directory (a soft distinction that only gates
    the reference table-of-contents check)."""
    if explicit in ("skill", "reference", "prompt"):
        return explicit
    if path.name == "SKILL.md":
        return "skill"
    if path.parent.name == "references" or "references" in path.parts:
        return "reference"
    return "prompt"


def frontmatter_load_issue(text: str, path: Path) -> str | None:
    """C0: a STRUCTURAL reason a SKILL.md will not load/register, or None. Structural
    only \u2014 deeper YAML validity is the reviewer's [judge] call."""
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return "does not begin with '---' on line 1 (blank line / BOM / missing) \u2014 will not load"
    fm, _ = split_frontmatter(text)
    if not fm.strip():
        return "frontmatter is empty or not closed by a second '---' \u2014 will not register"
    if not re.search(r"(?m)^name:[ \t]*\S", fm):
        return "frontmatter has no 'name' field \u2014 will not load"
    m_desc = re.search(r"(?m)^description:[ \t]*(.*)$", fm)
    if not m_desc:
        return "frontmatter has no 'description' field \u2014 will not register"
    # Content may be inline (`description: text` / a block-scalar marker `| `/`>`) OR on an
    # indented continuation line (`description:\n  text`). Only a truly empty field fails.
    if not m_desc.group(1).strip() and not re.match(r"\r?\n[ \t]+\S", fm[m_desc.end():]):
        return "frontmatter 'description' field is empty \u2014 will not register"
    m = re.search(r"(?m)^name:[ \t]*(.+?)[ \t]*$", fm)  # full scalar on the name line
    folder = path.resolve().parent.name
    if m and folder:
        # strip an inline YAML comment (space + #), surrounding quotes, and whitespace,
        # then compare the WHOLE value — a trailing token (`name: foo bar`) must not pass.
        name_val = re.sub(r"[ \t]+#.*$", "", m.group(1)).strip().strip("\"'")
        # The Agent Skills spec compares name↔folder after NFKC normalization (common.md C0).
        if unicodedata.normalize("NFKC", name_val) != unicodedata.normalize("NFKC", folder):
            return (f"name '{name_val}' != directory '{folder}' \u2014 the Agent Skills spec requires a "
                    "match (a distributed/uploaded skill is rejected); a local Claude Code skill still "
                    "loads, deriving its command from the directory")
    return None


def lint(path: Path, explicit_kind: str | None = None) -> list[tuple[str, str, list[str]]]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    fm, body = split_frontmatter(text)
    fm_offset = text[: len(text) - len(body)].count("\n")  # body line n -> file line n + fm_offset
    desc = get_description(fm)
    body_lines = len(body.splitlines()) or 1
    kind = target_kind(path, explicit_kind)  # "skill" | "reference" | "prompt"
    out: list[tuple[str, str, list[str]]] = []

    def add(crit, summary, hits):
        out.append((crit, summary, [f"L{n + fm_offset}" for n, _ in hits[:6]]))

    # C0 — frontmatter loads (a SKILL.md only; a prompt/reference has no frontmatter).
    if kind == "skill":
        issue = frontmatter_load_issue(text, path)
        if issue:
            out.append(("C0 frontmatter loads", issue, []))

    # C8 — time-stamped facts: dates, bare current-year anchors, versions, model pins.
    # Scanned over the BODY and (below) the shipped frontmatter description.
    dates = lines_matching(body, C8_DATE_RX)
    if dates:
        add("C8 time-stamped facts", f"{len(dates)} hardcoded date(s) in the body", dates)
    byears = lines_matching(body, C8_BARE_YEAR_RX)
    if byears:
        add("C8 time-stamped facts",
            f"{len(byears)} bare current-year anchor(s) — de-pin or inject at runtime "
            "(G4 may exempt a recency-dependent Gemini prompt)", byears)
    versions = lines_matching_unquoted(body, C8_SEMVER_RX)
    if versions:
        add("C8 version pins", f"{len(versions)} pinned version number(s)", versions)
    toolvers = lines_matching_unquoted(body, C8_TOOLVER_RX)
    if toolvers:
        add("C8 version pins", f"{len(toolvers)} pinned tool/runtime version(s)", toolvers)
    modelpins = lines_matching_unquoted(body, C8_MODELPIN_RX)
    if modelpins:
        add("C8 model pins", f"{len(modelpins)} pinned model name/version — phrase around the moving target", modelpins)
    recency = lines_matching(body, C8_RECENCY_RX)
    if recency:
        add("C8 time-stamped facts",
            f"{len(recency)} release-aging phrase(s) (a recency word on a model/release) — describe the tier, not its recency", recency)
    # C8 over the shipped DESCRIPTION (trigger text): a stale model/date/recency pin there
    # bypasses the body scan. Report at the `description:` field's file line.
    if desc:
        desc_line = next((i for i, ln in enumerate(text.splitlines(), 1)
                          if re.match(r"(?i)\s*description\s*:", ln)), 1)
        for label, pat in (("C8 time-stamped facts", C8_DATE_RX), ("C8 time-stamped facts", C8_BARE_YEAR_RX),
                           ("C8 version pins", C8_SEMVER_RX), ("C8 version pins", C8_TOOLVER_RX),
                           ("C8 model pins", C8_MODELPIN_RX), ("C8 time-stamped facts", C8_RECENCY_RX)):
            if re.search(pat, desc):
                out.append((label, "pinned/stale value in the shipped description — de-pin the trigger text", [f"L{desc_line}"]))

    # C6 — capitalized-imperative density.
    caps = [(i, ln) for i, ln in enumerate(body.splitlines(), 1)
            if any(w in ln for w in CAPS_IMPERATIVES)]
    density = 100 * len(caps) / max(body_lines, 1)
    if body_lines >= DENSITY_MIN_LINES and density > CAPS_IMPERATIVE_PER_100_LINES:
        add("C6 imperative density",
            f"{len(caps)} imperative lines = {density:.0f} per 100 "
            f"(soft limit {CAPS_IMPERATIVE_PER_100_LINES})", caps)

    # C4 — priming: enumerated excuses and past-failure narratives. Kept to
    # high-signal phrases; a bare run of quoted strings is left to the reviewer
    # (it also matches legitimate value enumerations like "red", "green", "blue").
    excuses = lines_matching_unquoted(
        body,
        r"are\s+NEVER\s+valid|not\s+(?:a\s+)?(?:valid|good)\s+reason|\bno\s+excuse\b|"
        r"\b(?:do\s+not|don'?t)\s+skip\b.{0,30}\bbecause\b",
        re.I)
    if excuses:
        add("C4 enumerated excuses", f"{len(excuses)} line(s) framing rationalizations to avoid", excuses)
    narratives = lines_matching_unquoted(
        body,
        r"\(origin:|historical reason|reason for the ban|"
        r"\b(?:kept|keeps|used\s+to)\s+forgetting\b|\bpreviously\s+failed\b|"
        r"\bthe\s+model\s+(?:kept|keeps|used\s+to)\b",
        re.I)
    if narratives:
        add("C4 failure narrative", f"{len(narratives)} past-incident narrative(s)", narratives)

    # C10 — negation density (a proxy for "what not to do" framing).
    neg = sum(len(re.findall(rf"\b{n}\b", body.replace("\u2019", "'"), re.I)) for n in NEGATIONS)
    neg_density = 100 * neg / max(body_lines, 1)
    if body_lines >= DENSITY_MIN_LINES and neg_density > NEGATIONS_PER_100_LINES:
        out.append(("C10 negation density",
                    f"{neg} negations = {neg_density:.0f} per 100 lines "
                    f"(consider positive 'do X' framing)", []))

    # C9 — progressive disclosure: body length (a SKILL.md only) and reference TOC.
    if kind == "skill" and body_lines > BODY_LINES_SOFT:
        out.append(("C9 body length",
                    f"body is {body_lines} lines (> {BODY_LINES_SOFT}); "
                    "move detail into references/ and link to it", []))
    if kind == "reference" and body_lines > REF_TOC_LINES and not re.search(r"(?im)^#+\s*contents\b", body):
        out.append(("C9 reference TOC",
                    f"reference is {body_lines} lines (> {REF_TOC_LINES}) with no '## Contents'", []))

    # C11 — distribution hygiene: non-Latin-script text in the description. Matches
    # script ranges (Hangul, Japanese kana, CJK, Cyrillic, Arabic), not punctuation
    # like em-dashes or curly quotes that legitimately appear in English prose.
    # Trigger keywords are EXEMPT: a skill's triggers (typically quoted in the description)
    # may be in the user's language even when it ships, because they must match how the user
    # phrases the request. Strip quoted/backticked spans first; flag only non-Latin PROSE drift.
    desc_prose = re.sub(r'"[^"]*"|\u201c[^\u201d]*\u201d|`[^`]*`', "", desc)
    nonlatin = re.findall(r"[\uac00-\ud7a3\u3040-\u30ff\u4e00-\u9fff\u0370-\u03ff\u0400-\u04ff\u0590-\u05ff\u0600-\u06ff\u0900-\u097f\u0e00-\u0e7f]+", desc_prose)
    if nonlatin:
        out.append(("C11 description language",
                    f"description carries {len(nonlatin)} non-Latin-script token(s) "
                    "(a non-Latin script) — a distributed description "
                    "should read in the consumer's language",
                    []))

    # C3 assist — world-facts the target likely does not act on. Kept narrow to
    # cost/quota language; a bare "tier" is left out because reasoning-effort and
    # model tiers are legitimate prompt content (found via dog-food on this skill).
    world = lines_matching_unquoted(body, r"\bpricing\b|\bprices?\b|\bquota\b|"
                                 r"\brate limit\b|\bbilling\b|\busage (?:cap|limit)s?\b|"
                                 r"\bsubscription\b|\bper 1M\b|\bper 1K\b|\bper token\b|"
                                 r"\bper-token\b|\bweekly limit\b", re.I)
    if world:
        add("C3 world-facts (assist)",
            f"{len(world)} line(s) mention cost/quota — confirm the target ACTS on these", world)

    # AI-authorship signature (references/ai-authorship.md AA1/AA2/AA3/AA5) — the
    # chat-register residue a model leaves when it writes a shipped instruction like a
    # chat reply. [script] candidates; the reviewer confirms (a reference file that QUOTES
    # these phrases as examples is scoping language, not a real defect).
    deixis = lines_matching_unquoted(
        body,
        r"(?i)\bas you (?:requested|asked)\b|\byou asked me to\b|\bper our (?:conversation|discussion|chat)\b|"
        r"\blike you mentioned\b|\bas we discussed\b|\b(?:the|this|that|our) \w[\w ]{0,18}\bwe (?:discussed|talked about|mentioned)\b",
    )
    if deixis:
        add("AA1 authoring-conversation carryover",
            f"{len(deixis)} line(s) point at a vanished chat — say the thing directly", deixis)
    chat = lines_matching_unquoted(
        body,
        r"(?i)\bgreat question\b|\bi'?ll help you\b|\blet me\b|\bas an ai\b|\bas a language model\b|"
        r"\bi hope this helps\b|\blet me know if\b|\bi apologi|\bsorry\b|\bi want to be careful\b|"
        r"\bhappy to help\b|\bfeel free to\b|\bof course[!,]|\bsure[!,]",
    )
    if chat:
        add("AA2 chat-register padding",
            f"{len(chat)} conversational/self-referential phrase(s) — state the task, do not converse", chat)
    softeners = lines_matching_unquoted(
        body,
        r"(?i)\byou might want to\b|\bif you'?d like\b|\bplease try to\b|\bit would be great if\b|"
        r"\bmaybe consider\b|\bperhaps you could\b|\byou could (?:maybe|perhaps)\b",
    )
    if softeners:
        add("AA3 sycophantic softeners",
            f"{len(softeners)} weak/over-polite imperative(s) — state the instruction directly", softeners)
    # emoji / decorative glyphs — astral emoji plane + misc symbols (U+2600-26FF: ⚠ ☀ etc)
    # + a curated set of ornamental dingbats (stars/flowers/fat-arrows), deliberately EXCLUDING
    # plain arrows (U+2190-21FF, e.g. →) and functional check dingbats (✓ ✗) the skill uses.
    emoji = lines_matching(body, r"[\U0001F000-\U0001FAFF☀-⛿️❖✦✧✩✪✫✬✭✮✯✰✱✲✳❀❂❊❋➤➢➣]")
    if emoji:
        add("AA5 decoration overload",
            f"{len(emoji)} line(s) with emoji/decorative glyphs — keep formatting functional", emoji)
    # AA6 — body-language: non-Latin script in the BODY (an AI authors in the chat's
    # language, not the consumer's). Quoted trigger phrases / example user-input strings are
    # EXEMPT (a skill lists the phrases that fire it, which may be in the user's language);
    # flag only unquoted PROSE. Strip BALANCED quote/backtick pairs PER LINE — the same
    # failure mode as C11's description strip: an unbalanced quote fails toward FLAGGING,
    # never toward a silent exempt (a body-start parity count would invert on a lone `"`).
    _aa6_quoted = re.compile(r'"[^"\n]*"|“[^”\n]*”|`[^`\n]*`')
    _aa6_script = re.compile(r"[가-힣぀-ヿ一-鿿Ͱ-ϿЀ-ӿ֐-׿؀-ۿऀ-ॿ฀-๿]")
    aa6 = [(i, ln.strip()) for i, ln in enumerate(body.splitlines(), 1)
           if _aa6_script.search(_aa6_quoted.sub("", ln))]
    if aa6:
        add("AA6 body language",
            f"{len(aa6)} body line(s) carry non-consumer-language script — write shipped text in the consumer's language", aa6)

    return out


def main(argv: list[str]) -> int:
    args = argv[1:]
    explicit_kind = None
    if "--kind" in args:
        i = args.index("--kind")
        explicit_kind = args[i + 1] if i + 1 < len(args) else None
        args = args[:i] + args[i + 2:]
    if not args:
        print(__doc__)
        return 2
    any_findings = False
    for arg in args:
        path = Path(arg)
        if not path.is_file():
            print(f"# {arg}: not a file — skipped")
            continue
        findings = lint(path, explicit_kind)
        label = target_kind(path, explicit_kind)
        print(f"\n# lint — {arg}  ({label})")
        if not findings:
            print("  no mechanical candidates. (Semantic criteria still need a fresh-eye reviewer.)")
            continue
        any_findings = True
        for crit, summary, locs in findings:
            loc = f"  [{', '.join(locs)}]" if locs else ""
            print(f"  - {crit}: {summary}{loc}")
    return 1 if any_findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
