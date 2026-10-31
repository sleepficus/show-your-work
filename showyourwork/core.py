"""Core checking engine for Show Your Work.

Deterministic only: no model, no network. Every verdict in the output
can be re-derived by re-running the same comparisons.
"""

import hashlib
import os
import re
from dataclasses import dataclass, field

DOCTRINE = (
    "This tool checks receipt discipline, not truth. SUPPORTED means the "
    "evidence carries the claim - not that the evidence is honest."
)

MAX_TEXT_BYTES = 1_000_000          # per-file cap for text search
MAX_FILES = 5000                    # walk cap
MAX_WEAK_NUMBER_CLAIMS = 40         # readability cap for bare numbers

FILE_EXTS = {
    "md", "txt", "py", "js", "ts", "jsx", "tsx", "json", "zip", "pdf",
    "html", "htm", "css", "csv", "yaml", "yml", "toml", "sh", "png",
    "jpg", "jpeg", "webp", "gif", "xml", "sql", "lock", "rs", "go",
    "java", "c", "cpp", "h", "rb", "php", "docx", "xlsx", "pptx",
}

NUM = r"(?:\d{1,3}(?:,\d{3})+|\d+)"
RE_SHA256 = re.compile(r"\b[0-9a-fA-F]{64}\b")
RE_SHA1 = re.compile(r"\b[0-9a-fA-F]{40}\b")
RE_FILETOKEN = re.compile(
    r"(?<![\w/.:-])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.([A-Za-z0-9]{1,6}))(?![\w-]|\.\w)")
RE_COUNT = re.compile(
    r"\b(" + NUM + r")\s*(files?|tests?|checks?|pages?|entries|items|verdicts?|records?)\b",
    re.IGNORECASE)
RE_PERCENT = re.compile(r"\b(" + NUM + r"(?:\.\d+)?)%")
RE_NUMBER = re.compile(r"\b" + NUM + r"(?:\.\d+){0,3}\b")
RE_SUCCESS = re.compile(
    r"\b(all\s+)?(tests?|checks?|suites?)\s+(pass|passed|passing)\b"
    r"|\beverything\s+(passed|passes)\b|\bclean\s+pass\b"
    r"|\b0\s+(failures?|failed|errors?)\b|\bno\s+failures?\b",
    re.IGNORECASE)
# A report ADMITTING failure, in any ordinary phrasing, must never be
# graded as asserting a clean pass (audit F1: "3 tests failed;
# remaining tests passed" is a truthful report, not a success claim).
ADMISSION_PATTERNS = [
    re.compile(r"\b([1-9]\d*)\s+(?:tests?\s+|checks?\s+)?(failed|failures?|errors?)\b",
               re.IGNORECASE),
    re.compile(r"\b(tests?|checks?)\s+(failed|failing)\b", re.IGNORECASE),
    re.compile(r"\b(failures?|errors?|failed)\s*[:=]\s*([1-9]\d*)", re.IGNORECASE),
    re.compile(r"\b([1-9]\d*)\s+of\s+\d+\s+(failed|did not pass)\b", re.IGNORECASE),
    re.compile(r"\bnot all\b[^.\n]{0,40}\b(pass|passed)\b", re.IGNORECASE),
    re.compile(r"\bdid not pass\b", re.IGNORECASE),
    re.compile(r"\bfailing\s+(tests?|checks?)\b", re.IGNORECASE),
]
RE_MARK_FAIL_STRONG = [
    re.compile(r"FAILED\s*\(failures=\d+\)"),
    re.compile(r"Traceback \(most recent call last\)"),
    re.compile(r"(\d+)\s+failed,\s*\d+\s+passed"),
    re.compile(r"=+\s*(\d+)\s+failed\b"),
    re.compile(r"(?m)^FAILED\s+\S+"),            # pytest short summary
    re.compile(r"(?m)^ERROR\s+\S+::\S+"),        # pytest error summary
    re.compile(r"(?m)^ERROR:\s+\S+"),            # unittest error header
]
RE_MARK_PASS = [
    re.compile(r"Ran\s+\d+\s+tests?[\s\S]{0,60}?\bOK\b"),
    re.compile(r"\b\d+\s+passed\b"),
]


def _int_value(tok):
    return int(float(tok.replace(",", "")))


@dataclass
class EvidenceFile:
    rel: str
    size: int
    sha256: str
    sha1: str
    text: str = ""            # capped, lossy-decoded; "" for binary/large


@dataclass
class Evidence:
    root: str
    files: list = field(default_factory=list)
    files_skipped: int = 0
    walk_capped: bool = False
    text_unsearched: list = field(default_factory=list)   # too large / binary

    @property
    def by_basename(self):
        out = {}
        for f in self.files:
            out.setdefault(os.path.basename(f.rel), []).append(f)
        return out

    def find_file(self, token):
        """Find an evidence file matching a report token (rel path,
        path suffix, or basename). Returns the EvidenceFile or None."""
        token = token.strip().lstrip("./")
        for f in self.files:
            if f.rel == token or f.rel.endswith("/" + token):
                return f
        base = os.path.basename(token)
        hits = self.by_basename.get(base, [])
        return hits[0] if hits else None

    def search_text(self, needle):
        """Return the rel path of the first file whose text contains
        needle, else None."""
        for f in self.files:
            if f.text and needle in f.text:
                return f.rel
        return None

    def search_text_ci(self, needle):
        """Case-insensitive substring search (hashes get printed in
        either case; a case mismatch must not manufacture a
        contradiction). Returns the rel path of the first hit."""
        low = needle.lower()
        for f in self.files:
            if f.text and low in f.text.lower():
                return f.rel
        return None

    def search_number(self, plain):
        """Boundary-aware search for a bare number (digits, no commas):
        '3' must not match inside 'python3', '30', or '0.412'.
        Returns the rel path of the first hit, else None."""
        pat = re.compile(r"(?<![\w.,])" + re.escape(plain) + r"(?![\w.,])")
        for f in self.files:
            if f.text and pat.search(f.text):
                return f.rel
        return None


def load_evidence(path):
    ev = Evidence(root=str(path))
    paths = []
    if os.path.isfile(path):
        paths = [(path, os.path.basename(path))]
    else:
        for dirpath, _dirs, names in os.walk(path):
            for name in sorted(names):
                ap = os.path.join(dirpath, name)
                rel = os.path.relpath(ap, path)
                paths.append((ap, rel))
                if len(paths) >= MAX_FILES:
                    ev.walk_capped = True
                    break
            if ev.walk_capped:
                break
    for ap, rel in paths:
        try:
            h256 = hashlib.sha256()
            h1 = hashlib.sha1()
            size = 0
            with open(ap, "rb") as fh:
                while True:
                    chunk = fh.read(65536)
                    if not chunk:
                        break
                    size += len(chunk)
                    h256.update(chunk)
                    h1.update(chunk)
            text = ""
            if size <= MAX_TEXT_BYTES:
                with open(ap, "rb") as fh:
                    raw = fh.read()
                if b"\x00" not in raw:
                    text = raw.decode("utf-8", errors="replace")
                else:
                    ev.text_unsearched.append(rel.replace(os.sep, "/"))
            elif size > 0:
                ev.text_unsearched.append(rel.replace(os.sep, "/"))
            ev.files.append(EvidenceFile(
                rel=rel.replace(os.sep, "/"), size=size,
                sha256=h256.hexdigest(), sha1=h1.hexdigest(), text=text))
        except OSError:
            ev.files_skipped += 1
    return ev


@dataclass
class Claim:
    kind: str
    claim: str
    verdict: str              # SUPPORTED | CONTRADICTED | UNVERIFIABLE
    reason: str


def check_report(report_text, ev):
    claims = []
    consumed_hashes = set()   # lowercased hashes already claimed via pairs
    consumed_files = set()    # file tokens already claimed via pairs

    # --- 1. file<->hash pairs stated in the report ---------------------
    # A pair = a hash whose line carries a file token shortly before it
    # (prose like "- exporter.zip - the release, SHA-256: ab12..." counts).
    for line in report_text.splitlines():
        for hm in RE_SHA256.finditer(line):
            window = line[max(0, hm.start() - 80):hm.start()]
            tokens = list(RE_FILETOKEN.finditer(window))
            distinct = {t.group(1) for t in tokens}
            if len(distinct) != 1:
                # Zero tokens: not a pair. Two or more: ambiguous -
                # never state a pair the report didn't (audit F4).
                # The hash still grades on its own in pass 2.
                continue
            fname = tokens[-1].group(1)
            hx = hm.group(0).lower()
            consumed_hashes.add(hx)
            consumed_files.add(fname)
            f = ev.find_file(fname)
            if f is None:
                claims.append(Claim("hash-pair", f"{fname} = {hx[:12]}...",
                                    "CONTRADICTED",
                                    "the pair names a file absent from the evidence"))
            elif f.sha256.lower() == hx:
                claims.append(Claim("hash-pair", f"{fname} = {hx[:12]}...",
                                    "SUPPORTED", f"SHA-256 matches {f.rel}"))
            else:
                claims.append(Claim("hash-pair", f"{fname} = {hx[:12]}...",
                                    "CONTRADICTED",
                                    f"actual SHA-256 of {f.rel} is {f.sha256[:12]}..."))

    # --- 2. bare SHA-256 claims ---------------------------------------
    sha256_values = {f.sha256.lower(): f.rel for f in ev.files}
    for m in RE_SHA256.finditer(report_text):
        hx = m.group(0).lower()
        if hx in consumed_hashes:
            continue
        consumed_hashes.add(hx)
        if hx in sha256_values:
            claims.append(Claim("hash", f"SHA-256 {hx[:12]}...", "SUPPORTED",
                                f"matches evidence file {sha256_values[hx]}"))
        elif ev.search_text_ci(hx):
            claims.append(Claim("hash", f"SHA-256 {hx[:12]}...", "SUPPORTED",
                                "the hash appears in the evidence text"))
        else:
            claims.append(Claim("hash", f"SHA-256 {hx[:12]}...", "CONTRADICTED",
                                "matches no evidence file and appears in no evidence text"))

    # --- 3. bare 40-hex (git-style) claims -----------------------------
    sha1_values = {f.sha1.lower(): f.rel for f in ev.files}
    for m in RE_SHA1.finditer(report_text):
        start = m.start()
        if start > 0 and report_text[start - 1] in "0123456789abcdefABCDEF":
            continue                      # tail of a longer hex string
        hx = m.group(0).lower()
        if hx in sha1_values:
            claims.append(Claim("hash", f"SHA-1 {hx[:12]}...", "SUPPORTED",
                                f"matches evidence file {sha1_values[hx]}"))
        elif ev.search_text_ci(hx):
            claims.append(Claim("hash", f"hash {hx[:12]}...", "SUPPORTED",
                                "the hash appears in the evidence text"))
        else:
            claims.append(Claim("hash", f"hash {hx[:12]}...", "UNVERIFIABLE",
                                "git-style hashes cannot be recomputed from files alone"))

    # --- 4. file claims -------------------------------------------------
    seen_tokens = set()
    for m in RE_FILETOKEN.finditer(report_text):
        token, ext = m.group(1), m.group(2).lower()
        if token in seen_tokens or token in consumed_files:
            continue
        if ext not in FILE_EXTS and "/" not in token:
            continue
        if token[0].isdigit() or ".." in token:
            continue
        seen_tokens.add(token)
        f = ev.find_file(token)
        if f is not None:
            claims.append(Claim("file", token, "SUPPORTED",
                                f"found in the evidence as {f.rel}"))
        else:
            claims.append(Claim("file", token, "CONTRADICTED",
                                "named in the report, absent from the evidence"))

    # Hash spans are masked out of the count/number passes: digits inside
    # a hash are not numbers, and the "256" in the label "SHA-256" is not
    # a claim either.
    hash_spans = [m.span() for m in RE_SHA256.finditer(report_text)]
    hash_spans += [m.span() for m in RE_SHA1.finditer(report_text)]
    hash_spans += [m.span() for m in re.finditer(
        r"\bSHA-?256\b|\bSHA-?1\b|\bMD5\b", report_text, re.IGNORECASE)]

    def _in_hash(span):
        return any(s <= span[0] and span[1] <= e for s, e in hash_spans)

    # --- 5. count claims ------------------------------------------------
    for m in RE_COUNT.finditer(report_text):
        if _in_hash(m.span()):
            continue
        n = _int_value(m.group(1))
        noun = m.group(2).lower()
        label = f"{m.group(1)} {m.group(2)}"
        if noun.startswith("file"):
            actual = len(ev.files)
            if n == actual:
                claims.append(Claim("count", label, "SUPPORTED",
                                    f"the evidence contains exactly {actual} files"))
            else:
                claims.append(Claim("count", label, "CONTRADICTED",
                                    f"the evidence contains {actual} files"))
        elif noun.startswith(("test", "check")):
            bases = set()
            for f in ev.files:
                if not f.text:
                    continue
                # Bases must be anchored in test-shaped text (audit F3:
                # a bare "500 passed" in prose - "500 passed the
                # entrance exam" - is not a test total).
                for pat in (r"Ran\s+(" + NUM + r")\s+tests?",
                            r"(" + NUM + r")\s+tests?\s*[:,]?\s*(?:passed|pass|OK)\b",
                            r"(" + NUM + r")\s*/\s*" + NUM,
                            r"={1,}[^=\n]*?\b(" + NUM + r")\s+passed\b",
                            r"\b(" + NUM + r")\s+passed\s+in\s+[\d.]+\s*s\b"):
                    for mm in re.finditer(pat, f.text, re.IGNORECASE):
                        bases.add(_int_value(mm.group(1)))
            if n in bases:
                claims.append(Claim("count", label, "SUPPORTED",
                                    "matches a test total in the evidence text"))
            elif bases:
                claims.append(Claim("count", label, "CONTRADICTED",
                                    f"test totals in the evidence are {sorted(bases)}"))
            else:
                claims.append(Claim("count", label, "UNVERIFIABLE",
                                    "no test totals found in the evidence"))
        else:
            hit = ev.search_text(m.group(0))
            if not hit and n >= 1000:
                hit = ev.search_text(f"{n:,} {m.group(2)}")
            if hit:
                claims.append(Claim("count", label, "SUPPORTED",
                                    f"the same count appears in {hit}"))
            else:
                claims.append(Claim("count", label, "UNVERIFIABLE",
                                    f"no basis for this count in the evidence"))

    # --- 6. success claims vs failure markers ---------------------------
    fail_admitted = any(p.search(report_text) for p in ADMISSION_PATTERNS)
    if RE_SUCCESS.search(report_text) and not fail_admitted:
        marker = None
        for f in ev.files:
            if not f.text:
                continue
            for pat in RE_MARK_FAIL_STRONG:
                mm = pat.search(f.text)
                if mm:
                    marker = (f.rel, mm.group(0))
                    break
            if marker:
                break
        if marker:
            claims.append(Claim("success", "report asserts a clean pass",
                                "CONTRADICTED",
                                f"evidence file {marker[0]} carries a failure marker: {marker[1]!r}"))
        elif any(p.search(f.text or "") for f in ev.files for p in RE_MARK_PASS):
            claims.append(Claim("success", "report asserts a clean pass",
                                "SUPPORTED",
                                "pass markers present in the evidence, no failure markers"))
        else:
            claims.append(Claim("success", "report asserts a clean pass",
                                "UNVERIFIABLE",
                                "no pass or failure markers found in the evidence"))

    # --- 7. bare numbers and percentages (weak claims) ------------------
    counted_numbers = set()
    for m in RE_COUNT.finditer(report_text):
        if not _in_hash(m.span()):
            counted_numbers.add(m.group(1))
    seen_numbers = set()
    weak = 0
    for m in list(RE_PERCENT.finditer(report_text)) + list(RE_NUMBER.finditer(report_text)):
        if _in_hash(m.span()):
            continue
        tok = m.group(1) if m.re is RE_PERCENT else m.group(0)
        plain = tok.replace(",", "")
        if tok in counted_numbers or plain in seen_numbers:
            continue
        if len(plain) >= 40:                       # part of a hash token
            continue
        seen_numbers.add(plain)
        if weak >= MAX_WEAK_NUMBER_CLAIMS:
            claims.append(Claim("number", "...", "UNVERIFIABLE",
                                f"further bare numbers not listed (cap {MAX_WEAK_NUMBER_CLAIMS})"))
            break
        weak += 1
        hit = ev.search_number(plain)
        if not hit and plain.isdigit():
            comma_form = f"{int(plain):,}"
            if comma_form != plain:
                hit = ev.search_number(comma_form)
        label = (tok + "%") if m.re is RE_PERCENT else tok
        if hit:
            claims.append(Claim("number", label, "SUPPORTED",
                                f"appears in the evidence text ({hit})"))
        else:
            claims.append(Claim("number", label, "UNVERIFIABLE",
                                "does not appear in the evidence text"))

    return claims


def run_check(report_path, evidence_path):
    with open(report_path, "r", encoding="utf-8", errors="replace") as fh:
        report_text = fh.read()
    ev = load_evidence(evidence_path)
    # A report sitting inside its own evidence tree must not grade
    # itself (audit F6): exclude it and say so in the limits.
    report_abs = os.path.abspath(report_path)
    kept = []
    excluded_report = False
    for f in ev.files:
        f_abs = os.path.abspath(os.path.join(ev.root, f.rel)) \
            if not os.path.isfile(ev.root) else os.path.abspath(ev.root)
        if f_abs == report_abs:
            excluded_report = True
            continue
        kept.append(f)
    ev.files = kept
    claims = check_report(report_text, ev)
    summary = {"SUPPORTED": 0, "CONTRADICTED": 0, "UNVERIFIABLE": 0}
    for c in claims:
        summary[c.verdict] += 1
    from . import __version__
    result = {
        "tool": "show-your-work",
        "version": __version__,
        "report": str(report_path),
        "evidence": str(evidence_path),
        "evidence_files": len(ev.files),
        "summary": {**summary, "total": len(claims)},
        "claims": [
            {"kind": c.kind, "claim": c.claim, "verdict": c.verdict,
             "reason": c.reason} for c in claims
        ],
        "limits": {
            "files_skipped_unreadable": ev.files_skipped,
            "walk_capped": ev.walk_capped,
            "text_search_cap_bytes_per_file": MAX_TEXT_BYTES,
            "files_not_text_searched": ev.text_unsearched[:20],
            "files_not_text_searched_count": len(ev.text_unsearched),
            "report_excluded_from_evidence": excluded_report,
        },
        "doctrine": DOCTRINE,
    }
    exit_code = 1 if summary["CONTRADICTED"] else 0
    return result, exit_code


def render_text(result):
    lines = []
    lines.append(f"Show Your Work - receipt check")
    lines.append(f"report:   {result['report']}")
    lines.append(f"evidence: {result['evidence']} ({result['evidence_files']} files)")
    lines.append("")
    mark = {"SUPPORTED": "[ SUPPORTED ]", "CONTRADICTED": "[ CONTRADICTED ]",
            "UNVERIFIABLE": "[ UNVERIFIABLE ]"}
    for c in result["claims"]:
        lines.append(f"{mark[c['verdict']]:17} {c['claim']}")
        lines.append(f"{'':17} -> {c['reason']}")
    s = result["summary"]
    lines.append("")
    lines.append(f"summary: {s['SUPPORTED']} supported / {s['CONTRADICTED']} contradicted / "
                 f"{s['UNVERIFIABLE']} unverifiable (of {s['total']} claims)")
    if s["total"] == 0:
        lines.append("verdict: no checkable claims found in the report")
    elif s["CONTRADICTED"]:
        lines.append("verdict: the evidence contradicts the report")
    elif s["UNVERIFIABLE"]:
        lines.append("verdict: no contradictions - but not everything could be checked")
    else:
        lines.append("verdict: every checkable claim is supported by the evidence")
    lines.append("")
    lines.append(DOCTRINE)
    return "\n".join(lines)
