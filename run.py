"""One command: python run.py  -> output/austin_pm_leads.csv. Never sends anything."""
import csv, os
from urllib.parse import urlparse
from dotenv import load_dotenv
import scrape, generate

COLS = ["business_name", "website", "city", "phone", "email", "missing_contact", "signal", "source_url",
        "signal_source_url", "seed_source", "outreach_subject", "outreach_opener", "llm_status"]

def main():
    load_dotenv()
    import sys
    if "--regen-only" in sys.argv:  # reuse existing CSV, only redo LLM columns
        kept = list(csv.DictReader(open("output/austin_pm_leads.csv")))
        p = generate.generate(kept); write(kept, p); return
    rows = scrape.run()
    kept, seen = [], set()
    for r in rows:
        if r["crawl_note"]:
            print("drop", r["website"], "-", r["crawl_note"]); continue
        key = urlparse(r["website"]).netloc.replace("www.", "")
        if key in seen or (r["phone"] and r["phone"] in seen):
            print("dup", r["website"]); continue
        seen.add(key); r["phone"] and seen.add(r["phone"])
        r["missing_contact"] = "yes" if not (r["phone"] or r["email"]) else "no"
        kept.append(r)
    p = generate.generate(kept); write(kept, p)

def write(kept, p):
    os.makedirs("output", exist_ok=True)
    with open("output/austin_pm_leads.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore"); w.writeheader(); w.writerows(kept)
    print(f"\n{len(kept)} leads -> output/austin_pm_leads.csv")
    print("LLM:", f"{p[0]} / {p[3]}" if p else "NO API KEY FOUND - outreach columns left blank. Add a key to .env and rerun.")

if __name__ == "__main__":
    main()
