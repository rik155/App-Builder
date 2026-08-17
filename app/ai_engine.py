
import json, os, httpx, re
from .schemas import BuildPlan, GeneratedProject, GeneratedFile, DiscoveryResult
from .fallback import fallback_plan, fallback_project, fallback_discovery

SYSTEM_DISCOVER = """You are the product discovery agent inside an AI app builder.
Before building, understand the user's idea and ask only high-value questions.
Suggest features that naturally fit the requested app.
Do NOT overwhelm the user. Ask 2-6 questions maximum.
If a feature is strongly implied, suggest it.
Return JSON only:
{
 "summary":"...",
 "detected_app_type":"...",
 "suggested_features":[{"name":"...","description":"..."}],
 "questions":[
   {"id":"...","question":"...","why":"...","type":"text|choice|boolean","options":[],"required":true,"recommended_answer":"..."}
 ],
 "assumptions":[]
}
Questions should be specific to the app type, not generic boilerplate."""

SYSTEM_PLAN = """You are the planning engine for an AI app builder.
Turn the user's original prompt PLUS discovery answers into a concrete product plan.
Respect the user's answers exactly.
Return JSON only with:
app_name, app_type, visual_style, color_direction,
pages:[{name,route,purpose}],
features:[{name,description}],
data_entities:[string],
notes:[string].
Do not force a form template. Apps may be games, websites, dashboards, tools, CRMs, booking systems, calculators, etc."""

SYSTEM_CODE = """You are the code generation engine for an AI app builder.
Generate a polished, usable single-service FastAPI web app as files.
The UI must be professionally styled, responsive on iPhone and desktop, and materially tailored to the user's prompt, discovery answers and plan.
Return JSON only:
{"files":[{"path":"app/templates/index.html","content":"..."},{"path":"app/static/app.css","content":"..."},{"path":"app/static/app.js","content":"..."}]}
Use plain HTML/CSS/JS. No external frameworks/CDNs. Make the main interactions work in-browser. Never display secrets."""

def _extract_json(text):
    text=text.strip()
    if text.startswith("```"):
        text=re.sub(r"^```(?:json)?","",text).strip()
        text=re.sub(r"```$","",text).strip()
    a=text.find("{");b=text.rfind("}")
    if a>=0 and b>a:text=text[a:b+1]
    return json.loads(text)

async def _chat(messages):
    key=os.getenv("AI_API_KEY","").strip()
    base=os.getenv("AI_BASE_URL","https://api.openai.com/v1").rstrip("/")
    model=os.getenv("AI_MODEL","gpt-5-mini")
    if not key: raise RuntimeError("AI_API_KEY ontbreekt")
    async with httpx.AsyncClient(timeout=90) as client:
        r=await client.post(base+"/chat/completions",headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json={"model":model,"messages":messages,"temperature":0.35})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

async def discover(app_name,prompt):
    try:
        raw=_extract_json(await _chat([{"role":"system","content":SYSTEM_DISCOVER},{"role":"user","content":f"App name: {app_name}\nIdea:\n{prompt}"}]))
        return DiscoveryResult.model_validate(raw)
    except Exception:
        return fallback_discovery(app_name,prompt)

async def make_plan(app_name,prompt,answers):
    augmented=prompt+"\n\nDISCOVERY ANSWERS:\n"+json.dumps(answers,ensure_ascii=False,indent=2)
    try:
        raw=_extract_json(await _chat([{"role":"system","content":SYSTEM_PLAN},{"role":"user","content":f"App name: {app_name}\nRequest:\n{augmented}"}]))
        raw["app_name"]=app_name
        return BuildPlan.model_validate(raw),augmented
    except Exception:
        return fallback_plan(app_name,augmented),augmented

async def make_project(plan,prompt):
    try:
        raw=_extract_json(await _chat([{"role":"system","content":SYSTEM_CODE},{"role":"user","content":"REQUEST:\n"+prompt+"\n\nPLAN:\n"+plan.model_dump_json(indent=2)}]))
        files=[GeneratedFile.model_validate(x) for x in raw["files"]]
        return GeneratedProject(plan=plan,files=files)
    except Exception:
        return fallback_project(plan,prompt)
