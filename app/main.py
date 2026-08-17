
from pathlib import Path
import json, os, uuid
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .ai_engine import discover, make_plan, make_project
from .project_io import finalize_project

app=FastAPI(title="AI App Studio V5")
app.mount("/static",StaticFiles(directory="app/static"),name="static")
templates=Jinja2Templates(directory="app/templates")
WORKSPACE=Path("workspace");WORKSPACE.mkdir(exist_ok=True)
SESSIONS={}

@app.get("/",response_class=HTMLResponse)
def home(request:Request):
    return templates.TemplateResponse("index.html",{"request":request,"has_ai":bool(os.getenv("AI_API_KEY","").strip())})

@app.post("/discover",response_class=HTMLResponse)
async def discovery(request:Request,app_name:str=Form(...),prompt:str=Form(...)):
    result=await discover(app_name,prompt)
    sid=uuid.uuid4().hex
    SESSIONS[sid]={"app_name":app_name,"prompt":prompt,"discovery":result.model_dump()}
    return templates.TemplateResponse("questions.html",{
        "request":request,"sid":sid,"app_name":app_name,"prompt":prompt,
        "summary":result.summary,"features":result.suggested_features,"questions":result.questions
    })

@app.post("/build",response_class=HTMLResponse)
async def build(request:Request,sid:str=Form(...)):
    if sid not in SESSIONS: raise HTTPException(400,"Sessie verlopen")
    sess=SESSIONS[sid]
    form=await request.form()
    answers={}
    for k,v in form.items():
        if k.startswith("q_"): answers[k[2:]]=str(v)
    plan,augmented=await make_plan(sess["app_name"],sess["prompt"],answers,sess["discovery"])
    project=await make_project(plan,augmented)
    slug,folder,zip_path=finalize_project(project,augmented,WORKSPACE)
    SESSIONS.pop(sid,None)
    return templates.TemplateResponse("done.html",{"request":request,"app_name":sess["app_name"],"slug":slug,"app_type":plan.app_type,"pages":len(plan.pages),"features":len(plan.features)})

@app.get("/apps/{slug}",response_class=HTMLResponse)
def preview(slug:str):
    p=WORKSPACE/slug/"app"/"templates"/"index.html"
    if not p.exists(): raise HTTPException(404)
    html=p.read_text(encoding="utf-8")
    html=html.replace('href="/static/app.css"',f'href="/apps/{slug}/static/app.css"').replace('src="/static/app.js"',f'src="/apps/{slug}/static/app.js"').replace('href="/static/manifest.json"',f'href="/apps/{slug}/static/manifest.json"')
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

@app.get("/plan/{slug}")
def plan(slug:str):
    p=WORKSPACE/slug/"plan.json"
    if not p.exists(): raise HTTPException(404)
    return json.loads(p.read_text(encoding="utf-8"))

@app.get("/health")
def health():
    return {"status":"ok","version":"5","ai_connected":bool(os.getenv("AI_API_KEY","").strip())}
