
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json, re, shutil
from .schemas import GeneratedProject, GeneratedFile

SAFE_PATHS={"app/templates/index.html","app/static/app.css","app/static/app.js"}

def slugify(value:str)->str:
    value=re.sub(r"[^a-zA-Z0-9_-]+","-",value.strip()).strip("-").lower()
    return value or "app"

def finalize_project(project:GeneratedProject, prompt:str, root:Path):
    slug=slugify(project.plan.app_name)
    folder=root/slug
    if folder.exists(): shutil.rmtree(folder)
    (folder/"app"/"templates").mkdir(parents=True)
    (folder/"app"/"static").mkdir(parents=True)

    by_path={f.path:f.content for f in project.files if f.path in SAFE_PATHS}
    html=by_path.get("app/templates/index.html","<h1>App</h1>")
    css=by_path.get("app/static/app.css","")
    js=by_path.get("app/static/app.js","")

    (folder/"app"/"__init__.py").write_text("",encoding="utf-8")
    (folder/"app"/"templates"/"index.html").write_text(html,encoding="utf-8")
    (folder/"app"/"static"/"app.css").write_text(css,encoding="utf-8")
    (folder/"app"/"static"/"app.js").write_text(js,encoding="utf-8")
    manifest={
        "name":project.plan.app_name,
        "short_name":project.plan.app_name[:20],
        "start_url":"/",
        "display":"standalone",
        "background_color":"#f4f7fb",
        "theme_color":"#0f172a",
    }
    (folder/"app"/"static"/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
    (folder/"app"/"static"/"sw.js").write_text("self.addEventListener('fetch',()=>{});",encoding="utf-8")
    main_py=f"""from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app=FastAPI(title={project.plan.app_name!r})
app.mount("/static",StaticFiles(directory="app/static"),name="static")
templates=Jinja2Templates(directory="app/templates")

@app.get("/",response_class=HTMLResponse)
def index(request:Request):
    return templates.TemplateResponse("index.html",{{"request":request}})

@app.get("/health")
def health():
    return {{"status":"ok"}}
"""
    (folder/"app"/"main.py").write_text(main_py,encoding="utf-8")
    (folder/"requirements.txt").write_text("fastapi==0.115.0\nuvicorn[standard]==0.30.6\njinja2==3.1.4\n",encoding="utf-8")
    (folder/"Dockerfile").write_text(
        'FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nCMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]\n',
        encoding="utf-8"
    )
    (folder/"plan.json").write_text(project.plan.model_dump_json(indent=2),encoding="utf-8")
    (folder/"README.md").write_text("# "+project.plan.app_name+"\n\nPrompt:\n"+prompt+"\n",encoding="utf-8")

    zip_path=root/(slug+".zip")
    with ZipFile(zip_path,"w",ZIP_DEFLATED) as z:
        for p in folder.rglob("*"):
            if p.is_file(): z.write(p,p.relative_to(folder))
    return slug,folder,zip_path
