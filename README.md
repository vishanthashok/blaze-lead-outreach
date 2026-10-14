# blaze-lead-outreach

Builds a lead list of property-management companies in the Austin, TX area from public company websites, enriches each one with contact info and one "AI CFO" signal, and generates a personalized cold-email subject + opener per lead with an LLM. Built for the Blaze (YC S24) Growth Engineering Intern screen.

**It never contacts anyone.** Output is a CSV only.

## How it works
1. `data/seeds.csv` - company names + websites found via web search (source noted per row).
2. `scrape.py` - for each site: checks robots.txt, fetches the homepage plus up to 3 contact/about/owner pages (1s delay, identifying User-Agent), and extracts phone, public email, city, and a signal: PM software named on the site (AppFolio, Buildium, Rentvine, Rent Manager, DoorLoop...), a door/unit count ("950 homes"), or mentions of owner statements / late rent. Rows that do not confirm "Austin" + "property management" are dropped. Missing fields stay blank, nothing is guessed.
3. `run.py` - dedupes by domain and phone, adds `missing_contact`, calls the LLM, writes `output/austin_pm_leads.csv`.
4. `generate.py` + `prompts/outreach.md` - accepts `LLM_API_KEY` (provider detected from key prefix: sk-ant- Anthropic, xai- xAI, gsk_ Groq, sk- OpenAI; override with `LLM_PROVIDER`, model with `LLM_MODEL`) or auto-detects OPENAI / ANTHROPIC / XAI / GROQ key from `.env`. With no key, outreach columns stay blank and `llm_status` says so (no fake openers).

## Run
```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # add one API key
.venv/bin/python run.py
```
Takes about 2-3 minutes (polite crawl delays). To redo only the outreach columns on the existing CSV: `.venv/bin/python run.py --regen-only`.

Each opener is retried up to 3 times if it fails a rule check (2-3 sentences, no "most PMs we talk to" claims, no guessed accounting software, no em dashes).

## Columns
business_name, website, city, phone, email, missing_contact, signal, source_url, signal_source_url, seed_source, outreach_subject, outreach_opener, llm_status

## Sample output (first 3 rows)
| business_name | phone | email | signal | outreach_subject | outreach_opener |
|---|---|---|---|---|---|
| 1836 Property Management | (512) 994-4323 | info@1836pm.com | site says: '950 homes' | 950 homes and reconciliation | Your site mentions 950 homes under management. How do you currently handle reconciling transactions between your bank, books, and PM software each month? We built Blaze to automate that work, with your final approval on everything that moves. |
| Stone Oak Property Management | (512) 617-6766 | jason@stoneoakmgmt.com | uses AppFolio (found on site) | appfolio + accounting reconciliation | I noticed Stone Oak uses AppFolio. Do you spend time each month reconciling transactions between AppFolio, your books, and your bank account? Blaze connects all three and categorizes everything automatically, so nothing moves without your approval. |
| Prime Properties | (512) 342-9566 | thomas@primepropertiesaustin.com | uses AppFolio (found on site) | appfolio + bank reconciliation | Saw you use AppFolio for property management. Does reconciling transactions between AppFolio, your bank, and your books take up a lot of time each month? Blaze automates that matching and categorization, so nothing moves without your approval. |

Last run: 27 leads, all with phone or email. 25 got an LLM subject + opener (Anthropic, claude-haiku-4-5). 2 rows with no signal (Austin's Best PM, Crosstown Properties) are skipped on purpose and flagged in `llm_status`.

## Limits
- Some sites block bots (HTTP 202/401) and are dropped rather than bypassed.
- "Uses AppFolio" means the name appears on the site (usually a portal link), not a confirmed contract.
- A few national/flat-fee firms list non-Austin phone numbers.
