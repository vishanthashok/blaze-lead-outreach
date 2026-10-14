# blaze-lead-outreach

Builds a lead list of property-management companies in the Austin, TX area from public company websites, enriches each one with contact info and one "AI CFO" signal, and generates a personalized cold-email subject + opener per lead with an LLM. Built for the Blaze (YC S24) Growth Engineering Intern screen.

**It never contacts anyone.** Output is a CSV only.

## How it works
1. `data/seeds.csv` - company names + websites found via web search (source noted per row).
2. `scrape.py` - for each site: checks robots.txt, fetches the homepage plus up to 3 contact/about/owner pages (1s delay, identifying User-Agent), and extracts phone, public email, city, and a signal: PM software named on the site (AppFolio, Buildium, Rentvine, Rent Manager, DoorLoop...), a door/unit count ("950 homes"), or mentions of owner statements / late rent. Rows that do not confirm "Austin" + "property management" are dropped. Missing fields stay blank, nothing is guessed.
3. `run.py` - dedupes by domain and phone, adds `missing_contact`, calls the LLM, writes `output/austin_pm_leads.csv`.
4. `generate.py` + `prompts/outreach.md` - auto-detects OPENAI / ANTHROPIC / XAI / GROQ key from `.env`. With no key, outreach columns stay blank and `llm_status` says so (no fake openers).

## Run
```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # add one API key
.venv/bin/python run.py
```
Takes about 2-3 minutes (polite crawl delays).

## Columns
business_name, website, city, phone, email, missing_contact, signal, source_url, signal_source_url, seed_source, outreach_subject, outreach_opener, llm_status

## Sample output (first 3 rows)
| business_name | city | phone | email | missing_contact | signal | source_url |
|---|---|---|---|---|---|---|
| 1836 Property Management | Austin | (512) 994-4323 | info@1836pm.com | no | site says: '950 homes' | https://1836propertymanagement.com/ |
| Stone Oak Property Management | Austin | (512) 617-6766 | jason@stoneoakmgmt.com | no | uses AppFolio (found on site) | https://www.stoneoakmgmt.com/ |
| Prime Properties | Austin | (512) 342-9566 | thomas@primepropertiesaustin.com | no | uses AppFolio (found on site) | https://www.austinpropertymanagement.com/ |

Last run: 27 leads, all with phone or email. Outreach columns are blank in the committed CSV because no LLM key was set on that run.

## Limits
- Some sites block bots (HTTP 202/401) and are dropped rather than bypassed.
- "Uses AppFolio" means the name appears on the site (usually a portal link), not a confirmed contract.
- A few national/flat-fee firms list non-Austin phone numbers.
