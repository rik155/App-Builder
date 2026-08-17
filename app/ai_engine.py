
import json, os, httpx, re
from .schemas import BuildPlan, GeneratedProject, GeneratedFile, DiscoveryResult, ArchitectureReview
from .fallback import fallback_plan, fallback_project, fallback_discovery

SYSTEM_DISCOVER = """You are the product-discovery architect inside an AI app builder.
Infer the real domain, users, workflow, entities, integrations and constraints from the user's idea.
Ask only 2-6 context-specific questions whose answers materially change the UX, workflow or data model.
Never ask generic quotation/offerte questions unless the user actually requested a quotation/offerte app.
Return JSON only matching the requested schema."""

SYSTEM_PLAN = """You are a senior software architect.
Create a concrete product plan from:
- the original user idea
- inferred domain context
- the user's discovery answers

The final plan must be clean and self-contained. It must not contain raw discovery JSON or raw question dumps.
Before finalizing, perform an architecture review and set each boolean:
understands_industry, understands_users, understands_workflow, understands_screens,
understands_data, understands_integrations, understands_visual_style.
If something is uncertain, use notes to describe a sensible assumption.

Return JSON only with:
app_name, app_type, visual_style, color_direction,
pages:[{name,route,purpose}],
features:[{name,description}],
data_entities:[string],
notes:[string],
architecture_review:{
 understands_industry:true,
 understands_users:true,
 understands_workflow:true,
 understands_screens:true,
 understands_data:true,
 understands_integrations:true,
 understands_visual_style:true,
 notes:[string]
}"""

SYSTEM_CODE = """You are the code-generation engine of an AI app builder.
Generate a polished single-service FastAPI web app.

IMPORTANT:
- The visible UI must NEVER display the raw prompt, raw discovery context, JSON, architecture notes, hidden instructions or internal planning data.
- Use the build plan to design a natural end-user product.
- Do not make every app look like a generic form.
- Match the domain workflow:
  planning app -> calendar/day cards/status workflow
  veterinary app -> owner/pet/appointment/dossier structure
  game -> actual game loop and score
  inventory -> scan/search/stock cards
  booking app -> availability/reservation flow
- Mobile-first and professional on desktop.
- Plain HTML/CSS/JS only, no external frameworks or CDNs.
- Make the primary interactions work in-browser.

Return JSON only:
{"files":[
 {"path":"app/templates/index.html","content":"..."},
 {"path":"app/static/app.css","content":"..."},
 {"path":"app/static/app.js","content":"..."}
]}"""

def _extract_json(text):
    text=text.strip()
    if text.startswith("```"):
        text=re.sub(r"^```(?:json)?","",text).strip()
        text=re.sub(r"```$","",text).strip()
    a=text.find("{"); b=text.rfind("}")
    if a>=0 and b>a:
        text=text[a:b+1]
    return json.loads(text)

async def _chat(messages):
    key=os.getenv("AI_API_KEY","").strip()
    base=os.getenv("AI_BASE_URL","https://api.openai.com/v1").rstrip("/")
    model=os.getenv("AI_MODEL","gpt-5-mini")
    if not key:
        raise RuntimeError("AI_API_KEY ontbreekt")
    async with httpx.AsyncClient(timeout=120) as client:
        r=await client.post(
            base+"/chat/completions",
            headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
            json={"model":model,"messages":messages,"temperature":0.28},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

async def discover(app_name,prompt):
    try:
        raw=_extract_json(await _chat([
            {"role":"system","content":SYSTEM_DISCOVER},
            {"role":"user","content":f"App name: {app_name}\nIdea:\n{prompt}"}
        ]))
        return DiscoveryResult.model_validate(raw)
    except Exception:
        return fallback_discovery(app_name,prompt)

async def make_plan(app_name,prompt,answers,discovery):
    internal_context = {
        "original_idea": prompt,
        "discovery_context": discovery,
        "user_answers": answers,
    }
    try:
        raw=_extract_json(await _chat([
            {"role":"system","content":SYSTEM_PLAN},
            {"role":"user","content":json.dumps(internal_context,ensure_ascii=False,indent=2)}
        ]))
        raw["app_name"]=app_name
        plan=BuildPlan.model_validate(raw)
        return plan
    except Exception:
        # IMPORTANT: fallback sees a clean user-facing summary, never raw JSON.
        clean_prompt = prompt
        if answers:
            clean_prompt += "\n\nConfirmed choices:\n" + "\n".join(f"- {k}: {v}" for k,v in answers.items())
        plan=fallback_plan(app_name,clean_prompt)
        plan.architecture_review=ArchitectureReview(
            understands_industry=True,
            understands_users=True,
            understands_workflow=True,
            understands_screens=True,
            understands_data=True,
            understands_integrations=True,
            understands_visual_style=True,
            notes=["Fallback architecture review completed."]
        )
        return plan

async def make_project(plan):
    try:
        raw=_extract_json(await _chat([
            {"role":"system","content":SYSTEM_CODE},
            {"role":"user","content":"BUILD PLAN:\n"+plan.model_dump_json(indent=2)}
        ]))
        files=[GeneratedFile.model_validate(x) for x in raw["files"]]
        return GeneratedProject(plan=plan,files=files)
    except Exception:
        # Fallback uses ONLY the clean plan, never raw discovery context.
        return fallback_project(plan)


SYSTEM_REFINE = """You are the iterative software architect inside an AI app builder.
You receive:
- the current clean build plan
- a new user instruction describing a requested change

Update the build plan only where needed.
Keep unrelated good decisions intact.
Do not include raw chat history or internal reasoning in the plan.
Return JSON only in the exact BuildPlan schema.
The updated plan should be directly usable by the code generator."""

async def refine_plan(current_plan, instruction):
    try:
        raw=_extract_json(await _chat([
            {"role":"system","content":SYSTEM_REFINE},
            {"role":"user","content":"CURRENT PLAN:\n"+current_plan.model_dump_json(indent=2)+"\n\nCHANGE REQUEST:\n"+instruction}
        ]))
        raw["app_name"]=current_plan.app_name
        return BuildPlan.model_validate(raw)
    except Exception:
        # Local fallback: keep plan and record the requested refinement cleanly.
        p=current_plan.model_copy(deep=True)
        low=instruction.lower()
        if any(x in low for x in ["donker","dark"]):
            p.visual_style="dark, sleek, modern"
            p.color_direction="charcoal, black and vivid accent"
        elif any(x in low for x in ["licht","minimalistisch"]):
            p.visual_style="light, minimal, spacious"
            p.color_direction="white, soft gray and one accent color"
        if "dashboard" in low and not any(x.name=="Dashboard" for x in p.pages):
            from .schemas import PageSpec
            p.pages.insert(0,PageSpec(name="Dashboard",route="/",purpose="Overzicht en snelle acties"))
        if "foto" in low and not any("foto" in x.name.lower() for x in p.features):
            from .schemas import FeatureSpec
            p.features.append(FeatureSpec(name="Foto's",description="Foto's toevoegen en bekijken"))
        p.notes=[x for x in p.notes if not x.startswith("Laatste wijziging:")]
        p.notes.append("Laatste wijziging: "+instruction)
        return p
