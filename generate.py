"""LLM outreach generation. Auto-detects a provider from env; never fakes output."""
import json, os, re, requests
PROVIDERS = [  # env var, kind, url, default model
    ("OPENAI_API_KEY", "openai", "https://api.openai.com/v1/chat/completions", "gpt-4o-mini"),
    ("ANTHROPIC_API_KEY", "anthropic", "https://api.anthropic.com/v1/messages", "claude-haiku-4-5"),
    ("XAI_API_KEY", "openai", "https://api.x.ai/v1/chat/completions", "grok-3-mini"),
    ("GROQ_API_KEY", "openai", "https://api.groq.com/openai/v1/chat/completions", "llama-3.1-8b-instant"),
]

GENERIC = {"anthropic": PROVIDERS[1], "openai": PROVIDERS[0], "xai": PROVIDERS[2], "groq": PROVIDERS[3]}

def detect(key):
    if key.startswith("sk-ant-"): return "anthropic"
    if key.startswith("xai-"): return "xai"
    if key.startswith("gsk_"): return "groq"
    if key.startswith("sk-"): return "openai"
    return None

def provider():
    key = os.getenv("LLM_API_KEY")
    if key:
        name = (os.getenv("LLM_PROVIDER") or detect(key) or "").lower()
        if name not in GENERIC:
            raise SystemExit("LLM_API_KEY set but provider unknown; set LLM_PROVIDER=openai|anthropic|xai|groq")
        _, kind, url, model = GENERIC[name]
        return "LLM_API_KEY", kind, url, os.getenv("LLM_MODEL") or model, name
    for env, kind, url, model in PROVIDERS:
        if os.getenv(env):
            return env, kind, url, os.getenv("LLM_MODEL") or model, env.split("_")[0].lower()
    return None

def call(p, prompt):
    env, kind, url, model, _ = p; key = os.environ[env]
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
            row["llm_status"] = "skipped: no signal found (no opener without a real hook)"; continue
        o, err = None, ""
        for _ in range(3):  # retry on bad JSON or rule violations
            try:
                o = call(p, tmpl.format(**{k: row.get(k, "") for k in ("city", "website", "signal")}, name=row["business_name"]))
                n = len(re.findall(r"[.?!](\s|$)", o["opener"].strip()))
                bad = re.search(r"we talk to|we work with|\u2014|15 minutes|quickbooks|xero", o["opener"] + " " + o["subject"], re.I)
                if 2 <= n <= 3 and not bad: break
                err, o = f"rule check failed ({n} sentences)", None
            except Exception as e:
                err, o = f"error: {type(e).__name__}", None
        if o:
            row["outreach_subject"], row["outreach_opener"] = o["subject"].strip(), o["opener"].strip()
            row["llm_status"] = f"ok: {p[4]}/{p[3]}"
        else:
            row["llm_status"] = err
    return p
