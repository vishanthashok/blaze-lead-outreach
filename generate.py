"""LLM outreach generation. Auto-detects a provider from env; never fakes output."""
import json, os, re, requests
PROVIDERS = [  # env var, kind, url, default model
    ("OPENAI_API_KEY", "openai", "https://api.openai.com/v1/chat/completions", "gpt-4o-mini"),
    ("ANTHROPIC_API_KEY", "anthropic", "https://api.anthropic.com/v1/messages", "claude-3-5-haiku-latest"),
    ("XAI_API_KEY", "openai", "https://api.x.ai/v1/chat/completions", "grok-3-mini"),
    ("GROQ_API_KEY", "openai", "https://api.groq.com/openai/v1/chat/completions", "llama-3.1-8b-instant"),
]

def provider():
    for env, kind, url, model in PROVIDERS:
        if os.getenv(env):
            return env, kind, url, os.getenv("LLM_MODEL") or model
    return None

def call(p, prompt):
    env, kind, url, model = p; key = os.environ[env]
    if kind == "anthropic":
        r = requests.post(url, timeout=60, headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                          json={"model": model, "max_tokens": 300, "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status(); out = r.json()["content"][0]["text"]
    else:
        r = requests.post(url, timeout=60, headers={"Authorization": f"Bearer {key}"},
                          json={"model": model, "temperature": 0.4, "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status(); out = r.json()["choices"][0]["message"]["content"]
    return json.loads(re.search(r"\{.*\}", out, re.S).group(0))

def generate(rows, template_path="prompts/outreach.md"):
    tmpl = open(template_path).read()
    p = provider()
    for row in rows:
        row["outreach_subject"] = row["outreach_opener"] = ""
        if not p:
            row["llm_status"] = "skipped: no LLM API key in .env"; continue
        if not row["signal"]:
            row["llm_status"] = "skipped: no signal found"; continue
        try:
            o = call(p, tmpl.format(**{k: row.get(k, "") for k in ("city", "website", "signal")}, name=row["business_name"]))
            row["outreach_subject"], row["outreach_opener"] = o["subject"].strip(), o["opener"].strip()
            row["llm_status"] = f"ok: {p[0].split('_')[0].lower()}/{p[3]}"
        except Exception as e:
            row["llm_status"] = f"error: {type(e).__name__}"
    return p
