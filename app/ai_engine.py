
import json, os, httpx, re
from .schemas import BuildPlan, GeneratedProject, GeneratedFile, DiscoveryResult
from .fallback import fallback_plan, fallback_project, fallback_discovery

SYSTEM_DISCOVER = """You are the product-discovery architect inside an AI app builder.

Your job is NOT to classify the prompt into a template and ask generic questions.
Instead:
1. Infer the domain/industry from the prompt.
2. Infer who will use the app.
3. Infer the real-world workflow the app is trying to digitize.
4. Identify important domain objects/entities.
5. Identify likely integrations and operational constraints.
6. Suggest only features that naturally fit that workflow.
7. Ask 2-6 clarifying questions ONLY where the answer materially changes the UX, data model, or workflow.

Questions must be context-specific. Never ask quotation/offer questions unless the user is actually building an offer/quotation app.
Do not ask about features the user already clearly specified.
Avoid generic boilerplate like 'do you want a login?' unless authentication is genuinely relevant.
Prefer operational questions such as scheduling rules, handoff steps, approval flow, recurring jobs, scoring logic, medical history, route planning, etc.

Return JSON only:
{
 "summary":"brief interpretation",
 "detected_app_type":"specific app/domain type",
 "context":{
   "industry":"...",
   "target_users":["..."],
   "core_goal":"...",
   "core_workflow":["..."],
   "important_objects":["..."],
   "possible_integrations":["..."],
   "risks_or_constraints":["..."]
 },
 "suggested_features":[{"name":"...","description":"..."}],
 "questions":[
   {"id":"...","question":"...","why":"...","type":"text|choice|boolean","options":[],"required":true,"recommended_answer":"..."}
 ],
 "assumptions":[]
}"""

SYSTEM_PLAN = """You are a senior software product architect.
Use the user's original prompt, the inferred domain context, and all discovery answers to create a concrete build plan.
Do not fall back to a generic form unless a form is genuinely the product.
Design the app around the user's real workflow.
Return JSON only with:
app_name, app_type, visual_style, color_direction,
pages:[{name,route,purpose}],
features:[{name,description}],
data_entities:[string],
notes:[string]."""

SYSTEM_CODE = """You are the code-generation engine of an AI app builder.
Generate a polished, usable single-service FastAPI web app as files.
The generated UI and interaction model must be derived from the domain workflow and discovery answers.
Do not reuse a generic form layout for every app.
Examples:
- planning app => calendar/day cards/status workflow
- veterinary app => owners/pets/appointments/dossier
- game => real game loop and scoring
- inventory => scan/search/stock cards
- booking app => availability and reservation flow
Return JSON only:
{"files":[{"path":"app/templates/index.html","content":"..."},{"path":"app/static/app.css","content":"..."},{"path":"app/static/app.js","content":"..."}]}
Plain HTML/CSS/JS only; no external frameworks/CDNs. Make the primary interactions work in-browser. Mobile first but polished on desktop too."""

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
        r=await client.post(base+"/chat/completions",headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json={"model":model,"messages":messages,"temperature":0.3})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

async def discover(app_name,prompt):
    try:
        raw=_extract_json(await _chat([{"role":"system","content":SYSTEM_DISCOVER},{"role":"user","content":f"App name: {app_name}\nIdea:\n{prompt}"}]))
        return DiscoveryResult.model_validate(raw)
    except Exception:
        return fallback_discovery(app_name,prompt)

async def make_plan(app_name,prompt,answers,discovery):
    augmented=(
        prompt+
        "\n\nDISCOVERY CONTEXT:\n"+json.dumps(discovery,ensure_ascii=False,indent=2)+
        "\n\nUSER ANSWERS:\n"+json.dumps(answers,ensure_ascii=False,indent=2)
    )
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
