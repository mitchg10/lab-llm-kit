"""Identifier scanner.

A deliberately cautious, rule-based check for identifiers, run before any text
goes to a model. It never calls a model: under the lab constitution, text that
might contain identifiers must not reach a model at all.

It flags *possible* identifiers. False positives are expected. Handle them with
`ignore=` (a finding kind) or an allow-list of terms (for example, your
pseudonyms). It cannot catch everything, and indirect identifiers ("the only
woman in section 2") in particular need a human read-through. Passing this scan
is necessary, not sufficient.
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

PATTERNS: dict[str, re.Pattern] = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"(?<![\w-])(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b"),
    # Cornell NetIDs look like "abc123". Common tech tokens (gpt4, mp3, utf8…) are excluded.
    "netid": re.compile(r"(?<![\w@./-])(?!(?:gpt|mp|utf|sha|md|ipv|llm|api|web|gen|win|os|ios|py|h)\d)[a-z]{2,3}\d{1,5}(?![\w@-])"),
    "student_id": re.compile(r"(?<![\w.-])\d{7,9}(?![\w-]|\.\d)"),
    "date": re.compile(
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-](?:19|20)?\d{2}"
        r"|(?:19|20)\d{2}-\d{2}-\d{2}"
        r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+(?:19|20)\d{2}"
        r"|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(?:19|20)\d{2})\b"
    ),
    "street_address": re.compile(
        r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s){1,3}(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|"
        r"Boulevard|Blvd|Court|Ct|Way|Place|Pl|Terrace|Circle|Cir)\b\.?"
    ),
    "zip_code": re.compile(r"\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b"),
    "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "profile_url": re.compile(
        r"\b(?:https?://)?(?:www\.)?(?:linkedin\.com/in|github\.com|twitter\.com|x\.com|instagram\.com|"
        r"facebook\.com|tiktok\.com/@|orcid\.org)/[A-Za-z0-9_.-]+", re.I
    ),
    "social_handle": re.compile(r"(?<![\w.@])@[A-Za-z0-9_]{3,}\b(?!\.[A-Za-z])"),
    "titled_name": re.compile(r"\b(?:Dr|Prof|Professor|Mr|Mrs|Ms|Mx|Dean)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?"),
    "speaker_name": re.compile(r"^\s*[A-Z][a-z]+(?:\s+[A-Z][a-z'-]+)+\s*(?:\(\d|:)", re.M),
}

DESCRIPTIONS = {
    "email": "email address",
    "ssn": "Social Security number",
    "phone": "phone number",
    "netid": "possible NetID",
    "student_id": "possible student/employee ID (7–9 digits)",
    "date": "full date (possible birth or event date)",
    "street_address": "street address",
    "zip_code": "state + ZIP code",
    "ip_address": "IP address",
    "profile_url": "personal profile URL",
    "social_handle": "social-media handle",
    "titled_name": "title + name (e.g. 'Dr. Smith')",
    "speaker_name": "transcript speaker label that looks like a real name",
    "listed_name": "name from your names list",
}


@dataclass
class Finding:
    kind: str
    line: int
    col: int
    masked: str
    source: str = ""

    def __str__(self) -> str:
        where = f"{self.source}:" if self.source else ""
        return f"{where}{self.line}:{self.col}  {DESCRIPTIONS.get(self.kind, self.kind):<46} {self.masked}"


def mask(s: str) -> str:
    s = s.strip()
    if len(s) <= 2:
        return "*" * len(s)
    return f"{s[0]}{'*' * (len(s) - 2)}{s[-1]}  ({len(s)} chars)"


def load_terms(path: str | Path | None) -> list[str]:
    if not path:
        return []
    return [t.strip() for t in Path(path).read_text(encoding="utf-8").splitlines()
            if t.strip() and not t.lstrip().startswith("#")]


def scan_text(text: str, *, names: list[str] | None = None, allow: list[str] | None = None,
              ignore: list[str] | tuple[str, ...] = (), source: str = "") -> list[Finding]:
    """Return possible identifiers in `text`.

    names  real names (e.g. a roster or interview list) to look for, case-insensitive.
           Keep that list OFF this machine when you can, or delete it afterwards.
    allow  terms that are fine (pseudonyms, public figures, course names).
    ignore finding kinds to skip, e.g. ["date"].
    """
    allow_l = {a.lower() for a in (allow or [])}
    found: list[Finding] = []
    line_starts = [0] + [m.end() for m in re.finditer(r"\n", text)]

    def pos(i: int) -> tuple[int, int]:
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= i:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1, i - line_starts[lo] + 1

    def add(kind: str, m: re.Match):
        hit = m.group(0).strip()
        if hit.lower() in allow_l or any(a in hit.lower() for a in allow_l if len(a) > 3):
            return
        ln, col = pos(m.start())
        found.append(Finding(kind, ln, col, mask(hit), source))

    for kind, pat in PATTERNS.items():
        if kind in ignore:
            continue
        for m in pat.finditer(text):
            if kind == "speaker_name":
                label = m.group(0).split("(")[0].split(":")[0].strip()
                if label.lower() in allow_l or re.match(r"(?i)(participant|interviewer|speaker|student|p\d)", label):
                    continue
            add(kind, m)

    if names and "listed_name" not in ignore:
        for n in names:
            for m in re.finditer(r"(?<!\w)" + re.escape(n) + r"(?!\w)", text, re.I):
                add("listed_name", m)

    found.sort(key=lambda f: (f.line, f.col))
    return found


def read_text_file(path: str | Path) -> str:
    """Read .txt/.md/.csv/.json/.vtt/.srt and similar as UTF-8; .docx via its XML (no extra deps)."""
    p = Path(path)
    if p.suffix.lower() == ".docx":
        with zipfile.ZipFile(p) as z:
            xml = z.read("word/document.xml").decode("utf-8", "replace")
        xml = re.sub(r"</w:p>", "\n", xml)
        xml = re.sub(r"<w:tab/>", "\t", xml)
        return re.sub(r"<[^>]+>", "", xml)
    if p.suffix.lower() in (".pdf", ".xlsx", ".doc", ".pptx"):
        raise ValueError(f"{p.name}: convert to text first (e.g. save as .txt or .csv)")
    return p.read_text(encoding="utf-8", errors="replace")


class IdentifierError(ValueError):
    """Raised when text bound for a model contains possible identifiers."""

    def __init__(self, findings: list[Finding]):
        self.findings = findings
        kinds = sorted({f.kind for f in findings})
        lines = "\n".join(f"  {f}" for f in findings[:15])
        more = f"\n  … and {len(findings) - 15} more" if len(findings) > 15 else ""
        super().__init__(
            f"Not sent: {len(findings)} possible identifier(s) found ({', '.join(kinds)}).\n{lines}{more}\n"
            "De-identify the text first (lab constitution §1–2). If these are false positives, pass "
            "ignore=[kinds] or allow=[terms] — never turn the check off for real participant data."
        )
