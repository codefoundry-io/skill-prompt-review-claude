#!/usr/bin/env python3
"""Deterministic lint for skill-prompt-review.

Runs the mechanical checks from references/common.md against a SKILL.md or a
prompt file and prints CANDIDATE findings. It does not judge: the semantic
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
    if not re.search(r"(?m)^description:[ \t]*\S", fm):
        return "frontmatter has no 'description' field \u2014 will not register"
    m = re.search(r"(?m)^name:[ \t]*[\"']?([\w-]+)", fm)  # first token; ignores a trailing # comment / quotes
    folder = path.resolve().parent.name
    if m and folder:
        name_val = m.group(1)
        if name_val != folder:
            return f"name '{name_val}' != containing directory '{folder}' (case-sensitive) \u2014 will not load"
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

    # C8 — time-stamped facts: dates, pinned versions, and pinned model names.
    dates = lines_matching(body, r"\b20\d{2}[-/]\d{2}[-/]\d{2}\b|\(20\d{2}[-)]|"
                                 r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+20\d{2}\b")
    if dates:
        add("C8 time-stamped facts", f"{len(dates)} hardcoded date(s) in the body", dates)
    # Three-part semver, but not any octet of a 4-part IP (192.168.1.1): the left
    # guard blocks a preceding octet, the lookahead blocks a trailing one.
    versions = lines_matching(body, r"(?<![\w.])v?\d+\.\d+\.\d+\b(?!\.\d)")
    if versions:
        add("C8 version pins", f"{len(versions)} pinned version number(s)", versions)
    # Two-part MODEL pins with a family prefix (gpt-5.6, gpt-4o, claude 4.8,
    # gemini-3.1-pro, opus/sonnet/haiku N.N) plus known codenames. The letter tail
    # catches suffixed names like gpt-4o. A bare "o3"/"o4-mini" is NOT matched here:
    # `o\d` also hits section labels (O1) and ordinary text, so the reviewer judges
    # a bare o-series name (C8 [judge]).
    modelpins = lines_matching(
        body,
        r"(?i)\b(?:gpt|claude|gemini|opus|sonnet|haiku|codex|fable|mythos)[-\s]?\d+(?:\.\d+)?[a-z0-9-]*\b|"
        r"\b(?-i:Sol|Terra|Luna|Fable|Mythos)\b",
    )
    if modelpins:
        add("C8 model pins", f"{len(modelpins)} pinned model name/version — phrase around the moving target", modelpins)
    # A bare "new"/"recent"/"preview" is not checked here: it fires on ordinary prose
    # ("recent models", "a new column") and only matters when it pins a moving fact,
    # which is a judgment the reviewer makes (C8 [judge]), not a keyword count.

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
    excuses = lines_matching(body, r"are\s+NEVER\s+valid|not\s+(?:a\s+)?valid\s+reason", re.I)
    if excuses:
        add("C4 enumerated excuses", f"{len(excuses)} line(s) framing rationalizations to avoid", excuses)
    narratives = lines_matching(body, r"\(origin:|historical reason|reason for the ban", re.I)
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
    nonlatin = re.findall(r"[\uac00-\ud7a3\u3040-\u30ff\u4e00-\u9fff\u0370-\u03ff\u0400-\u04ff\u0590-\u05ff\u0600-\u06ff\u0900-\u097f\u0e00-\u0e7f]+", desc)
    if nonlatin:
        out.append(("C11 description language",
                    f"description carries {len(nonlatin)} non-Latin-script token(s) "
                    "(a non-Latin script) — a distributed description "
                    "should read in the consumer's language",
                    []))

    # C3 assist — world-facts the target likely does not act on. Kept narrow to
    # cost/quota language; a bare "tier" is left out because reasoning-effort and
    # model tiers are legitimate prompt content (found via dog-food on this skill).
    world = lines_matching(body, r"\bpricing\b|\bquota\b|\brate limit\b|\bbilling\b|"
                                 r"\bsubscription\b|\bper 1M\b|\bper 1K\b|\bper token\b|"
                                 r"\bper-token\b|\bweekly limit\b", re.I)
    if world:
        add("C3 world-facts (assist)",
            f"{len(world)} line(s) mention cost/quota — confirm the target ACTS on these", world)

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
