
from pathlib import Path
import json, os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .ai_engine import make_plan, make_project
from .project_io import finalize_project, slugify

app=FastAPI(title="AI App Studio V4")
app.mount("/static",StaticFiles(directory="app/static"),name="static")
templates=Jinja2Templates(directory="app/templates")
WORKSPACE=Path("workspace");WORKSPACE.mkdir(exist_ok=True)

@app.get("/",response_class=HTMLResponse)
def home(request:Request):
    has_ai=bool(os.getenv("AI_API_KEY","").strip())
    return templates.TemplateResponse("index.html",{"request":request,"has_ai":has_ai})

@app.post("/build",response_class=HTMLResponse)
async def build(request:Request, app_name:str=Form(...), prompt:str=Form(...)):
    plan=await make_plan(app_name,prompt)
    project=await make_project(plan,prompt)
    slug,folder,zip_path=finalize_project(project,prompt,WORKSPACE)
    return templates.TemplateResponse("done.html",{
        "request":request,"app_name":app_name,"slug":slug,
        "app_type":plan.app_type,"pages":len(plan.pages),"features":len(plan.features)
    })

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
def app_asset(slug:str,filename:str):
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
    return {"status":"ok","version":"4","ai_connected":bool(os.getenv("AI_API_KEY","").strip())}
