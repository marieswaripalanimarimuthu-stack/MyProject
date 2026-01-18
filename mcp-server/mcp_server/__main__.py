import json
import os
import time
import subprocess
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
from base64 import b64encode
import ssl
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional, List
import socket
try:
    import pdfplumber  # for parsing tables from PDFs
except Exception:
    pdfplumber = None
try:
    import oracledb
except Exception:
    oracledb = None

HOST = "127.0.0.1"
PORT = 8765

JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")
JIRA_USERNAME = os.environ.get("JIRA_USERNAME", "")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_MOCK = os.environ.get("JIRA_MOCK", "0") == "1"
JIRA_API_VERSION = os.environ.get("JIRA_API_VERSION", "3")
JIRA_AUTH_MODE = (os.environ.get("JIRA_AUTH_MODE", "basic") or "basic").strip().lower()
JIRA_BEARER_TOKEN = os.environ.get("JIRA_BEARER_TOKEN", "")
JIRA_COOKIE = os.environ.get("JIRA_COOKIE", "_ga=GA1.1.850250016.1767583299; s_fid=7C40FA7C79074A46-1AB898CC4F677EA4; s_cc=true; s_vi=[CS]v1|34AD972CA0A88857-4000159A60452055[CE]; JiraSDSamlssoLoginV2=s288ae1ab5b8545d4bf01c79c7a105d9354f976936%23%23%23v776133%23%23%23VZIDP_21773_CELV_JIRA%23%23%237P2QJTC2RNG6VW2; JSESSIONID=2AE839050726589FB099A2982B0C6302; atlassian.xsrf.token=BY2O-5KM7-5RKV-Q03A_401f3990b94591e66c914c4e9f072e67638e489e_lin; _ga_71R7QHH04M=GS2.1.s1767585751$o2$g0$t1767585751$j60$l0$h0; SMSESSION=2QRi1HuoL5zzY3I3vx1g1A8pt6q3Vvj0OCbfZMyoUr2R8Zmo9MnkW5mfSRnNlHOMwHOwPRmU/SlqoP/Suwoz2KEDI33tPXSSaTTEq2W2qpYK8yad5dQ7L+5F2oR5Lka1s+NVPon8qhQmQEdPTQAxxwIlZR6Zs4OwfzF9SAQeqNiEXwZGK/WjV0ibJvEWIP16Ao4sv0DoL4/L33ihO86Qy6eJXPzHcUimcA0ZzuQOTj6CYwcKx9gdhHOvRAuBPGy4mczKZ/1oaQXq20OIv+XrTRYroBV9EH8ANYSUXelas42GqRCYk0154yjd3wfilEyPVizHacd/hSmR+Jsl5viRsV2EjxkANCw7BFeyc+DcKszqeq/oFMMYWXI+UZqSNGLJbR2be51RxdT+1ZcswJqJ2UqB+QdENeVt99o7zJwbgbYKwVyPBfrj8HtwFe4jOKUkkrlqSVtArq/PY8kH2h6ve2fF9QFJevzlIRhUSHAnqqpdXaQKYMkB4c7BLAXyh3wT81itAX/AxywUqsWTtWlPjl6SdvBx+WdjDrAOPZuEBn76SSdcJkt3WiuvK9wXkeEPv6lM/m6sjjDBezbZuViOpHcYU4cpy+zwZPCCl8DEgghZtnjS/6LqQkVZbRqelf3HPphbkiAeUBTMsNUa3XhLnYhQcO7KaI01q8QKJlwOc8Ott5GqcHB1+6tN183LBluDVeo34Y9k4DsNL3pgWOuEjRNXdiimxUmZv380zZidZd+FTR1Fq66Er51NBPAW5VhRhooloK8uQ9EdgQElERcNS9+qZ4rAl94Yq1Guu4U88dRR2hc5z+PAQGk+AbZUBei/YQDqXjEb2FT2fdfgcmu52lnTyRLGXiQNgx4eA7n0UO/5eSSqZSlG8I3cFr5jS9IymdeeeKy+umyutQeC1h2MVFLWjoorVYbsrmB+68zL9hQIC6EHhJl6jBUesjnT1hCwM/XTuHLzjejeprc7aqlvZFhSNN6hb2yXaErsFtg52rB9lZilWAJB+T3nzqSr0aZwddNY0b/9PuAKUhov/rbqgzlTQ9LoHX42hNlg0pGNcu3DmhAzip4Iv72/hkgENJgl+r5/9d+NKxlCq1NDMtFn6XmDWHAeCjEGiSNp1Pq02K62lgiUjwY9NNFaR+3bhR21EuRgQ4PvTjJlln+dp2Eo2EvgysRDetU0xqp4qtZ70HDyj/63p7YUY83qpWILJc15CHs/DObCQ3Bb90tHy0gR56R8jGU/28Uks+5c86fus4zgZ3vESpMnzwV3saWkt/pHlK/5iIuI4zOhBW/8VFOb0wFIrqjqPZ10RdnkiSGCiT2C9srrLIm2qnklIrydI7vg; SSOPRDSESSION=iy0x5GNHDFjYah51uw4jwDaQIAo.*AAJTSQACMDIAAlNLABwycGEvSDFzVFo2RlVRYmZzQzZQNC92NlU0enM9AAR0eXBlAANDVFMAAlMxAAI0Mw..*; SSOPRDLB=tpa124; AWSALB=VNzuguZz+B18L9KV1nYNiYSvXBoubrFkRWwbl14r6QbLut5+itwPrtQOgQR0eA9/Ap6jKd7PU2mll/LG0zvwjzP3ttKRlml73idWYeLF/Cn0pfgXIZVIxSEX1n2R; AWSALBCORS=VNzuguZz+B18L9KV1nYNiYSvXBoubrFkRWwbl14r6QbLut5+itwPrtQOgQR0eA9/Ap6jKd7PU2mll/LG0zvwjzP3ttKRlml73idWYeLF/Cn0pfgXIZVIxSEX1n2R")

# Confluence configuration (optional)
CONFLUENCE_BASE_URL = os.environ.get("CONFLUENCE_BASE_URL", "")
CONFLUENCE_USERNAME = os.environ.get("CONFLUENCE_USERNAME", os.environ.get("CONFLUENCE_EMAIL", ""))
CONFLUENCE_TOKEN = os.environ.get("CONFLUENCE_TOKEN", "")
CONFLUENCE_DEFAULT_SPACES = [s.strip() for s in (os.environ.get("CONFLUENCE_SPACE_KEYS", "").split(",")) if s.strip()]
# Release Plan configuration
RELEASE_PLAN_URL = os.environ.get("RELEASE_PLAN_URL", "https://releaseplan.ebiz.verizon.com/")

# Release Plan configuration
                    # Convert params keys to str and pass as dict for named binds
# Oracle configuration (optional, for Queue Snapshot and status lookup)
ORACLE_DSN = os.environ.get("ORACLE_DSN", os.environ.get("ORACLE_CONNECT_STRING", ""))
ORACLE_USER = os.environ.get("ORACLE_USER", "")
ORACLE_PASSWORD = os.environ.get("ORACLE_PASSWORD", "")

# Resolve path to UI (serve static index.html from mcp-client/ui)
# __file__ = .../mcp-server/mcp_server/__main__.py
# Go up three levels to reach workspace root (JiraAgent/)
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# UI likely at JiraAgent/mcp-client/ui/index.html
UI_INDEX_PATH = os.path.join(WORKSPACE_ROOT, "mcp-client", "ui", "index.html")
UI_QUEUE_SNAPSHOT_PATH = os.path.join(WORKSPACE_ROOT, "mcp-client", "ui", "queue_snapshot.html")
UI_ORDER_VALIDATION_PATH = os.path.join(WORKSPACE_ROOT, "mcp-client", "ui", "order_validation.html")
UI_HEALTHCHECK_PATH = os.path.join(WORKSPACE_ROOT, "mcp-client", "ui", "healthcheck.html")

def _fetch_binary(url: str) -> bytes:
    """Fetch binary content from a URL with browser-like headers and optional cookie."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
    req.add_header("Accept", "*/*")
    req.add_header("Accept-Language", "en-US,en;q=0.9")
    cookie = os.environ.get("RELEASE_PLAN_COOKIE", "").strip()
    if cookie:
        req.add_header("Cookie", cookie)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        return resp.read()

def parse_vcg_milestones_pdf(pdf_bytes: bytes) -> List[dict]:
    """Extract rows with columns Deployment, Go Live Date, Clarity Release / Jira Fix Version.
    Returns list of dicts: {deployment, go_live_date, release_version}.
    """
    if not pdfplumber:
        raise RuntimeError("pdfplumber is not installed. Run: pip install -r mcp-server/requirements.txt")
    import io
    def norm(s):
        return (str(s or "").lower().replace(" ", "").replace("-", "").strip())
    def safe(row, idx):
        try:
            return row[idx]
        except Exception:
            return ""
    rows = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            try:
                tables = page.extract_tables() or []
            except Exception:
                tables = []
            for tbl in tables:
                if not tbl or not tbl[0]:
                    continue
                headers = [h if h is not None else "" for h in tbl[0]]
                nh = [norm(h) for h in headers]
                # Find column indices with flexible matches
                def find_idx(options):
                    for i, h in enumerate(nh):
                        for opt in options:
                            if opt in h:
                                return i
                    return -1
                i_dep = find_idx(["deployment"])  # Deployment
                i_go = find_idx(["golivedate", "go live date", "go-live date".replace(" ", "")])
                i_rel = find_idx(["clarityrelease", "jirafixversion", "fixversion"])
                if i_dep >= 0 and i_go >= 0 and i_rel >= 0:
                    for r in tbl[1:]:
                        deployment = str(safe(r, i_dep) or "").strip()
                        go_live_date = str(safe(r, i_go) or "").strip()
                        release_version = str(safe(r, i_rel) or "").strip()
                        if deployment or go_live_date or release_version:
                            rows.append({
                                "deployment": deployment,
                                "go_live_date": go_live_date,
                                "release_version": release_version,
                            })
    return rows


def _build_jira_request(url: str, method: str = "GET", data: Optional[bytes] = None, content_type: Optional[str] = None) -> urllib.request.Request:
    """Create a urllib Request with the appropriate Jira authentication based on env.
    Supports:
      - basic (default): Authorization: Basic base64(username:token)
      - bearer: Authorization: Bearer <JIRA_BEARER_TOKEN>
      - cookie: Cookie: <JIRA_COOKIE>
    """
    req = urllib.request.Request(url, data=data, method=method)
    # Common headers
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", "JiraAgent/1.0 (+Windows) Python-urllib")
    if content_type:
        req.add_header("Content-Type", content_type)

    mode = JIRA_AUTH_MODE
    try:
        if mode == "bearer" and JIRA_BEARER_TOKEN:
            req.add_header("Authorization", f"Bearer {JIRA_BEARER_TOKEN}")
        elif mode == "cookie" and JIRA_COOKIE:
            req.add_header("Cookie", JIRA_COOKIE)
        else:
            # Fallback/basic
            user_id = JIRA_USERNAME if JIRA_USERNAME else JIRA_EMAIL
            auth = b64encode(f"{user_id}:{JIRA_API_TOKEN}".encode()).decode()
            req.add_header("Authorization", f"Basic {auth}")
    except Exception:
        # Do not crash on header building; allow request to proceed without auth (likely 401)
        pass
    return req


def tokenize_for_jql_public(s: str, limit_tokens: int = 8):
    try:
        s = str(s)
    except Exception:
        s = ""
    import re
    s = re.sub(r"[^A-Za-z0-9]+", " ", s)
    raw = [t.lower() for t in s.split()]
    stop = {
        'the','and','for','with','from','this','that','have','has','had','was','were','is','are','will','can','could','should','would',
        'to','of','in','on','at','by','a','an','as','it','its','be','been','not','no','yes','we','they','you','he','she','i','or','but',
        'please','customer','issue','error','problem','phone','call','number','order','id','code','cart','mdn','sos'
    }
    toks = [t for t in raw if len(t) >= 4 and not t.isdigit() and t not in stop]
    seen = set()
    out = []
    for t in toks:
        if t not in seen:
            seen.add(t)
            out.append(t)
        if len(out) >= limit_tokens:
            break
    return out

def _html_to_text(html: str, max_len: int = 4000) -> str:
    try:
        s = str(html)
    except Exception:
        s = ""
    import re
    # Remove script/style
    s = re.sub(r"<script[\s\S]*?</script>", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.IGNORECASE)
    # Replace breaks and block tags with newlines
    s = re.sub(r"<(br|p|div|li|h[1-6])[^>]*>", "\n", s, flags=re.IGNORECASE)
    # Strip tags
    s = re.sub(r"<[^>]+>", " ", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s[:max_len]

def _extract_structure(html: str, max_items: int = 50):
    try:
        s = str(html)
    except Exception:
        s = ""
    import re
    items = []
    for m in re.finditer(r"<h([1-6])[^>]*>([\s\S]*?)</h\1>", s, flags=re.IGNORECASE):
        txt = _html_to_text(m.group(2), max_len=500)
        if txt:
            items.append({"type": "heading", "level": int(m.group(1)), "text": txt})
        if len(items) >= max_items:
            break
    for m in re.finditer(r"<li[^>]*>([\s\S]*?)</li>", s, flags=re.IGNORECASE):
        txt = _html_to_text(m.group(1), max_len=300)
        if txt:
            items.append({"type": "bullet", "text": txt})
        if len(items) >= max_items:
            break
    return items

def _summarize_text(text: str, query_tokens: List[str], max_sentences: int = 6) -> str:
    # Very simple extractive summary: pick sentences containing most query tokens, then top-k by length/coverage
    import re
    try:
        t = str(text)
    except Exception:
        t = ""
    sentences = re.split(r"(?<=[.!?])\s+", t)
    qt = [q.lower() for q in (query_tokens or [])]
    scored = []
    for s in sentences:
        sl = s.lower()
        hits = sum(1 for q in qt if q and q in sl)
        score = hits * 2 + min(len(s), 300) / 300
        if s.strip():
            scored.append((score, s.strip()))
    top = [s for _, s in sorted(scored, key=lambda x: x[0], reverse=True)[:max_sentences]]
    return "\n".join(top)

def _boost_by_phrases(scores_sentences, phrases):
    out = []
    ph = [p.lower() for p in phrases if p]
    for score, s in scores_sentences:
        sl = s.lower()
        hits = sum(1 for p in ph if p in sl)
        out.append((score + hits * 1.5, s))
    return out

def _quote_list(value: str):
    items = [s.strip() for s in value.split(",") if s.strip()]
    return items

def _parse_date_any(s: str):
    from datetime import datetime
    s = (s or '').strip()
    fmts = [
        "%B %d, %Y",  # January 5, 2026
        "%b %d, %Y",  # Jan 5, 2026
        "%d %B %Y",   # 5 January 2026
        "%d %b %Y",   # 5 Jan 2026
        "%b %d %Y",   # Jan 5 2026 (no comma)
        "%d %b %y",   # 5 Jan 26 (2-digit year)
        "%d-%b-%Y",   # 05-Jan-2026
        "%d-%b-%y",   # 05-Jan-26
        "%Y-%m-%d",   # 2026-01-05
        "%m/%d/%Y",   # 01/05/2026 (US)
        "%d/%m/%Y",   # 05/01/2026 (EU)
    ]
    for f in fmts:
        try:
            return datetime.strptime(s, f)
        except Exception:
            pass
    return None

def _find_date_strings(s: str):
    """Return a list of candidate date substrings in many common formats.
    Supports:
      - MonthName dd, yyyy / MonthName dd yyyy
      - dd MonthName yyyy
      - dd-Mon-YYYY / dd-Mon-YY
      - ISO yyyy-mm-dd
      - dd/mm/yyyy and mm/dd/yyyy
    """
    import re
    src = (s or "")
    patterns = [
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},\s+\d{4}\b",
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}\s+\d{4}\b",
        r"\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{2,4}\b",
        r"\b\d{1,2}-[A-Za-z]{3}-\d{2,4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",
    ]
    out = []
    seen = set()
    for pat in patterns:
        for m in re.finditer(pat, src, flags=re.IGNORECASE):
            val = (m.group(0) or '').strip()
            k = val.lower()
            if val and k not in seen:
                seen.add(k)
                out.append(val)
    return out

def _parse_month_range(line: str):
    """Parse patterns like 'Jan 2-5, 2026' → (2026-01-02, 2026-01-05)."""
    import re
    months = {
        'jan':1,'january':1,'feb':2,'february':2,'mar':3,'march':3,'apr':4,'april':4,
        'may':5,'jun':6,'june':6,'jul':7,'july':7,'aug':8,'august':8,'sep':9,'sept':9,'september':9,
        'oct':10,'october':10,'nov':11,'november':11,'dec':12,'december':12
    }
    m = re.search(r"\b([A-Za-z]{3,9})\s+(\d{1,2})\s*-\s*(\d{1,2}),\s*(\d{4})\b", line)
    if not m:
        return None
    mon = months.get(m.group(1).lower())
    if not mon:
        return None
    try:
        y = int(m.group(4)); d1 = int(m.group(2)); d2 = int(m.group(3))
        from datetime import date
        return {
            "start": date(y, mon, d1).isoformat(),
            "end": date(y, mon, d2).isoformat()
        }
    except Exception:
        return None

def fetch_release_plan_digital_first(from_ym: str = "2026-01", months: int = 24):
    """Fetch release plan HTML and extract Digital First deployments and Deployment Freeze windows.
    Returns array of { month: 'YYYY-MM', deployments: [ISO dates], freezes: [{start,end}] }.
    """
    # Fetch page
    print(f"[MCP Server] Fetching Release Plan page: {RELEASE_PLAN_URL}")
    try:
        req = urllib.request.Request(RELEASE_PLAN_URL)
        # Browser-like headers to avoid 406
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
        req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8")
        req.add_header("Accept-Language", "en-US,en;q=0.9")
        req.add_header("Upgrade-Insecure-Requests", "1")
        # Optional cookie for SSO-protected sites
        cookie = os.environ.get("RELEASE_PLAN_COOKIE", "").strip()
        if cookie:
            req.add_header("Cookie", cookie)
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[MCP Server] Release Plan fetch error: {e}")
        return {"error": f"Failed to fetch {RELEASE_PLAN_URL}: {e}"}
    text = _html_to_text(html, max_len=500000)
    # Split into lines for neighborhood scanning
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    from datetime import datetime
    # Build map month→info
    out = {}
    def ensure_bucket(dt):
        ym = dt.strftime("%Y-%m")
        if ym not in out:
            out[ym] = {"month": ym, "deployments": [], "freezes": []}
        return out[ym]
    # Scan lines for keywords and dates
    import re
    for idx, line in enumerate(lines):
        low = line.lower()
        # Deployment Freeze window (allow ranges)
        if "deployment freeze" in low or "freeze window" in low:
            # Try range first
            rng = _parse_month_range(line)
            if not rng and idx+1 < len(lines):
                rng = _parse_month_range(lines[idx+1])
            if rng:
                # Use start date to bucket month
                d0 = _parse_date_any(rng["start"])
                if d0:
                    b = ensure_bucket(d0)
                    b["freezes"].append(rng)
                continue
            # Else look for single dates possibly indicating a freeze start
            mdates = _find_date_strings(line)
            if not mdates and idx+1 < len(lines):
                mdates = _find_date_strings(lines[idx+1])
            for ds in mdates:
                dt = _parse_date_any(ds)
                if dt:
                    b = ensure_bucket(dt)
                    b["freezes"].append({"start": dt.date().isoformat(), "end": dt.date().isoformat()})
        # Digital First deployments
        import re as _re
        if _re.search(r"digital\s*first", low) and ("deploy" in low or "release" in low):
            # Extract any dates in this or next line
            mdates = _find_date_strings(line)
            if not mdates and idx+1 < len(lines):
                mdates = _find_date_strings(lines[idx+1])
            for ds in mdates:
                dt = _parse_date_any(ds)
                if dt:
                    b = ensure_bucket(dt)
                    iso = dt.date().isoformat()
                    if iso not in b["deployments"]:
                        b["deployments"].append(iso)
    # Filter months from from_ym onwards and limit count
    def ym_key(ym: str):
        try:
            return datetime.strptime(ym+"-01", "%Y-%m-%d")
        except Exception:
            return datetime(1970,1,1)
    start_dt = ym_key(from_ym)
    months_sorted = sorted([m for m in out.keys() if ym_key(m) >= start_dt], key=lambda x: ym_key(x))
    months_sorted = months_sorted[:max(1, int(months))]
    result = {"url": RELEASE_PLAN_URL, "months": [out[m] for m in months_sorted]}
    print(f"[MCP Server] Release Plan parsed months: {len(result['months'])}")
    # Fallback: if no months parsed from text, try extracting dates from tooltip attributes
    if not result["months"]:
        try:
            tips = extract_digital_first_tooltips(html)
            print(f"[MCP Server] Fallback tooltips count: {len(tips)}")
            # Parse any dates present in tooltip strings
            # Collect individual dates and ranges
            from datetime import datetime
            def ensure_bucket_by_iso(iso_date: str):
                try:
                    dt = datetime.strptime(iso_date, "%Y-%m-%d")
                except Exception:
                    return
                b = ensure_bucket(dt)
                if iso_date not in b["deployments"]:
                    b["deployments"].append(iso_date)
            for t in tips:
                # Try range first
                rng = _parse_month_range(t)
                if rng and rng.get("start") and rng.get("end"):
                    ensure_bucket_by_iso(rng["start"])
                    ensure_bucket_by_iso(rng["end"])
                    continue
                # Find individual Month Day, Year patterns within the tooltip
                mdates = _find_date_strings(t)
                for ds in mdates:
                    dt = _parse_date_any(ds)
                    if dt:
                        ensure_bucket_by_iso(dt.date().isoformat())
            months_sorted = sorted(out.keys(), key=lambda x: ym_key(x))
            if from_ym:
                months_sorted = [m for m in months_sorted if ym_key(m) >= ym_key(from_ym)]
            months_sorted = months_sorted[:max(1, int(months))]
            result = {"url": RELEASE_PLAN_URL, "months": [out[m] for m in months_sorted]}
            print(f"[MCP Server] Fallback parsed months (tooltips): {len(result['months'])}")
        except Exception as e:
            print(f"[MCP Server] Fallback tooltip parsing error: {e}")
    return result

def parse_release_plan_html_to_months(html: str, from_ym: str = "2026-01", months: int = 24):
    """Parse provided Release Plan HTML to extract Digital First deployments and Freeze windows.
    Returns array of { month: 'YYYY-MM', deployments: [ISO dates], freezes: [{start,end}] }.
    """
    if not isinstance(html, str) or not html.strip():
        return {"error": "Missing or empty HTML"}
    text = _html_to_text(html, max_len=500000)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    from datetime import datetime
    out = {}
    def ensure_bucket(dt):
        ym = dt.strftime("%Y-%m")
        if ym not in out:
            out[ym] = {"month": ym, "deployments": [], "freezes": []}
        return out[ym]
    import re
    for idx, line in enumerate(lines):
        low = line.lower()
        if "deployment freeze" in low or "freeze window" in low:
            rng = _parse_month_range(line)
            if not rng and idx+1 < len(lines):
                rng = _parse_month_range(lines[idx+1])
            if rng:
                d0 = _parse_date_any(rng["start"])
                if d0:
                    b = ensure_bucket(d0)
                    b["freezes"].append(rng)
                continue
            mdates = _find_date_strings(line)
            if not mdates and idx+1 < len(lines):
                mdates = _find_date_strings(lines[idx+1])
            for ds in mdates:
                dt = _parse_date_any(ds)
                if dt:
                    b = ensure_bucket(dt)
                    b["freezes"].append({"start": dt.date().isoformat(), "end": dt.date().isoformat()})
        import re as _re
        if _re.search(r"digital\s*first", low) and ("deploy" in low or "release" in low):
            mdates = _find_date_strings(line)
            if not mdates and idx+1 < len(lines):
                mdates = _find_date_strings(lines[idx+1])
            for ds in mdates:
                dt = _parse_date_any(ds)
                if dt:
                    b = ensure_bucket(dt)
                    iso = dt.date().isoformat()
                    if iso not in b["deployments"]:
                        b["deployments"].append(iso)
    # Fallback via tooltips if needed
    months_map = out
    if not months_map:
        try:
            tips = extract_digital_first_tooltips(html)
            from datetime import datetime as _dt
            def ensure_bucket_by_iso(iso_date: str):
                try:
                    dt = _dt.strptime(iso_date, "%Y-%m-%d")
                except Exception:
                    return
                ym = dt.strftime("%Y-%m")
                if ym not in months_map:
                    months_map[ym] = {"month": ym, "deployments": [], "freezes": []}
                if iso_date not in months_map[ym]["deployments"]:
                    months_map[ym]["deployments"].append(iso_date)
            for t in tips:
                rng = _parse_month_range(t)
                if rng and rng.get("start") and rng.get("end"):
                    ensure_bucket_by_iso(rng["start"]); ensure_bucket_by_iso(rng["end"])
                    continue
                mdates = _find_date_strings(t)
                for ds in mdates:
                    dt = _parse_date_any(ds)
                    if dt:
                        ensure_bucket_by_iso(dt.date().isoformat())
        except Exception:
            pass
    # Filter from month and limit count
    def ym_key(ym: str):
        try:
            return datetime.strptime(ym+"-01", "%Y-%m-%d")
        except Exception:
            return datetime(1970,1,1)
    start_dt = ym_key(from_ym)
    months_sorted = sorted([m for m in months_map.keys() if ym_key(m) >= start_dt], key=lambda x: ym_key(x))
    months_sorted = months_sorted[:max(1, int(months))]
    result = {"url": RELEASE_PLAN_URL, "months": [months_map[m] for m in months_sorted]}
    return result

def extract_digital_first_tooltips(html: str):
    """Extract tooltip values associated with Digital First deployments.
    Heuristics:
      - Attributes possibly used for tooltips: title, data-original-title, data-bs-original-title, aria-label, data-tooltip, data-title, data-content.
      - Tags whose inner text contains 'Digital First' → collect tooltip-like attributes from that tag.
      - Tags within ~200 chars of 'Digital First' text (siblings/nearby) → collect tooltip-like attributes.
      - Direct matches where the attribute value itself contains 'Digital First'.
    Returns a unique list of tooltip strings.
    """
    import re
    s = str(html)
    # Direct attribute matches containing "Digital First"
    attr_names = [
        'title','data-original-title','data-bs-original-title','aria-label','data-tooltip','data-title','data-content'
    ]
    found = []
    seen = set()
    for an in attr_names:
        pat1 = rf'{an}\s*=\s*"([^"]*Digital\s*First[^"]*)"'
        pat2 = rf"{an}\s*=\s*'([^']*Digital\s*First[^']*)'"
        for m in re.finditer(pat1, s, flags=re.IGNORECASE):
            val = (m.group(1) or '').strip()
            k = val.lower()
            if val and k not in seen:
                seen.add(k)
                found.append(val)
        for m in re.finditer(pat2, s, flags=re.IGNORECASE):
            val = (m.group(1) or '').strip()
            k = val.lower()
            if val and k not in seen:
                seen.add(k)
                found.append(val)
    # Tags whose inner text includes 'Digital First'
    tag_pat = re.compile(r"<([a-zA-Z][a-zA-Z0-9]*)\s+([^>]*?)>([\s\S]*?)</\1>", re.IGNORECASE)
    for m in tag_pat.finditer(s):
        attrs = m.group(2) or ''
        inner = m.group(3) or ''
        if re.search(r"Digital\s*First", inner, flags=re.IGNORECASE):
            # Extract tooltip-like attributes from the opening tag
            for an in attr_names:
                m1 = re.search(rf'{an}\s*=\s*"([^"]+)"', attrs, flags=re.IGNORECASE)
                m2 = re.search(rf"{an}\s*=\s*'([^']+)'", attrs, flags=re.IGNORECASE)
                val = None
                if m1:
                    val = m1.group(1)
                elif m2:
                    val = m2.group(1)
                if val:
                    v = val.strip()
                    k = v.lower()
                    if v and k not in seen:
                        seen.add(k)
                        found.append(v)
    # Nearby tags within 200 chars of 'Digital First'
    for m in re.finditer(r"Digital\s*First", s, flags=re.IGNORECASE):
        start = max(0, m.start() - 200)
        end = min(len(s), m.end() + 200)
        window = s[start:end]
        # Fetch opening tags in the window and extract tooltip attributes
        for an in attr_names:
            for m1 in re.finditer(rf'{an}\s*=\s*"([^"]+)"', window, flags=re.IGNORECASE):
                v = (m1.group(1) or '').strip()
                k = v.lower()
                if v and k not in seen:
                    seen.add(k)
                    found.append(v)
            for m2 in re.finditer(rf"{an}\s*=\s*'([^']+)'", window, flags=re.IGNORECASE):
                v = (m2.group(1) or '').strip()
                k = v.lower()
                if v and k not in seen:
                    seen.add(k)
                    found.append(v)
    return found

# System alias map (can be externalized later)
SYSTEM_ALIASES = {
    "CJCM": ["cjcm", "journey", "customer journey", "ui flow"],
    "CXP": ["cxp", "activation", "order capture", "billing profile", "activation api"],
    "Enforce": ["enforce", "policy", "entitlement", "rules engine"],
    "SAP": ["sap", "ecc", "idoc", "bapi", "rfc", "sap ecc"],
}
# Allow alias overrides via env var (comma-separated system:alias1|alias2)
try:
    override = os.environ.get("SYSTEM_ALIASES", "")
    if override.strip():
        parts = [p.strip() for p in override.split(",") if p.strip()]
        for p in parts:
            if ":" in p:
                sys, ali = p.split(":", 1)
                alist = [a.strip() for a in ali.split("|") if a.strip()]
                if alist:
                    SYSTEM_ALIASES[sys.strip()] = alist
except Exception:
    pass

def _score_system(text: str) -> dict:
    s = (text or "").lower()
    scores = {k:0 for k in SYSTEM_ALIASES.keys()}
    for system, aliases in SYSTEM_ALIASES.items():
        for a in aliases:
            if a and a in s:
                scores[system] += 2
        # exact system name gets extra weight
        if system.lower() in s:
            scores[system] += 3
    return scores


def _build_jql(project: str, assigned_to: Optional[str], issue_type: Optional[str], status: Optional[str], priority: Optional[str]) -> str:
    terms = []
    terms.append(f'project="{project}"')
    if assigned_to:
        at = str(assigned_to)
        if at.lower() in ("me", "currentuser"):
            terms.append("assignee = currentUser()")
        else:
            # Support CJCM JSON-encoded list for names with commas
            if at.startswith("__cjcmjson__:"):
                try:
                    raw = at.replace("__cjcmjson__:", "", 1)
                    items = json.loads(raw)
                    items = [str(s).strip() for s in items if str(s).strip()]
                except Exception:
                    items = []
                if len(items) > 1:
                    terms.append('assignee IN (' + ", ".join([f'"{s}"' for s in items]) + ')')
                elif items:
                    terms.append(f'assignee = "{items[0]}"')
                else:
                    terms.append('assignee is not EMPTY')
            # Single user explicitly JSON-encoded (custom user)
            elif at.startswith("__oneuserjson__:"):
                try:
                    one = json.loads(at.replace("__oneuserjson__:", "", 1))
                    s = str(one)
                except Exception:
                    s = ""
                terms.append(f'assignee = "{s}"')
            # Backward compat: CSV-based CJCM encoding
            elif at.startswith("__cjcm__:"):
                items = [s.strip() for s in at.replace("__cjcm__:", "", 1).split(",") if s.strip()]
                if len(items) > 1:
                    terms.append('assignee IN (' + ", ".join([f'"{s}"' for s in items]) + ')')
                elif items:
                    terms.append(f'assignee = "{items[0]}"')
            else:
                terms.append(f'assignee = "{at}"')
    if issue_type:
        terms.append(f'issuetype = "{issue_type}"')
    if status:
        sts = _quote_list(status)
        if len(sts) > 1:
            terms.append('status IN (' + ", ".join([f'"{s}"' for s in sts]) + ')')
        else:
            terms.append(f'status = "{sts[0]}"')
    if priority:
        prios = _quote_list(priority)
        if len(prios) > 1:
            terms.append('priority IN (' + ", ".join([f'"{p}"' for p in prios]) + ')')
        else:
            terms.append(f'priority = "{prios[0]}"')
    jql = " AND ".join(terms) + " ORDER BY created DESC"
    return jql


def fetch_jira_issues(project_key: str, max_results: int = 25, start_at: int = 0, assigned_to: Optional[str] = None, issue_type: Optional[str] = None, status: Optional[str] = None, priority: Optional[str] = None):
    if JIRA_MOCK or not (JIRA_BASE_URL and JIRA_EMAIL and JIRA_API_TOKEN):
        if JIRA_MOCK:
            print("[MCP Server] Using MOCK mode (JIRA_MOCK=1).")
        else:
            print("[MCP Server] Missing envs; using MOCK.")
            print(f"  JIRA_BASE_URL={'set' if JIRA_BASE_URL else 'missing'}; JIRA_EMAIL={'set' if JIRA_EMAIL else 'missing'}; JIRA_API_TOKEN={'set' if JIRA_API_TOKEN else 'missing'}")
        return {
            "issues": [
                {"key": f"{project_key}-1", "fields": {"summary": "Mock issue one", "status": {"name": "To Do"}}},
                {"key": f"{project_key}-2", "fields": {"summary": "Mock issue two", "status": {"name": "In Progress"}}},
            ],
            "maxResults": max_results,
            "isMock": True,
        }

    jql = _build_jql(project_key, assigned_to, issue_type, status, priority)
    print(f"JIRA query: {jql}")
    api_ver = "2" if JIRA_API_VERSION == "2" else "3"
    # Include names expand to map customfield IDs to human-readable names
    url = f"{JIRA_BASE_URL}/rest/api/{api_ver}/search?jql={urllib.parse.quote(jql)}&maxResults={max_results}&startAt={start_at}&expand=names"
    print(f"JIRA URL: {url}")
    # Prefer username for on-prem if provided; fall back to email
    req = _build_jira_request(url)
    # Use default SSL context
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = resp.read().decode("utf-8")
            payload = json.loads(data)
            # Derive components and 'Work Owner VCG' from fields when possible
            names = payload.get("names", {})
            work_owner_key = None
            for k, v in names.items():
                if isinstance(v, str) and v.strip().lower() == "work owner vcg":
                    work_owner_key = k
                    break
            issues = payload.get("issues", [])
            for issue in issues:
                fields = issue.get("fields", {})
                comps = fields.get("components") or []
                comp_names = [c.get("name") for c in comps if isinstance(c, dict)]
                # Fix Versions (standard Jira field)
                fixvers = fields.get("fixVersions") or []
                fixver_names = [fv.get("name") for fv in fixvers if isinstance(fv, dict)]
                work_owner = None
                if work_owner_key and work_owner_key in fields:
                    work_owner = fields.get(work_owner_key)
                assignee = fields.get("assignee") or {}
                assignee_name = assignee.get("displayName") or assignee.get("name") or assignee.get("emailAddress") or None
                # Attach simplified extras for UI consumption
                issue["extra"] = {
                    "components": comp_names,
                    "fixVersions": fixver_names,
                    "workOwnerVCG": work_owner,
                    "assignee": assignee_name,
                }
            return payload
    except urllib.error.HTTPError as e:
        err_text = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
        raise RuntimeError(f"Jira search failed: HTTP {e.code} {err_text[:300]}")


def fetch_latest_comment(issue_key: str):
    if JIRA_MOCK or not (JIRA_BASE_URL and (JIRA_USERNAME or JIRA_EMAIL) and JIRA_API_TOKEN):
        return {"issue": issue_key, "latestComment": {"author": "mock-user", "body": "This is a mock comment.", "created": "2025-12-10T10:00:00.000+0000"}, "isMock": True}

    api_ver = "2" if JIRA_API_VERSION == "2" else "3"
    expand = "&expand=renderedBody" if api_ver == "2" else ""
    url = f"{JIRA_BASE_URL}/rest/api/{api_ver}/issue/{urllib.parse.quote(issue_key)}/comment?orderBy=created&maxResults=50{expand}"
    user_id = JIRA_USERNAME if JIRA_USERNAME else JIRA_EMAIL
    auth = b64encode(f"{user_id}:{JIRA_API_TOKEN}".encode()).decode()
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = resp.read().decode("utf-8")
        j = json.loads(data)
        comments = j.get("comments", [])
        if not comments:
            return {"issue": issue_key, "latestComment": None, "total": j.get("total", 0)}
        latest = sorted(comments, key=lambda c: c.get("created", ""))[-1]
        return {"issue": issue_key, "latestComment": latest, "total": j.get("total", len(comments))}


def fetch_issue_attachments(issue_key: str):
    if JIRA_MOCK or not (JIRA_BASE_URL and (JIRA_USERNAME or JIRA_EMAIL) and JIRA_API_TOKEN):
        return {"issue": issue_key, "attachments": []}
    api_ver = "2" if JIRA_API_VERSION == "2" else "3"
    url = f"{JIRA_BASE_URL}/rest/api/{api_ver}/issue/{urllib.parse.quote(issue_key)}?fields=attachment"
    user_id = JIRA_USERNAME if JIRA_USERNAME else JIRA_EMAIL
    auth = b64encode(f"{user_id}:{JIRA_API_TOKEN}".encode()).decode()
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = resp.read().decode("utf-8")
        j = json.loads(data)
        fields = j.get("fields", {})
        atts = fields.get("attachment", [])
        out = []
        for a in atts:
            out.append({
                "id": a.get("id"),
                "filename": a.get("filename"),
                "content": a.get("content"),
                "thumbnail": a.get("thumbnail"),
                "mimeType": a.get("mimeType"),
                "size": a.get("size"),
            })
        return {"issue": issue_key, "attachments": out}


def fetch_issue_details(issue_key: str):
    """Fetch summary fields for an issue: summary, description, created, and comments.
    Returns a consolidatedComments string which concatenates comment bodies in order.
    """
    if JIRA_MOCK or not (JIRA_BASE_URL and (JIRA_USERNAME or JIRA_EMAIL) and JIRA_API_TOKEN):
        return {
            "issue": issue_key,
            "summary": "Mock summary",
            "description": "Mock description",
            "created": "2025-12-10T10:00:00.000+0000",
            "comments": [
                {"author": "mock-user", "created": "2025-12-10T10:00:00.000+0000", "body": "First comment"},
                {"author": "mock-user2", "created": "2025-12-11T09:00:00.000+0000", "body": "Second comment"},
            ],
            "consolidatedComments": "First comment\n\nSecond comment",
            "isMock": True,
        }

    api_ver = "2" if JIRA_API_VERSION == "2" else "3"
    # For v3, description may be a rich text document; we'll return raw value
    url = f"{JIRA_BASE_URL}/rest/api/{api_ver}/issue/{urllib.parse.quote(issue_key)}?fields=summary,description,created,comment"
    user_id = JIRA_USERNAME if JIRA_USERNAME else JIRA_EMAIL
    auth = b64encode(f"{user_id}:{JIRA_API_TOKEN}".encode()).decode()
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = resp.read().decode("utf-8")
        j = json.loads(data)
        fields = j.get("fields", {})
        summary = fields.get("summary")
        description = fields.get("description")
        created = fields.get("created")
        comment_block = fields.get("comment") or {}
        comments = []
        # v2: comments is list; v3: comments are in comment.comments
        raw = comment_block.get("comments") if isinstance(comment_block, dict) else None
        raw = raw if isinstance(raw, list) else (comment_block if isinstance(comment_block, list) else [])
        for c in raw:
            if isinstance(c, dict):
                author_obj = c.get("author") or {}
                author_name = author_obj.get("displayName") or author_obj.get("name") or ""
                comments.append({
                    "author": author_name,
                    "created": c.get("created"),
                    "body": c.get("body") or "",
                })
        # Consolidate comment bodies from latest to oldest
        comments_sorted = sorted(comments, key=lambda x: x.get("created") or "", reverse=True)
        consolidated = "\n\n".join((c.get("body") or "").strip() for c in comments_sorted if (c.get("body") or "").strip())
        return {
            "issue": issue_key,
            "summary": summary,
            "description": description,
            "created": created,
            "comments": comments_sorted,
            "consolidatedComments": consolidated,
        }


def search_similar_issues(issue_key: str, project_keys: list, max_results: int = 20):
    """Search for issues across given projects whose text or comments match the description/comments of the given issue key."""
    # First fetch the target issue description/comments
    base = fetch_issue_details(issue_key)
    desc = base.get("description") or ""
    consolidated = base.get("consolidatedComments") or ""
    # Build a conservative search string by truncating to avoid overly long queries
    def clean_text(s: str, limit: int = 300):
        try:
            s = str(s)
        except Exception:
            s = ""
        s = s.replace("\r", " ").replace("\n", " ").strip()
        return s[:limit]
    def jql_escape(s: str) -> str:
        # Escape double quotes and backslashes for JQL string literals
        return str(s).replace("\\", "\\\\").replace('"', '\\"')
    q_desc = clean_text(desc)
    q_comm = clean_text(consolidated)

    def tokenize_for_jql(s: str, limit_tokens: int = 8):
        # Replace non-word chars with spaces, split, filter short tokens and numeric-only
        try:
            s = str(s)
        except Exception:
            s = ""
        import re
        s = re.sub(r"[^A-Za-z0-9]+", " ", s)
        raw = [t.lower() for t in s.split()]
        # Basic stopwords to reduce noise
        stop = {
            'the','and','for','with','from','this','that','have','has','had','was','were','is','are','will','can','could','should','would',
            'to','of','in','on','at','by','a','an','as','it','its','be','been','not','no','yes','we','they','you','he','she','i','or','but',
            'please','customer','issue','error','problem','phone','call','number','order','id','code','cart','mdn','sos'
        }
        toks = [t for t in raw if len(t) >= 4 and not t.isdigit() and t not in stop]
        # Deduplicate preserving order
        seen = set()
        out = []
        for t in toks:
            if t not in seen:
                seen.add(t)
                out.append(t)
            if len(out) >= limit_tokens:
                break
        return out

    def extract_phrases(s: str, max_phrases: int = 3, min_len: int = 2, max_len: int = 5):
        # Build short contiguous phrases from cleaned text to try quoted searches
        try:
            s = str(s)
        except Exception:
            s = ""
        import re
        words = [w for w in re.sub(r"[^A-Za-z0-9]+", " ", s).split() if len(w) >= 3]
        phrases = []
        for L in range(max_len, min_len-1, -1):
            for i in range(0, max(0, len(words)-L+1)):
                ph = " ".join(words[i:i+L])
                if len(ph) >= 8:
                    phrases.append(ph)
                    if len(phrases) >= max_phrases:
                        return phrases
        return phrases

    # Build token lists from description and comments; fallback to summary
    # Consider title (summary), description, and comments tokens for similarity
    tokens_desc = tokenize_for_jql(q_desc)
    tokens_sum = tokenize_for_jql(base.get("summary", ""))
    tokens_comm = tokenize_for_jql(q_comm, limit_tokens=6)
    phrases_desc = extract_phrases(q_desc)
    phrases_sum = extract_phrases(base.get("summary", ""), max_phrases=2, min_len=2, max_len=4)
    # Prefer description tokens, then summary; keep comments as auxiliary
    tokens = tokens_desc or tokens_sum
    # Compose JQL across projects
    projects_clause = " OR ".join([f"project={pk}" for pk in project_keys if pk])
    if not projects_clause:
        projects_clause = ""
    # Prefer comment ~ and text ~ where supported
    # Use parentheses to combine clauses
    # Build matching: require multiple tokens (AND) across summary/description, OR matches in comments, prefer quoted phrases
    jql = ''
    clauses = []
    if tokens:
        toks = tokens[:4]
        summary_and = " AND ".join([f'summary ~ "{jql_escape(t)}"' for t in toks])
        desc_and = " AND ".join([f'description ~ "{jql_escape(t)}"' for t in toks])
        sd_clause = f'(({desc_and}) OR ({summary_and}))' if desc_and and summary_and else (desc_and or summary_and)
        if sd_clause:
            clauses.append(f'({sd_clause})')
    # Add phrase matches for stronger relevance
    phrase_clauses = []
    for ph in phrases_desc[:2]:
        phrase_clauses.append(f'description ~ "{jql_escape(ph)}"')
    for ph in phrases_sum[:1]:
        phrase_clauses.append(f'summary ~ "{jql_escape(ph)}"')
    if phrase_clauses:
        clauses.append('(' + ' OR '.join(phrase_clauses) + ')')
    # Add comment token ORs (looser)
    if tokens_comm:
        comm_tokens = tokens_comm[:6]
        comm_or = " OR ".join([f'comment ~ "{jql_escape(t)}"' for t in comm_tokens])
        if comm_or:
            clauses.append(f'({comm_or})')
    if not clauses:
        jql = f'key = "{jql_escape(issue_key)}"'
    else:
        jql = "(" + " OR ".join(clauses) + ")"
    # Exclude the original issue from results
    jql = f"({jql}) AND key != \"{jql_escape(issue_key)}\""
    if projects_clause:
        jql = f"(({projects_clause})) AND {jql}"
    # Ensure newest issues first
    jql = jql + " ORDER BY created DESC"
    params = {"jql": jql, "maxResults": str(max_results)}
    # Call search
    if JIRA_MOCK or not (JIRA_BASE_URL and (JIRA_USERNAME or JIRA_EMAIL) and JIRA_API_TOKEN):
        return {"issue": issue_key, "jql": jql, "issues": [], "isMock": True}
    api_ver = "2" if JIRA_API_VERSION == "2" else "3"
    url = f"{JIRA_BASE_URL}/rest/api/{api_ver}/search?{urllib.parse.urlencode(params)}"
    user_id = JIRA_USERNAME if JIRA_USERNAME else JIRA_EMAIL
    auth = b64encode(f"{user_id}:{JIRA_API_TOKEN}".encode()).decode()
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = resp.read().decode("utf-8")
        j = json.loads(data)
        return {"issue": issue_key, "jql": jql, "issues": j.get("issues", []), "total": j.get("total")}


def fetch_fields_map():
    api_ver = "2" if JIRA_API_VERSION == "2" else "3"
    url = f"{JIRA_BASE_URL}/rest/api/{api_ver}/field"
    user_id = JIRA_USERNAME if JIRA_USERNAME else JIRA_EMAIL
    auth = b64encode(f"{user_id}:{JIRA_API_TOKEN}".encode()).decode()
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = resp.read().decode("utf-8")
        arr = json.loads(data)
        return {f.get("name"): f.get("id") for f in arr if isinstance(arr, list) or isinstance(arr, dict)}


def fetch_work_owner_options(project_key: str, max_results: int = 200, jql_override: Optional[str] = None):
    """Best-effort: derive allowed values for 'Work Owner VCG' by sampling issues in a project.
    Note: Jira does not expose custom field options generically without admin APIs. This samples existing values.
    """
    api_ver = "2" if JIRA_API_VERSION == "2" else "3"
    # Build a search limited to project (allow override)
    jql = jql_override if jql_override else f'project="{project_key}" ORDER BY created DESC'
    url = f"{JIRA_BASE_URL}/rest/api/{api_ver}/search?jql={urllib.parse.quote(jql)}&maxResults={max_results}&startAt=0&expand=names"
    user_id = JIRA_USERNAME if JIRA_USERNAME else JIRA_EMAIL
    auth = b64encode(f"{user_id}:{JIRA_API_TOKEN}".encode()).decode()
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = resp.read().decode("utf-8")
        payload = json.loads(data)
        names = payload.get("names", {})
        work_owner_key = None
        for k, v in names.items():
            if isinstance(v, str) and v.strip().lower() == "work owner vcg":
                work_owner_key = k
                break
        values = set()
        for issue in payload.get("issues", []):
            fields = issue.get("fields", {})
            if work_owner_key and work_owner_key in fields:
                val = fields.get(work_owner_key)
                if isinstance(val, str):
                    t = val.strip()
                    if t:
                        values.add(t)
        return {"fieldId": work_owner_key, "options": sorted(values)}


def fetch_project_components(project_key: str):
    api_ver = "2" if JIRA_API_VERSION == "2" else "3"
    url = f"{JIRA_BASE_URL}/rest/api/{api_ver}/project/{urllib.parse.quote(project_key)}/components"
    user_id = JIRA_USERNAME if JIRA_USERNAME else JIRA_EMAIL
    auth = b64encode(f"{user_id}:{JIRA_API_TOKEN}".encode()).decode()
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = resp.read().decode("utf-8")
        arr = json.loads(data)
        return arr

def fetch_projects():
    api_ver = "2" if JIRA_API_VERSION == "2" else "3"
    url = f"{JIRA_BASE_URL}/rest/api/{api_ver}/project"
    req = _build_jira_request(url)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = resp.read().decode("utf-8")
            arr = json.loads(data)
            # Normalize to name/key pairs
            out = []
            for p in arr:
                if isinstance(p, dict):
                    out.append({
                        "id": p.get("id"),
                        "key": p.get("key"),
                        "name": p.get("name"),
                        "projectTypeKey": p.get("projectTypeKey"),
                    })
            return out
    except urllib.error.HTTPError as e:
        err_text = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
        raise RuntimeError(f"Jira projects failed: HTTP {e.code} {err_text[:300]}")


def update_issue_fields(issue_key: str, components_names, work_owner_value: Optional[str], project_key_hint: Optional[str] = None):
    api_ver = "2" if JIRA_API_VERSION == "2" else "3"
    user_id = JIRA_USERNAME if JIRA_USERNAME else JIRA_EMAIL
    auth = b64encode(f"{user_id}:{JIRA_API_TOKEN}".encode()).decode()
    # Resolve components names to IDs
    comp_ids = None
    if components_names:
        # Normalize components input: accept comma-separated string or list
        if isinstance(components_names, str):
            items = [x.strip() for x in components_names.split(',') if x.strip()]
        elif isinstance(components_names, list):
            items = [str(x).strip() for x in components_names if str(x).strip()]
        else:
            items = []
        # Determine project key: prefer hint; otherwise try from issue key prefix before dash
        proj_key = project_key_hint
        if not proj_key and issue_key and "-" in issue_key:
            proj_key = issue_key.split("-")[0]
        # Ensure we use a likely valid Jira project key (strip spaces)
        if isinstance(proj_key, str):
            proj_key = proj_key.strip()
        comps = []
        if proj_key:
            try:
                comps = fetch_project_components(proj_key)
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
                return {"ok": False, "status": e.code, "error": f"Failed to fetch components for project '{proj_key}': {err_text}", "projectKey": proj_key}
            except Exception as e:
                return {"ok": False, "status": 500, "error": f"Error fetching components for project '{proj_key}': {e}", "projectKey": proj_key}
        name_to_id = {c.get("name"): c.get("id") for c in comps if isinstance(c, dict)}
        id_set = {str(c.get("id")) for c in comps if isinstance(c, dict)}
        resolved = []
        # Try resolve each item by ID direct, exact name, or name with trimmed whitespace
        for val in items:
            if val in id_set:
                resolved.append({"id": val})
                continue
            cid = name_to_id.get(val)
            if cid:
                resolved.append({"id": cid})
                continue
            # Attempt normalized matching to handle trailing spaces in Jira names
            normalized_map = {(k.strip() if isinstance(k, str) else k): v for k, v in name_to_id.items()}
            cid2 = normalized_map.get(val.strip())
            if cid2:
                resolved.append({"id": cid2})
        comp_ids = resolved if resolved else None
        if comp_ids is None:
            return {"ok": False, "status": 400, "error": f"No component IDs resolved for values: {', '.join(items)}. Ensure 'projectKeyHint' is the Jira project key (e.g., 'CXPOPER') and send component IDs when possible.", "projectKey": proj_key}

    # Resolve Work Owner VCG custom field id
    work_owner_field_id = None
    if work_owner_value is not None:
        fields_map = fetch_fields_map()
        for name, fid in fields_map.items():
            if isinstance(name, str) and name.strip().lower() == "work owner vcg":
                work_owner_field_id = fid
                break
        if not work_owner_field_id:
            return {"ok": False, "status": 400, "error": "Work Owner VCG field id not found in Jira fields list"}

    patch_body = {"fields": {}}
    if comp_ids is not None:
        patch_body["fields"]["components"] = comp_ids
    if work_owner_field_id and work_owner_value is not None:
        patch_body["fields"][work_owner_field_id] = work_owner_value

    body_bytes = json.dumps(patch_body).encode("utf-8")
    url = f"{JIRA_BASE_URL}/rest/api/{api_ver}/issue/{urllib.parse.quote(issue_key)}"
    req = urllib.request.Request(url, data=body_bytes, method="PUT")
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            status = resp.status
            return {"ok": True, "status": status}
    except urllib.error.HTTPError as e:
        err_text = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
        print(f"[MCP Server] Jira update HTTPError: {e.code} {err_text}")
        return {"ok": False, "status": e.code, "error": err_text}
    except Exception as e:
        print(f"[MCP Server] Jira update error: {e}")
        return {"ok": False, "status": 500, "error": str(e)}

def add_issue_comment(issue_key: str, comment_body: str):
    api_ver = "2" if JIRA_API_VERSION == "2" else "3"
    user_id = JIRA_USERNAME if JIRA_USERNAME else JIRA_EMAIL
    auth = b64encode(f"{user_id}:{JIRA_API_TOKEN}".encode()).decode()
    url = f"{JIRA_BASE_URL}/rest/api/{api_ver}/issue/{urllib.parse.quote(issue_key)}/comment"
    body = json.dumps({"body": comment_body}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as resp:
        data = resp.read().decode("utf-8")
        return json.loads(data) if data else {"ok": True}


class Handler(BaseHTTPRequestHandler):
    def _json(self, status_code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _static_html(self, file_path: str):
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            # Allow CORS for API calls from the page
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            fallback = b"<html><body><h2>UI not found</h2><p>Expected at: " + UI_INDEX_PATH.encode("utf-8") + b"</p></body></html>"
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(fallback)))
            self.end_headers()
            self.wfile.write(fallback)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/debug/oracle":
            # Quick diagnostics for Oracle DSN and DNS resolution
            try:
                dsn = ORACLE_DSN
                user = ORACLE_USER
                present = {"ORACLE_DSN": bool(dsn), "ORACLE_USER": bool(user), "ORACLE_PASSWORD": bool(ORACLE_PASSWORD)}
                def extract_host_port(dsn_str: str):
                    if not isinstance(dsn_str, str):
                        return None, None
                    s = dsn_str.strip()
                    # Try EZCONNECT host[:port][/service]
                    if "(DESCRIPTION=" not in s and "HOST=" not in s:
                        # Split off service
                        left = s.split("/")[0]
                        host = left
                        port = None
                        if ":" in left:
                            host, pr = left.split(":", 1)
                            try:
                                port = int(pr)
                            except Exception:
                                port = None
                        return host or None, port
                    # TNS-like string: find HOST=... and optional PORT=...
                    import re
                    m = re.search(r"HOST\s*=\s*([^\)\s]+)", s, flags=re.IGNORECASE)
                    host = m.group(1) if m else None
                    mp = re.search(r"PORT\s*=\s*(\d+)", s, flags=re.IGNORECASE)
                    port = int(mp.group(1)) if mp else None
                    return host, port
                host, port = extract_host_port(dsn or "")
                dns_ok = False
                addrs = []
                err = None
                if host:
                    try:
                        infos = socket.getaddrinfo(host, port or 0)
                        dns_ok = True
                        addrs = sorted({ai[4][0] for ai in infos if ai and ai[4] and ai[4][0]})
                    except Exception as e:
                        err = str(e)
                self._json(200, {
                    "env": present,
                    "dsn": dsn or "",
                    "host": host or "",
                    "port": port or None,
                    "dnsResolved": dns_ok,
                    "addresses": addrs,
                    "error": err or ""
                })
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        if parsed.path in ("/preview/healthcheck-email",):
            # Serve the healthcheck email preview file if present
            preview_path = os.path.join(WORKSPACE_ROOT, "healthcheck_email_preview.html")
            if os.path.exists(preview_path):
                try:
                    with open(preview_path, "rb") as f:
                        data = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except Exception as e:
                    self._json(500, {"error": str(e)})
            else:
                self._json(404, {"error": "healthcheck_email_preview.html not found"})
            return
        if parsed.path in ("/reporting.csv", "/Reporting.csv"):
            # Serve the Reporting.csv file content if present
            report_path = os.path.join(WORKSPACE_ROOT, "Reporting.csv")
            if os.path.exists(report_path):
                try:
                    with open(report_path, "rb") as f:
                        data = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except Exception as e:
                    self._json(500, {"error": str(e)})
            else:
                self._json(404, {"error": "Reporting.csv not found"})
            return
        if parsed.path == "/proxy":
            try:
                qs = parse_qs(parsed.query)
                url = (qs.get("url") or [""])[0]
                if not url:
                    self._json(400, {"error": "Missing 'url'"})
                    return
                # Basic allowlist: only allow Google Docs/Sheets CSV publishes
                if not (url.startswith("https://docs.google.com/") or url.startswith("http://docs.google.com/")):
                    self._json(400, {"error": "URL not allowed"})
                    return
                req = urllib.request.Request(url)
                req.add_header("User-Agent", "JiraAgent/1.0 (+Windows) Python-urllib")
                req.add_header("Accept", "text/csv, */*")
                # Use system proxies if set (HTTPS_PROXY/HTTP_PROXY)
                proxies = {}
                hp = os.environ.get("HTTP_PROXY", "").strip()
                sp = os.environ.get("HTTPS_PROXY", "").strip()
                if hp:
                    proxies["http"] = hp
                if sp:
                    proxies["https"] = sp
                ctx = ssl.create_default_context()
                handlers = [urllib.request.HTTPSHandler(context=ctx)]
                if proxies:
                    handlers.insert(0, urllib.request.ProxyHandler(proxies))
                opener = urllib.request.build_opener(*handlers)
                with opener.open(req) as resp:
                    data = resp.read()
                    self.send_response(200)
                    self.send_header("Content-Type", resp.headers.get("Content-Type", "text/plain"))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
            except Exception as e:
                try:
                    msg = str(e)
                except Exception:
                    msg = ""
                print(f"[MCP Server] /proxy error: {msg}")
                self._json(500, {"error": str(e)})
            return
        if parsed.path in ("/", "/index.html", "/ui", "/ui/index.html"):
            # Serve View Hierarchy page by default
            self._static_html(UI_ORDER_VALIDATION_PATH)
            return
        if parsed.path in ("/order-validation", "/ui/order_validation.html"):
            self._static_html(UI_ORDER_VALIDATION_PATH)
            return
        if parsed.path in ("/healthcheck", "/ui/healthcheck.html"):
            self._static_html(UI_HEALTHCHECK_PATH)
            return
        if parsed.path in ("/queue-snapshot", "/ui/queue_snapshot.html"):
            self._static_html(UI_QUEUE_SNAPSHOT_PATH)
            return
        if parsed.path == "/releaseplan/vcg-milestones-2026":
            try:
                url = "https://releaseplan.ebiz.verizon.com/uploads/files/keymilestones.pdf"
                pdf_bytes = _fetch_binary(url)
                rows = parse_vcg_milestones_pdf(pdf_bytes)
                out_path = os.path.join(WORKSPACE_ROOT, "vcg_milestones_2026.json")
                try:
                    with open(out_path, "w", encoding="utf-8") as f:
                        json.dump({"source": url, "count": len(rows), "rows": rows}, f, indent=2)
                except Exception:
                    out_path = None
                self._json(200, {"source": url, "count": len(rows), "rows": rows, "saved": out_path or ""})
            except urllib.error.HTTPError as e:
                err = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
                self._json(e.code, {"error": err})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        # Confluence: search and page fetch
        if parsed.path == "/confluence/search":
            qs = parse_qs(parsed.query)
            q = (qs.get("q") or [""])[0]
            space = (qs.get("space") or [""])[0]
            limit = int((qs.get("limit") or ["10"])[0])
            strict = (qs.get("strict") or [""])[0]
            if not (CONFLUENCE_BASE_URL and CONFLUENCE_USERNAME and CONFLUENCE_TOKEN):
                self._json(200, {"isMock": True, "results": [], "error": "Missing Confluence envs: CONFLUENCE_BASE_URL/USERNAME/TOKEN"})
                return
            try:
                # Build CQL from tokens: strict=AND, broad=OR; filter by spaceKey if provided
                cql = "type = page"
                if q:
                    import re
                    raw = re.sub(r"[^A-Za-z0-9]+"," ", str(q))
                    tokens = [t for t in raw.split() if len(t)>=3]
                    def esc(s):
                        return str(s).replace('"','\\"')
                    if tokens:
                        if strict:
                            and_text = " AND ".join([f'text ~ "{esc(t)}"' for t in tokens[:4]])
                            and_title = " AND ".join([f'title ~ "{esc(t)}"' for t in tokens[:4]])
                            cql = f'(({and_text}) OR ({and_title}))'
                        else:
                            or_text = " OR ".join([f'text ~ "{esc(t)}"' for t in tokens])
                            or_title = " OR ".join([f'title ~ "{esc(t)}"' for t in tokens])
                            cql = f'(({or_text}) OR ({or_title}))'
                if space:
                    # Quote space key in CQL to be safe
                    cql = f"space = \"{space}\" AND {cql}"
                elif CONFLUENCE_DEFAULT_SPACES:
                    spaces_or = " OR ".join([f"space = \"{s}\"" for s in CONFLUENCE_DEFAULT_SPACES])
                    cql = f"({spaces_or}) AND {cql}"
                params = {
                    "cql": cql,
                    "limit": str(max(1, min(limit, 50)))
                }
                url = f"{CONFLUENCE_BASE_URL}/rest/api/search?{urllib.parse.urlencode(params)}"
                auth = b64encode(f"{CONFLUENCE_USERNAME}:{CONFLUENCE_TOKEN}".encode()).decode()
                req = urllib.request.Request(url)
                req.add_header("Authorization", f"Basic {auth}")
                req.add_header("Accept", "application/json")
                ctx = ssl.create_default_context()
                with urllib.request.urlopen(req, context=ctx) as resp:
                    data = resp.read().decode("utf-8")
                    j = json.loads(data)
                    results = j.get("results", [])
                    # Normalize minimal fields for UI
                    out = []
                    for r in results:
                        if not isinstance(r, dict):
                            continue
                        title = r.get("title") or r.get("content", {}).get("title")
                        content = r.get("content") or {}
                        cid = content.get("id") or r.get("id")
                        link = r.get("_links", {}).get("webui") or content.get("_links", {}).get("webui")
                        abs_link = None
                        if isinstance(link, str) and link:
                            # Confluence typically returns relative webui links; prefix base URL
                            abs_link = (CONFLUENCE_BASE_URL.rstrip('/') + '/' + link.lstrip('/'))
                        out.append({"id": cid, "title": title, "link": link, "absoluteLink": abs_link})
                    # Fallback to content search if generic search returns empty
                    if not out:
                        url2 = f"{CONFLUENCE_BASE_URL}/rest/api/content/search?{urllib.parse.urlencode(params)}"
                        req2 = urllib.request.Request(url2)
                        req2.add_header("Authorization", f"Basic {auth}")
                        req2.add_header("Accept", "application/json")
                        with urllib.request.urlopen(req2, context=ctx) as resp2:
                            data2 = resp2.read().decode("utf-8")
                            j2 = json.loads(data2)
                            arr = j2.get("results") or j2.get("content") or []
                            out2 = []
                            for c in arr:
                                if not isinstance(c, dict):
                                    continue
                                cid = c.get("id")
                                title = c.get("title")
                                link = (c.get("_links") or {}).get("webui")
                                abs_link = None
                                if isinstance(link, str) and link:
                                    abs_link = (CONFLUENCE_BASE_URL.rstrip('/') + '/' + link.lstrip('/'))
                                out2.append({"id": cid, "title": title, "link": link, "absoluteLink": abs_link})
                            out = out2
                    self._json(200, {"results": out, "cql": cql})
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
                self._json(e.code, {"error": err_text})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        if parsed.path == "/debug/confluence":
            self._json(200, {
                "CONFLUENCE_BASE_URL": CONFLUENCE_BASE_URL,
                "CONFLUENCE_USERNAME": bool(CONFLUENCE_USERNAME),
                "CONFLUENCE_TOKEN_set": bool(CONFLUENCE_TOKEN),
                "CONFLUENCE_DEFAULT_SPACES": CONFLUENCE_DEFAULT_SPACES,
            })
            return
        if parsed.path == "/confluence/page":
            qs = parse_qs(parsed.query)
            cid = (qs.get("id") or [""])[0]
            if not cid:
                self._json(400, {"error": "Missing 'id'"})
                return
            if not (CONFLUENCE_BASE_URL and CONFLUENCE_USERNAME and CONFLUENCE_TOKEN):
                self._json(200, {"isMock": True, "id": cid, "title": "Mock Page", "html": "<p>Mock content</p>"})
                return
            try:
                url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{urllib.parse.quote(cid)}?expand=body.storage,title"
                auth = b64encode(f"{CONFLUENCE_USERNAME}:{CONFLUENCE_TOKEN}".encode()).decode()
                req = urllib.request.Request(url)
                req.add_header("Authorization", f"Basic {auth}")
                req.add_header("Accept", "application/json")
                ctx = ssl.create_default_context()
                with urllib.request.urlopen(req, context=ctx) as resp:
                    data = resp.read().decode("utf-8")
                    j = json.loads(data)
                    title = j.get("title")
                    storage = ((j.get("body") or {}).get("storage") or {}).get("value")
                    self._json(200, {"id": cid, "title": title, "html": storage})
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
                self._json(e.code, {"error": err_text})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        if parsed.path == "/confluence/summarize":
            qs = parse_qs(parsed.query)
            key = (qs.get("key") or [""])[0]
            space = (qs.get("space") or [""])[0]
            limit = int((qs.get("limit") or ["5"])[0])
            strict = (qs.get("strict") or [""])[0]
            if not key:
                self._json(400, {"error": "Missing 'key'"})
                return
            if not (CONFLUENCE_BASE_URL and CONFLUENCE_USERNAME and CONFLUENCE_TOKEN):
                self._json(200, {"isMock": True, "summary": "", "pages": []})
                return
            try:
                # Use Jira issue details to seed tokens
                base = fetch_issue_details(key)
                tokens = tokenize_for_jql_public((base.get("summary") or "") + " " + (base.get("description") or ""))
                # Build CQL: prefer token-based queries with AND across multiple tokens
                toks = tokens[:6]
                def esc(s):
                    return str(s).replace('"','\\"')
                cql = "type = page"
                if toks:
                    if strict:
                        # Strict: AND across tokens
                        and_clause_text = " AND ".join([f'text ~ "{esc(t)}"' for t in toks[:4]])
                        and_clause_title = " AND ".join([f'title ~ "{esc(t)}"' for t in toks[:4]])
                        cql = f'(({and_clause_text}) OR ({and_clause_title}))'
                    else:
                        # Broad: OR across tokens
                        or_clause_text = " OR ".join([f'text ~ "{esc(t)}"' for t in toks])
                        or_clause_title = " OR ".join([f'title ~ "{esc(t)}"' for t in toks])
                        cql = f'(({or_clause_text}) OR ({or_clause_title}))'
                sp = (space or (CONFLUENCE_DEFAULT_SPACES[0] if CONFLUENCE_DEFAULT_SPACES else "")).strip()
                if sp:
                    cql = f"space = \"{sp}\" AND {cql}"
                params = {"cql": cql, "limit": str(max(1, min(limit, 10)))}
                url = f"{CONFLUENCE_BASE_URL}/rest/api/search?{urllib.parse.urlencode(params)}"
                auth = b64encode(f"{CONFLUENCE_USERNAME}:{CONFLUENCE_TOKEN}".encode()).decode()
                req = urllib.request.Request(url)
                req.add_header("Authorization", f"Basic {auth}")
                req.add_header("Accept", "application/json")
                ctx = ssl.create_default_context()
                pages = []
                with urllib.request.urlopen(req, context=ctx) as resp:
                    data = resp.read().decode("utf-8")
                    j = json.loads(data)
                    results = j.get("results", [])
                    for r in results[:limit]:
                        content = r.get("content") or {}
                        cid = content.get("id") or r.get("id")
                        title = r.get("title") or content.get("title")
                        if not cid:
                            continue
                        # Fetch storage for each page to summarize
                        urlp = f"{CONFLUENCE_BASE_URL}/rest/api/content/{urllib.parse.quote(str(cid))}?expand=body.storage,title"
                        reqp = urllib.request.Request(urlp)
                        reqp.add_header("Authorization", f"Basic {auth}")
                        reqp.add_header("Accept", "application/json")
                        with urllib.request.urlopen(reqp, context=ctx) as resp2:
                            data2 = resp2.read().decode("utf-8")
                            j2 = json.loads(data2)
                            html = ((j2.get("body") or {}).get("storage") or {}).get("value") or ""
                            text = _html_to_text(html)
                            structure = _extract_structure(html)
                            pages.append({"id": str(cid), "title": title, "text": text, "structure": structure})
                # If no pages found, retry with alternative mode
                if not pages and toks:
                    or_text = " OR ".join([f'text ~ "{esc(t)}"' for t in toks])
                    or_title = " OR ".join([f'title ~ "{esc(t)}"' for t in toks])
                    cql = f'(({or_text}) OR ({or_title}))'
                    if sp:
                        cql = f"space = \"{sp}\" AND {cql}"
                    params = {"cql": cql, "limit": str(max(1, min(limit, 10)))}
                    url = f"{CONFLUENCE_BASE_URL}/rest/api/search?{urllib.parse.urlencode(params)}"
                    req = urllib.request.Request(url)
                    req.add_header("Authorization", f"Basic {auth}")
                    req.add_header("Accept", "application/json")
                    with urllib.request.urlopen(req, context=ctx) as resp:
                        data = resp.read().decode("utf-8")
                        j = json.loads(data)
                        results = j.get("results", [])
                        for r in results[:limit]:
                            content = r.get("content") or {}
                            cid = content.get("id") or r.get("id")
                            title = r.get("title") or content.get("title")
                            if not cid:
                                continue
                            urlp = f"{CONFLUENCE_BASE_URL}/rest/api/content/{urllib.parse.quote(str(cid))}?expand=body.storage,title"
                            reqp = urllib.request.Request(urlp)
                            reqp.add_header("Authorization", f"Basic {auth}")
                            reqp.add_header("Accept", "application/json")
                            with urllib.request.urlopen(reqp, context=ctx) as resp2:
                                data2 = resp2.read().decode("utf-8")
                                j2 = json.loads(data2)
                                html = ((j2.get("body") or {}).get("storage") or {}).get("value") or ""
                                text = _html_to_text(html)
                                structure = _extract_structure(html)
                                pages.append({"id": str(cid), "title": title, "text": text, "structure": structure})
                # Combine texts and produce short summary
                combined = "\n\n".join([p.get("text", "") for p in pages])
                jira_comments = (base.get("consolidatedComments") or "")
                import re as _re
                words = [w for w in _re.sub(r"[^A-Za-z0-9]+"," ", jira_comments).split() if len(w)>=3]
                bigrams = [" ".join([words[i], words[i+1]]) for i in range(len(words)-1)]
                uniq_phrases = []
                seen = set()
                for ph in bigrams:
                    l = ph.lower()
                    if l not in seen:
                        seen.add(l)
                        uniq_phrases.append(ph)
                    if len(uniq_phrases) >= 12:
                        break
                sentences = _re.split(r"(?<=[.!?])\s+", combined)
                qt = [q.lower() for q in (tokens or [])]
                scored = []
                for s in sentences:
                    sl = s.lower()
                    hits = sum(1 for q in qt if q and q in sl)
                    score = hits * 2 + min(len(s), 300) / 300
                    if s.strip():
                        scored.append((score, s.strip()))
                scored = _boost_by_phrases(scored, uniq_phrases)
                top = [s for _, s in sorted(scored, key=lambda x: x[0], reverse=True)[:8]]
                summary = "\n".join(top)
                self._json(200, {"key": key, "cql": cql, "pages": pages, "summary": summary, "phrases": uniq_phrases})
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
                self._json(e.code, {"error": err_text})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return

        if parsed.path == "/rca/system":
            qs = parse_qs(parsed.query)
            key = (qs.get("key") or [""])[0]
            space = (qs.get("space") or [""])[0]
            strict = (qs.get("strict") or [""])[0]
            if not key:
                self._json(400, {"error": "Missing 'key'"})
                return
            try:
                # Current defect text
                issue = fetch_issue_details(key)
                cur_text = " ".join([
                    str(issue.get("summary") or ""),
                    str(issue.get("description") or ""),
                    str(issue.get("consolidatedComments") or ""),
                ])
                # Similar defects (use defaults) and collect comments only
                project_keys = [
                    os.environ.get("DEFAULT_PROJECT_1", "CXPOPER"),
                    os.environ.get("DEFAULT_PROJECT_2", "PRODDEF"),
                    os.environ.get("DEFAULT_PROJECT_3", "CXTDT"),
                    os.environ.get("DEFAULT_PROJECT_4", "NSADT"),
                ]
                similar = search_similar_issues(key, project_keys, max_results=10)
                sim_comments = []
                for it in similar.get("issues", [])[:6]:
                    k = it.get("key")
                    if k:
                        try:
                            det = fetch_issue_details(k)
                            sim_comments.append(str(det.get("consolidatedComments") or ""))
                        except Exception:
                            pass
                # Confluence summary
                conf = {"summary":"","pages":[]}
                try:
                    sp = (space or (CONFLUENCE_DEFAULT_SPACES[0] if CONFLUENCE_DEFAULT_SPACES else ""))
                    params = {"key": key, "space": sp, "limit": "5"}
                    # Call local function pipeline directly
                    base = fetch_issue_details(key)
                    tokens = tokenize_for_jql_public((base.get("summary") or "") + " " + (base.get("description") or ""))
                    toks = tokens[:6]
                    def esc(s): return str(s).replace('"','\\"')
                    cql = "type = page"
                    if toks:
                        if strict:
                            and_text = " AND ".join([f'text ~ "{esc(t)}"' for t in toks[:4]])
                            and_title = " AND ".join([f'title ~ "{esc(t)}"' for t in toks[:4]])
                            cql = f'(({and_text}) OR ({and_title}))'
                        else:
                            or_text = " OR ".join([f'text ~ "{esc(t)}"' for t in toks])
                            or_title = " OR ".join([f'title ~ "{esc(t)}"' for t in toks])
                            cql = f'(({or_text}) OR ({or_title}))'
                    if sp:
                        cql = f"space = \"{sp}\" AND {cql}"
                    url = f"{CONFLUENCE_BASE_URL}/rest/api/search?{urllib.parse.urlencode({'cql': cql, 'limit': '5'})}"
                    auth = b64encode(f"{CONFLUENCE_USERNAME}:{CONFLUENCE_TOKEN}".encode()).decode()
                    req = urllib.request.Request(url)
                    req.add_header("Authorization", f"Basic {auth}")
                    req.add_header("Accept", "application/json")
                    ctx = ssl.create_default_context()
                    pages = []
                    with urllib.request.urlopen(req, context=ctx) as resp:
                        data = resp.read().decode("utf-8")
                        j = json.loads(data)
                        results = j.get("results", [])
                        for r in results[:5]:
                            content = r.get("content") or {}
                            cid = content.get("id") or r.get("id")
                            title = r.get("title") or content.get("title")
                            if not cid:
                                continue
                            urlp = f"{CONFLUENCE_BASE_URL}/rest/api/content/{urllib.parse.quote(str(cid))}?expand=body.storage,title"
                            reqp = urllib.request.Request(urlp)
                            reqp.add_header("Authorization", f"Basic {auth}")
                            reqp.add_header("Accept", "application/json")
                            with urllib.request.urlopen(reqp, context=ctx) as resp2:
                                data2 = resp2.read().decode("utf-8")
                                j2 = json.loads(data2)
                                html = ((j2.get("body") or {}).get("storage") or {}).get("value") or ""
                                text = _html_to_text(html)
                                pages.append({"id": str(cid), "title": title, "text": text})
                    conf = {"summary": "\n\n".join([p.get("text","") for p in pages]), "pages": pages}
                except Exception:
                    pass
                # Aggregate text for scoring (ignore components/workowner entirely)
                all_text = "\n\n".join([cur_text] + sim_comments + [conf.get("summary") or ""])
                scores = _score_system(all_text)
                # Determine winner and confidence
                system = max(scores, key=lambda k: scores[k]) if scores else None
                max_score = scores.get(system, 0) if system else 0
                # Confidence tiers
                conf_level = "Low"
                if max_score >= 8:
                    conf_level = "High"
                elif max_score >= 4:
                    conf_level = "Medium"
                # Build rationale snippets
                evidence = []
                def collect_lines(text_src, label):
                    for line in str(text_src or "").split("\n"):
                        l = line.strip().lower()
                        if not l:
                            continue
                        # include lines that mention the chosen system or aliases
                        aliases = SYSTEM_ALIASES.get(system, []) if system else []
                        if system and (system.lower() in l or any(a in l for a in aliases)):
                            evidence.append({"source": label, "text": line.strip()[:200]})
                            if len(evidence) >= 6:
                                return
                collect_lines(issue.get("consolidatedComments"), "Current Defect")
                for sc in sim_comments:
                    if len(evidence) >= 6:
                        break
                    collect_lines(sc, "Old Defect")
                if conf.get("summary"):
                    collect_lines(conf.get("summary"), "Confluence")
                self._json(200, {
                    "key": key,
                    "system": system,
                    "confidence": conf_level,
                    "scores": scores,
                    "evidence": evidence,
                    "strict": bool(strict),
                })
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
                self._json(e.code, {"error": err_text})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        if parsed.path == "/jira/latest-comment":
            qs = parse_qs(parsed.query)
            key = (qs.get("key") or [""])[0]
            if not key:
                self._json(400, {"error": "Missing 'key' query parameter"})
                return
            try:
                result = fetch_latest_comment(key)
                self._json(200, result)
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        if parsed.path == "/debug/env":
            self._json(200, {
                "JIRA_BASE_URL": JIRA_BASE_URL,
                "JIRA_EMAIL": JIRA_EMAIL,
                "JIRA_API_VERSION": JIRA_API_VERSION,
                "JIRA_API_TOKEN_set": bool(JIRA_API_TOKEN),
                "JIRA_MOCK": JIRA_MOCK,
                "JIRA_AUTH_MODE": JIRA_AUTH_MODE,
                "JIRA_BEARER_TOKEN_set": bool(JIRA_BEARER_TOKEN),
                "JIRA_COOKIE_set": bool(JIRA_COOKIE),
            })
            return
        if parsed.path == "/jira/issues":
            qs = parse_qs(parsed.query)
            project = (qs.get("project") or [""])[0]
            max_results_str = (qs.get("maxResults") or ["25"])[0]
            start_at_str = (qs.get("startAt") or ["0"])[0]
            assigned_to = (qs.get("assignedTo") or [None])[0]
            issue_type = (qs.get("type") or [None])[0]
            status = (qs.get("status") or [None])[0]
            priority = (qs.get("priority") or [None])[0]
            print(f"[MCP Server] /jira/issues params: project={project!r}, assignedTo={assigned_to!r}, type={issue_type!r}, status={status!r}, priority={priority!r}, maxResults={max_results_str}, startAt={start_at_str}")
            try:
                max_results = int(max_results_str)
            except ValueError:
                max_results = 25
            try:
                start_at = int(start_at_str)
            except ValueError:
                start_at = 0

            if not project:
                self._json(400, {"error": "Missing 'project' query parameter"})
                return
            try:
                issues = fetch_jira_issues(project, max_results, start_at=start_at, assigned_to=assigned_to, issue_type=issue_type, status=status, priority=priority)
                self._json(200, issues)
            except Exception as e:
                print(f"[MCP Server] Error in /jira/issues: {e}")
                self._json(500, {"error": str(e)})
            return

        if parsed.path == "/jira/attachments":
            qs = parse_qs(parsed.query)
            key = (qs.get("key") or [""])[0]
            if not key:
                self._json(400, {"error": "Missing 'key' query parameter"})
                return
            try:
                result = fetch_issue_attachments(key)
                self._json(200, result)
            except Exception as e:
                self._json(500, {"error": str(e)})
            return

        if parsed.path == "/jira/issue-details":
            qs = parse_qs(parsed.query)
            key = (qs.get("key") or [""])[0]
            if not key:
                self._json(400, {"error": "Missing 'key' query parameter"})
                return
            try:
                result = fetch_issue_details(key)
                self._json(200, result)
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
                self._json(e.code, {"error": err_text or f"HTTPError {e.code}"})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return

        if parsed.path == "/jira/search-similar":
            qs = parse_qs(parsed.query)
            key = (qs.get("key") or [""])[0]
            projects = (qs.get("projects") or [""])[0]
            max_results = int((qs.get("maxResults") or ["20"])[0])
            strict = (qs.get("strict") or [""])[0]
            if not key:
                self._json(400, {"error": "Missing 'key' query parameter"})
                return
            # projects may be CSV of project keys; default to known four if blank
            if not projects:
                project_keys = [
                    os.environ.get("DEFAULT_PROJECT_1", "CXPOPER"),
                    os.environ.get("DEFAULT_PROJECT_2", "PRODDEF"),
                    os.environ.get("DEFAULT_PROJECT_3", "CXTDT"),
                    os.environ.get("DEFAULT_PROJECT_4", "NSADT"),
                ]
            else:
                project_keys = [p.strip() for p in projects.split(',') if p.strip()]
            try:
                result = search_similar_issues(key, project_keys, max_results)
                # If strict requested, filter out results that do not contain ALL tokens in summary or description
                if strict:
                    base = fetch_issue_details(key)
                    def _tokens(s):
                        return set(tokenize_for_jql_public(str(s or "")))
                    # Recompute tokens based on description/summary
                    tdesc = _tokens(base.get("description"))
                    tsum = _tokens(base.get("summary"))
                    needed = tdesc or tsum
                    if needed:
                        filtered = []
                        for it in result.get("issues", []):
                            f = it.get("fields", {})
                            s = (f.get("summary") or "")
                            d = (f.get("description") or "")
                            text = f"{s} {d}"
                            have = _tokens(text)
                            if needed.issubset(have):
                                filtered.append(it)
                        result["issues"] = filtered
                self._json(200, result)
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
                self._json(e.code, {"error": err_text or f"HTTPError {e.code}"})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return

        if parsed.path == "/jira/fields":
            try:
                m = fetch_fields_map()
                self._json(200, m)
            except Exception as e:
                self._json(500, {"error": str(e)})
            return

        if parsed.path == "/jira/project-components":
            qs = parse_qs(parsed.query)
            pkey = (qs.get("projectKey") or [""])[0]
            if not pkey:
                self._json(400, {"error": "Missing 'projectKey'"})
                return
            try:
                print(f"[MCP Server] /jira/project-components projectKey={pkey!r}")
                comps = fetch_project_components(pkey)
                self._json(200, {"components": comps})
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
                self._json(e.code, {"error": err_text or f"HTTPError {e.code}"})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return

        if parsed.path == "/jira/projects":
            try:
                projects = fetch_projects()
                self._json(200, {"projects": projects})
            except Exception as e:
                # Be lenient: return empty list on Jira auth/network errors to keep UI functional
                try:
                    msg = str(e)
                except Exception:
                    msg = ""
                print(f"[MCP Server] /jira/projects fallback: {msg}")
                self._json(200, {"projects": [], "error": msg})
            return

        if parsed.path == "/jira/workowner-options":
            qs = parse_qs(parsed.query)
            pkey = (qs.get("projectKey") or [""])[0]
            max_results_str = (qs.get("maxResults") or ["200"])[0]
            jql_override = (qs.get("jql") or [None])[0]
            if not pkey:
                self._json(400, {"error": "Missing 'projectKey'"})
                return
            try:
                try:
                    mres = int(max_results_str)
                except ValueError:
                    mres = 200
                opts = fetch_work_owner_options(pkey, max_results=mres, jql_override=jql_override)
                self._json(200, opts)
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
                self._json(e.code, {"error": err_text})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return

        self._json(404, {"error": "Not Found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/mail/send":
            # Send an email with HTML body using SMTP envs
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8"))
                to_addr = (payload.get("to") or "").strip()
                cc_val = payload.get("cc")
                # cc can be a string comma-separated or a list
                if isinstance(cc_val, str):
                    cc_list = [a.strip() for a in cc_val.split(",") if a.strip()]
                elif isinstance(cc_val, list):
                    cc_list = [str(a).strip() for a in cc_val if str(a).strip()]
                else:
                    cc_list = []
                subject = (payload.get("subject") or "CJCM Healthcheck").strip()
                html_body = payload.get("html") or ""
                SMTP_HOST = os.environ.get("SMTP_HOST", "")
                SMTP_PORT = int(os.environ.get("SMTP_PORT", "587") or "587")
                SMTP_USER = os.environ.get("SMTP_USER", "")
                SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
                SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER or "")
                SMTP_TLS = os.environ.get("SMTP_TLS", "auto").lower()  # 'auto' | 'on' | 'off'
                if not to_addr:
                    self._json(400, {"error": "Missing 'to'"})
                    return
                if SMTP_HOST and SMTP_FROM:
                    try:
                        import smtplib
                        from email.mime.multipart import MIMEMultipart
                        from email.mime.text import MIMEText
                        msg = MIMEMultipart('alternative')
                        msg['Subject'] = subject
                        msg['From'] = SMTP_FROM
                        msg['To'] = to_addr
                        if cc_list:
                            msg['Cc'] = ", ".join(cc_list)
                        part = MIMEText(html_body, 'html')
                        msg.attach(part)
                        recipients = [to_addr] + cc_list
                        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
                            # Decide TLS behavior: auto enables TLS for non-25; off disables; on forces
                            use_tls = (SMTP_TLS == 'on') or (SMTP_TLS == 'auto' and SMTP_PORT != 25)
                            if use_tls:
                                try:
                                    server.starttls()
                                except Exception as e:
                                    print(f"[MCP Server] /mail/send starttls warning: {e}")
                            if SMTP_USER and SMTP_PASSWORD:
                                server.login(SMTP_USER, SMTP_PASSWORD)
                            server.sendmail(SMTP_FROM, recipients, msg.as_string())
                        self._json(200, {"ok": True, "sent": True})
                        return
                    except Exception as e:
                        # Fall through to preview
                        print(f"[MCP Server] /mail/send SMTP error: {e}")
                # Preview fallback: write HTML to workspace and return URL to view
                try:
                    preview_path = os.path.join(WORKSPACE_ROOT, "healthcheck_email_preview.html")
                    with open(preview_path, "w", encoding="utf-8") as f:
                        f.write(html_body)
                    self._json(200, {"ok": False, "previewPath": preview_path, "previewUrl": "/preview/healthcheck-email"})
                except Exception as e:
                    self._json(500, {"error": str(e)})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        if parsed.path == "/repo/push":
            # Stage, commit, and push repo changes. Body: {commitMessage?, pushGitHub?, pushGitLab?}
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8"))
                msg = (payload.get("commitMessage") or "Auto-commit from UI")
                push_github = bool(payload.get("pushGitHub", True))
                push_gitlab = bool(payload.get("pushGitLab", False))
                def run(cmd, cwd=WORKSPACE_ROOT):
                    print(f"[MCP Server] git cmd: {cmd}")
                    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
                    return {"code": p.returncode, "out": p.stdout, "err": p.stderr}
                results = {}
                # Stage all
                results["add"] = run("git add -A")
                # Check for changes
                status = run("git status --porcelain")
                results["status"] = status
                if status.get("out", "").strip():
                    #results["commit"] = run(f"git commit -m \"{msg.replace('\\','/').replace('"','\\"')}\"")
                    # Use single quotes for the f-string to avoid quote conflicts inside replace()
                    results["commit"] = run(f'git commit -m "{msg.replace("\\","/").replace("\"", "\\\"")}"')
                else:
                    results["commit"] = {"code": 0, "out": "No changes to commit", "err": ""}
                # Push to GitHub (origin)
                if push_github:
                    results["push_origin"] = run("git push origin main")
                # Push to GitLab (gitlab remote)
                if push_gitlab:
                    results["push_gitlab"] = run("git push gitlab main")
                self._json(200, {"ok": True, "results": results})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        if parsed.path == "/oracle/query":
            # Execute a read-only SELECT with optional named binds and return rows
            try:
                if oracledb is None:
                    self._json(500, {"error": "oracledb is not installed. Run: pip install -r mcp-server/requirements.txt"})
                    return
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8"))
                sql = (payload.get("sql") or "").strip()
                params = payload.get("params") or {}
                max_rows = int(payload.get("maxRows") or 1000)
                if not sql:
                    self._json(400, {"error": "Missing 'sql' in body"})
                    return
                # Basic safety: only allow SELECT statements
                upper_sql = sql.strip().upper()
                if not upper_sql.startswith("SELECT ") and not upper_sql.startswith("WITH "):
                    self._json(400, {"error": "Only SELECT statements are allowed"})
                    return
                if not (ORACLE_DSN and ORACLE_USER and ORACLE_PASSWORD):
                    self._json(500, {"error": "Oracle env not set. Provide ORACLE_DSN, ORACLE_USER, ORACLE_PASSWORD"})
                    return
                # Prepare binds and log incoming request to terminal
                bind_params = {str(k): v for k, v in (params.items() if isinstance(params, dict) else {})}
                preview_sql = sql if len(sql) <= 800 else (sql[:800] + "...")
                print(f"[MCP Server] /oracle/query incoming: maxRows={max_rows} | params={bind_params!r}\nSQL: {preview_sql}")
                # Connect and run with one retry on transient network disconnects
                print(f"[MCP Server] /oracle/query using DSN={ORACLE_DSN!r} user={ORACLE_USER!r}")
                def attempt():
                    conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)
                    try:
                        cur = conn.cursor()
                        try:
                            cur.arraysize = max(100, min(max_rows, 1000))
                        except Exception:
                            pass
                        try:
                            cur.prefetchrows = max(100, min(max_rows, 1000))
                        except Exception:
                            pass
                        t0 = time.time()
                        # Optional ping to preempt closed sockets
                        try:
                            conn.ping()
                        except Exception:
                            pass
                        cur.execute(sql, bind_params)
                        t1 = time.time()
                        cols = [d[0] for d in (cur.description or [])]
                        rows_raw = cur.fetchmany(max_rows)
                        rows = [[None if v is None else (v.isoformat() if hasattr(v, 'isoformat') else v) for v in r] for r in rows_raw]
                        count = len(rows)
                        t2 = time.time()
                        exec_time = t1 - t0
                        fetch_time = t2 - t1
                        total_time = t2 - t0
                        print(f"[MCP Server] /oracle/query ok: rows={count} cols={len(cols)} exec={exec_time:.3f}s fetch={fetch_time:.3f}s total={total_time:.3f}s")
                        return {"columns": cols, "rows": rows}
                    finally:
                        try:
                            conn.close()
                        except Exception:
                            pass
                try:
                    result = attempt()
                    self._json(200, result)
                except Exception as e1:
                    em = str(e1).lower() if e1 else ""
                    if ("dpy-4011" in em) or ("10054" in em) or ("connection was forcibly closed" in em) or ("closed the connection" in em):
                        print("[MCP Server] /oracle/query transient disconnect, retrying once...")
                        time.sleep(0.3)
                        try:
                            result = attempt()
                            self._json(200, result)
                            return
                        except Exception as e2:
                            raise e2
                    else:
                        raise e1
            except Exception as e:
                # Improve diagnostics for DNS resolution failures
                try:
                    msg = str(e)
                except Exception:
                    msg = ""
                dns_hint = None
                try:
                    # Detect getaddrinfo failures and include DSN/host guidance
                    em = msg.lower()
                    if "getaddrinfo failed" in em or isinstance(e, socket.gaierror):
                        def extract_host(dsn_str: str):
                            s = (dsn_str or "").strip()
                            if not s:
                                return None
                            if "(DESCRIPTION=" not in s and "HOST=" not in s:
                                return s.split("/")[0].split(":")[0]
                            import re
                            m = re.search(r"HOST\s*=\s*([^\)\s]+)", s, flags=re.IGNORECASE)
                            return m.group(1) if m else None
                        host = extract_host(ORACLE_DSN)
                        dns_hint = {
                            "message": "DNS resolution failed for Oracle host",
                            "dsn": ORACLE_DSN,
                            "host": host or "",
                            "suggestions": [
                                "Verify VPN/corporate network is connected",
                                "Use the DB host IP instead of hostname in ORACLE_DSN",
                                "Add host entry in C:\\Windows\\System32\\drivers\\etc\\hosts if appropriate",
                                "Confirm local DNS/proxy does not block internal domains"
                            ]
                        }
                except Exception:
                    pass
                if dns_hint:
                    print(f"[MCP Server] /oracle/query DNS error: {dns_hint}")
                    self._json(500, {"error": msg, "dns": dns_hint})
                else:
                    print(f"[MCP Server] /oracle/query error: {msg}")
                    self._json(500, {"error": msg})
            return
        if parsed.path == "/validate/log":
            # Log validation results to terminal for each row
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8"))
                columns = payload.get("columns") or []
                rows = payload.get("rows") or []
                ids = payload.get("ids") or {}
                # Print header/context
                print("[MCP Server] /validate/log context:", ids)
                # Print each row in a readable format
                # Map indices for common columns (support both old and new schemas)
                up = [str(c or '').upper() for c in columns]
                # Old schema fields
                i_res_old = up.index('RESULT') if 'RESULT' in up else -1
                i_step_old = up.index('ENTITYSTEP') if 'ENTITYSTEP' in up else -1
                i_status_old = up.index('WORKOBJECTSTATUS') if 'WORKOBJECTSTATUS' in up else -1
                # New schema fields
                i_val = up.index('VALIDATIONSTATUS') if 'VALIDATIONSTATUS' in up else -1
                i_step_new = up.index('OH_ENTITYSTEP') if 'OH_ENTITYSTEP' in up else (up.index('ENTITYSTEP') if 'ENTITYSTEP' in up else -1)
                i_status_new = up.index('OH_WORKOBJECTSTATUS') if 'OH_WORKOBJECTSTATUS' in up else (up.index('WORKOBJECTSTATUS') if 'WORKOBJECTSTATUS' in up else -1)
                for idx, r in enumerate(rows):
                    try:
                        # Prefer new schema
                        val = r[i_val] if i_val >= 0 else (r[i_res_old] if i_res_old >= 0 else '')
                        step = r[i_step_new] if i_step_new >= 0 else (r[i_step_old] if i_step_old >= 0 else '')
                        status = r[i_status_new] if i_status_new >= 0 else (r[i_status_old] if i_status_old >= 0 else '')
                        print(f"[VALIDATE] row={idx+1} entitystep={step} workobjectstatus={status} validationstatus={val}")
                    except Exception as e:
                        print(f"[VALIDATE] row={idx+1} print error: {e}")
                self._json(200, {"ok": True, "logged": len(rows)})
            except Exception as e:
                try:
                    msg = str(e)
                except Exception:
                    msg = ""
                print(f"[MCP Server] /validate/log error: {msg}")
                self._json(500, {"error": msg})
            return
        if parsed.path == "/reporting/append":
            # Append a single summary row to Reporting.csv: CARTID, ORDERNUMBER, LOCATIONCODE, TIMESTAMP
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8"))
                ids = payload.get("ids") or {}
                downloaded_file = payload.get("downloadedFile") or ""
                try:
                    print(f"[MCP Server] /reporting/append received: ids_cartid={ids.get('cartid','')} file={downloaded_file}")
                except Exception:
                    pass

                report_path = os.path.join(WORKSPACE_ROOT, "Reporting.csv")
                os.makedirs(os.path.dirname(report_path), exist_ok=True)
                header = ["CARTID","ORDERNUMBER","LOCATIONCODE","MTN","TIMESTAMP"]
                now_iso = time.strftime('%Y-%m-%dT%H:%M:%S')
                def esc(v):
                    s = '' if v is None else str(v)
                    if any(ch in s for ch in ['\n','\r',',','"']):
                        return '"' + s.replace('"','""') + '"'
                    return s
                try:
                    write_header = not os.path.exists(report_path)
                    with open(report_path, "a", encoding="utf-8") as f:
                        if write_header:
                            f.write(",".join(header) + "\n")
                        out = [
                            esc(ids.get('cartid') or ''),
                            esc(ids.get('ordernumber') or ''),
                            esc(ids.get('locationcode') or ''),
                            esc(ids.get('mtn') or ''),
                            esc(now_iso)
                        ]
                        f.write(",".join(out) + "\n")
                    try:
                        print(f"[MCP Server] /reporting/append wrote 1 row to {report_path}")
                    except Exception:
                        pass
                    self._json(200, {"ok": True, "appended": 1, "path": report_path})
                except Exception as e:
                    self._json(500, {"error": str(e)})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        if parsed.path == "/jira/update":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8"))
                key = payload.get("key")
                components = payload.get("components")
                work_owner = payload.get("workOwnerVCG")
                # Accept both projectKey and projectKeyHint
                project_hint = payload.get("projectKey") or payload.get("projectKeyHint")
                print(f"[MCP Server] /jira/update payload: key={key!r}, components={components!r}, workOwnerVCG={work_owner!r}, projectKeyHint={project_hint!r}")
                if not key:
                    self._json(400, {"error": "Missing 'key'"})
                    return
                result = update_issue_fields(key, components, work_owner, project_key_hint=project_hint)
                status_out = result.get("status", 200 if result.get("ok") else 500)
                print(f"[MCP Server] /jira/update result: {result}")
                self._json(status_out, result)
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        if parsed.path == "/jira/attach-summary":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8"))
                key = payload.get("key")
                summary = payload.get("summary") or ""
                space = payload.get("space") or ""
                if not key:
                    self._json(400, {"error": "Missing 'key'"})
                    return
                # Attach summary as Jira comment
                comment_text = f"Confluence Summary{(' ['+space+']') if space else ''}:\n\n" + str(summary)
                res = add_issue_comment(key, comment_text[:8000])
                self._json(200, {"ok": True, "issue": key, "comment": res})
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
                self._json(e.code, {"error": err_text})
            except Exception as e:
                self._json(500, {"error": str(e)})
            return
        self._json(404, {"error": "Not Found"})


def main():
    httpd = HTTPServer((HOST, PORT), Handler)
    print(f"MCP Server running on http://{HOST}:{PORT}")
    print(f"Env summary: BASE_URL={'set' if JIRA_BASE_URL else 'missing'}, API_VER={JIRA_API_VERSION}, EMAIL={'set' if JIRA_EMAIL else 'missing'}, USERNAME={'set' if JIRA_USERNAME else 'missing'}, TOKEN={'set' if JIRA_API_TOKEN else 'missing'}, MOCK={'1' if JIRA_MOCK else '0'}")
    print(f"UI path: {UI_INDEX_PATH} | exists={os.path.exists(UI_INDEX_PATH)}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
