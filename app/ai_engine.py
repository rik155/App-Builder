
import json, os, httpx, re
from .schemas import BuildPlan, GeneratedProject, GeneratedFile
from .fallback import fallback_plan, fallback_project

SYSTEM_PLAN = """You are the planning engine for an AI app builder.
Turn the user's app idea into a concrete product plan.
Do not force a form template. The app may be a business tool, website, dashboard, calculator, game, planner, CRM, booking tool, quote generator, etc.
Return JSON only with:
app_name, app_type, visual_style, color_direction,
pages:[{name,route,purpose}],
features:[{name,description}],
data_entities:[string],
notes:[string].
Be specific and infer sensible standard features when clearly implied by the app type."""

SYSTEM_CODE = """You are the code generation engine for an AI app builder.
Generate a polished, usable single-service FastAPI web app as files.
The UI must look professionally designed, responsive on iPhone and desktop, and must be materially tailored to the user's prompt and plan.
Do not return explanations. Return JSON only:
{"files":[{"path":"app/templates/index.html","content":"..."},{"path":"app/static/app.css","content":"..."},{"path":"app/static/app.js","content":"..."}]}
Requirements:
- Use plain HTML/CSS/JS frontend with FastAPI serving it.
- Do not use external JS frameworks or CDNs.
- Make interactions work in-browser.
- Avoid generic browser-default styling.
- Never display secrets.
- Keep generated files self-contained.
"""

def _extract_json(text: str):
    text=text.strip()
    if text.startswith("```"):
        text=re.sub(r"^```(?:json)?","",text).strip()
        text=re.sub(r"```$","",text).strip()
    a=text.find("{"); b=text.rfind("}")
    if a>=0 and b>a: text=text[a:b+1]
    return json.loads(text)

async def _chat(messages):
    key=os.getenv("AI_API_KEY","").strip()
    base=os.getenv("AI_BASE_URL","https://api.openai.com/v1").rstrip("/")
    model=os.getenv("AI_MODEL","gpt-5-mini")
    if not key:
        raise RuntimeError("AI_API_KEY ontbreekt")
    async with httpx.AsyncClient(timeout=90) as client:
        r=await client.post(
            base+"/chat/completions",
            headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
            json={"model":model,"messages":messages,"temperature":0.35},
        )
        r.raise_for_status()
        data=r.json()
        return data["choices"][0]["message"]["content"]

async def make_plan(app_name: str, prompt: str) -> BuildPlan:
    try:
        text=await _chat([
            {"role":"system","content":SYSTEM_PLAN},
            {"role":"user","content":f"App name: {app_name}\nUser prompt:\n{prompt}"}
        ])
        raw=_extract_json(text)
        raw["app_name"]=app_name
        return BuildPlan.model_validate(raw)
    except Exception:
        return fallback_plan(app_name,prompt)

async def make_project(plan: BuildPlan, prompt: str) -> GeneratedProject:
    try:
        text=await _chat([
            {"role":"system","content":SYSTEM_CODE},
            {"role":"user","content":"USER PROMPT:\n"+prompt+"\n\nPLAN:\n"+plan.model_dump_json(indent=2)}
        ])
        raw=_extract_json(text)
        files=[GeneratedFile.model_validate(x) for x in raw["files"]]
        return GeneratedProject(plan=plan,files=files)
    except Exception:
        return fallback_project(plan,prompt)
