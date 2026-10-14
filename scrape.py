"""Collect + enrich Austin property-management leads from public company websites.
Respects robots.txt, identifies itself, rate-limits, never fabricates: missing fields stay blank."""
import csv, re, time, urllib.robotparser
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

UA = "blaze-lead-outreach/0.1 (student take-home; public data only)"
S = requests.Session(); S.headers["User-Agent"] = UA
PHONE = re.compile(r"\(?\b(\d{3})\)?[\s.\-]?(\d{3})[\s.\-](\d{4})\b")
EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
SOFTWARE = ["AppFolio", "Buildium", "Rentvine", "Propertyware", "Rent Manager", "Yardi", "RentRedi", "TenantCloud", "DoorLoop"]
DOORS = re.compile(r"\b(\d{1,3}(?:,\d{3})*|\d+)\+?\s+(doors|units|homes|properties|rentals|rental homes)\b(?:\s+(?:under management|managed))?", re.I)
PAGE_HINTS = ("contact", "about", "owner", "career", "join", "technology")
BAD_EMAIL = ("example.", "sentry", "wixpress", ".png", ".jpg", "domain.com", "flywheelsites")

_robots = {}
def allowed(url):
    p = urlparse(url); base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            r = S.get(base + "/robots.txt", timeout=10)
            rp.parse(r.text.splitlines() if r.status_code == 200 else [])
        except Exception:
            rp.parse([])
        _robots[base] = rp
    return _robots[base].can_fetch(UA, url)

def fetch(url):
    if not allowed(url):
        return None, "blocked by robots.txt"
    try:
        r = S.get(url, timeout=15); time.sleep(1)
        if r.status_code != 200 or "html" not in r.headers.get("content-type", ""):
            return None, f"http {r.status_code}"
        return r, None
    except Exception as e:
        return None, type(e).__name__

def find_signal(text, html_lower):
    for sw in SOFTWARE:
        if sw.lower().replace(" ", "") in html_lower.replace(" ", ""):
            return f"uses {sw} (found on site)"
    m = DOORS.search(text)
    if m and int(m.group(1).replace(",", "")) >= 20:
        return f"site says: '{m.group(0).strip()}'"
    for kw, label in [("owner statement", "mentions owner statements"), ("late rent", "mentions late rent"),
                      ("bookkeeper", "mentions bookkeeper role"), ("we're hiring", "hiring"), ("trust account", "mentions trust accounting")]:
        if kw in text.lower():
            return label
    return ""

def enrich(seed):
    row = {"business_name": seed["name"], "website": seed["website"], "city": "", "phone": "", "email": "",
           "signal": "", "source_url": seed["website"], "signal_source_url": "", "seed_source": seed["seed_source"], "crawl_note": ""}
    r, err = fetch(seed["website"])
    if not r:
        row["crawl_note"] = err; return row
    pages = [(r.url, r.text)]
    soup = BeautifulSoup(r.text, "html.parser")
    host = urlparse(r.url).netloc
    links = []
    for a in soup.find_all("a", href=True):
        u = urljoin(r.url, a["href"]).split("#")[0]
        if urlparse(u).netloc == host and any(h in u.lower() for h in PAGE_HINTS) and u not in links:
            links.append(u)
    for u in links[:3]:
        rr, _ = fetch(u)
        if rr: pages.append((rr.url, rr.text))
    for url, html in pages:
        s = BeautifulSoup(html, "html.parser")
        mail = [a["href"][7:].split("?")[0] for a in s.select('a[href^="mailto:"]')]
        for tag in s(["script", "style", "noscript"]): tag.decompose()
        text = s.get_text(" ", strip=True)
        if not row["phone"]:
            tel = [a["href"][4:] for a in s.select('a[href^="tel:"]')]
            m = PHONE.search(" ".join(tel) + " " + text)
            if m: row["phone"] = f"({m.group(1)}) {m.group(2)}-{m.group(3)}"
        if not row["email"]:
            cands = [e for e in EMAIL.findall(" ".join(mail)) + EMAIL.findall(text) if not any(b in e.lower() for b in BAD_EMAIL)]
            if cands: row["email"] = cands[0].lower()
        if not row["city"]:
            m = re.search(r"\b(Austin|Round Rock|Cedar Park|Pflugerville|Georgetown|Dripping Springs|Leander|Kyle|Buda),?\s*(TX|Texas)\b", text)
            if m: row["city"] = m.group(1)
        if not row["signal"]:
            sig = find_signal(text, html.lower())
            if sig: row["signal"], row["signal_source_url"] = sig, url
        row["_austin"] = row.get("_austin") or ("austin" in text.lower())
        row["_pm"] = row.get("_pm") or ("property management" in text.lower() or "property manager" in text.lower())
    if not (row.pop("_austin", False) and row.pop("_pm", False)):
        row["crawl_note"] = "not confirmed as Austin property manager"
    return row

def run(seeds_path="data/seeds.csv"):
    seeds = list(csv.DictReader(open(seeds_path)))
    rows = []
    for sd in seeds:
        print("crawl", sd["website"], flush=True)
        rows.append(enrich(sd))
    return rows
