
from pathlib import Path
import json, os, uuid, time
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .ai_engine import discover, make_plan, make_project, refine_plan
from .project_io import finalize_project

app=FastAPI(title="AI App Studio V8")
app.mount("/static",StaticFiles(directory="app/static"),name="static")
templates=Jinja2Templates(directory="app/templates")
WORKSPACE=Path("workspace");WORKSPACE.mkdir(exist_ok=True)
SESSIONS={}

@app.get("/",response_class=HTMLResponse)
def home(request:Request):
    return templates.TemplateResponse("index.html",{"request":request,"has_ai":bool(os.getenv("AI_API_KEY","").strip())})

@app.post("/studio/start")
async def studio_start(app_name:str=Form(...), prompt:str=Form(...)):
    sid=uuid.uuid4().hex
    discovery=await discover(app_name,prompt)
    # Use recommended answers as sensible defaults for the first build.
    answers={}
    for q in discovery.questions:
        if q.recommended_answer:
            answers[q.id]=q.recommended_answer
    plan=await make_plan(app_name,prompt,answers,discovery.model_dump())
    project=await make_project(plan)
    slug,folder,zip_path=finalize_project(project,prompt,WORKSPACE)
    SESSIONS[sid]={
        "app_name":app_name,
        "slug":slug,
        "prompt":prompt,
        "discovery":discovery.model_dump(),
        "plan":plan.model_dump(),
        "messages":[
            {"role":"user","text":prompt},
            {"role":"assistant","text":"Eerste versie gebouwd. Zeg links wat je wilt veranderen; rechts zie je telkens de nieuwe versie."}
        ],
        "version":1,
    }
    return RedirectResponse(f"/studio/{sid}",status_code=303)

@app.get("/studio/{sid}",response_class=HTMLResponse)
def studio(request:Request,sid:str):
    s=SESSIONS.get(sid)
    if not s: raise HTTPException(404,"Studio-sessie niet gevonden")
    return templates.TemplateResponse("studio.html",{
        "request":request,
        "sid":sid,
        "app_name":s["app_name"],
        "slug":s["slug"],
        "messages":s["messages"],
        "version":s["version"],
        "ai_connected":bool(os.getenv("AI_API_KEY","").strip()),
    })

@app.post("/studio/{sid}/message")
async def studio_message(sid:str, instruction:str=Form(...)):
    s=SESSIONS.get(sid)
    if not s: raise HTTPException(404)
    instruction=instruction.strip()
    if not instruction:
        return RedirectResponse(f"/studio/{sid}",status_code=303)

    from .schemas import BuildPlan
    current=BuildPlan.model_validate(s["plan"])
    updated=await refine_plan(current,instruction)
    project=await make_project(updated)
    slug,folder,zip_path=finalize_project(project,s["prompt"]+"\n\nLatest requested change:\n"+instruction,WORKSPACE)

    s["plan"]=updated.model_dump()
    s["slug"]=slug
    s["messages"].append({"role":"user","text":instruction})
    s["messages"].append({"role":"assistant","text":"Aangepast. Bekijk de live versie rechts en geef gerust de volgende wijziging door."})
    s["version"]+=1
    return RedirectResponse(f"/studio/{sid}",status_code=303)

@app.post("/studio/{sid}/reset")
async def studio_reset(sid:str):
    s=SESSIONS.get(sid)
    if not s: raise HTTPException(404)
    discovery=await discover(s["app_name"],s["prompt"])
    answers={q.id:q.recommended_answer for q in discovery.questions if q.recommended_answer}
    plan=await make_plan(s["app_name"],s["prompt"],answers,discovery.model_dump())
    project=await make_project(plan)
    slug,folder,zip_path=finalize_project(project,s["prompt"],WORKSPACE)
    s["plan"]=plan.model_dump()
    s["slug"]=slug
    s["messages"].append({"role":"assistant","text":"Teruggezet naar een nieuwe basisversie op basis van je oorspronkelijke idee."})
    s["version"]+=1
    return RedirectResponse(f"/studio/{sid}",status_code=303)

@app.get("/apps/{slug}",response_class=HTMLResponse)
def preview(slug:str):
    p=WORKSPACE/slug/"app"/"templates"/"index.html"
    if not p.exists(): raise HTTPException(404)
    html=p.read_text(encoding="utf-8")
    html=html.replace('href="/static/app.css"',f'href="/apps/{slug}/static/app.css"')
    html=html.replace('src="/static/app.js"',f'src="/apps/{slug}/static/app.js"')
    html=html.replace('href="/static/manifest.json"',f'href="/apps/{slug}/static/manifest.json"')
    return HTMLResponse(html)

@app.get("/apps/{slug}/static/{filename}")
def asset(slug:str,filename:str):
    allowed={"app.css":"text/css","app.js":"application/javascript","manifest.json":"application/manifest+json","sw.js":"application/javascript"}
    if filename not in allowed: raise HTTPException(404)
    p=WORKSPACE/slug/"app"/"static"/filename
    if not p.exists(): raise HTTPException(404)
    return Response(p.read_text(encoding="utf-8"),media_type=allowed[filename])

@app.get("/download/{slug}")
def download(slug:str):
    p=WORKSPACE/(slug+".zip")
    if not p.exists(): raise HTTPException(404)
    return FileResponse(p,media_type="application/zip",filename=p.name)

@app.get("/health")
def health():
    return {"status":"ok","version":"8","ai_connected":bool(os.getenv("AI_API_KEY","").strip())}
