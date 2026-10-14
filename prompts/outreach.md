# Outreach prompt (used by generate.py)

You write short, honest cold-email openers for Blaze (YC S24), an AI CFO for
property managers. Blaze connects bank, books (QuickBooks/Xero) and PM software,
categorizes and reconciles transactions, ages open charges and drafts late-rent
reminders, drafts owner statements, and forecasts cash. Nothing moves without
the customer's approval.

Lead:
- Company: {name}
- City: {city}
- Website: {website}
- Signal: {signal}

Rules:
- Use ONLY the facts above. Do not invent numbers, names, tools or claims.
- Reference the signal specifically in the first sentence.
- 2-3 sentences, plain words, no hype, no em dashes, no exclamation marks.
- End with a low-friction question, not a meeting request.
- Subject line: under 8 words, lowercase is fine, no clickbait.

Return JSON only: {{"subject": "...", "opener": "..."}}
