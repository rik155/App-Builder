
from pathlib import Path
import json
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .generator import build_app, export_zip, slugify

app=FastAPI(title="Smart App Builder V3")
app.mount("/static",StaticFiles(directory="app/static"),name="static")
templates=Jinja2Templates(directory="app/templates")
STORE=Path("generated");STORE.mkdir(exist_ok=True)

@app.get("/",response_class=HTMLResponse)
def index(request:Request):
    return templates.TemplateResponse("index.html",{"request":request})

@app.post("/build",response_class=HTMLResponse)
def build(request:Request,app_name:str=Form(...),prompt:str=Form(...),
          database:bool=Form(False),excel:bool=Form(False),photos:bool=Form(False),
          signature:bool=Form(False),barcode:bool=Form(False),pwa:bool=Form(False),
          email:bool=Form(False)):
    modules={"database":database,"excel":excel,"photos":photos,"signature":signature,"barcode":barcode,"pwa":pwa,"email":email}
    plan,files=build_app(app_name,prompt,modules)
    slug=slugify(app_name)
    folder=STORE/slug;folder.mkdir(exist_ok=True)
    for name,content in files.items():
        (folder/name).write_text(content,encoding="utf-8")
    (folder/"meta.json").write_text(json.dumps({"plan":plan,"prompt":prompt,"modules":modules}),encoding="utf-8")
    zpath=STORE/(slug+".zip")
    export_zip(app_name,prompt,modules,zpath)
    return templates.TemplateResponse("done.html",{"request":request,"slug":slug,"app_name":app_name,"kind":plan["kind"],"theme":plan["theme"]})

@app.get("/apps/{slug}",response_class=HTMLResponse)
def preview(slug:str):
    p=STORE/slug/"index.html"
    if not p.exists(): raise HTTPException(404)
    return HTMLResponse(p.read_text(encoding="utf-8"))

@app.get("/apps/{slug}/{filename}")
def asset(slug:str,filename:str):
    allowed={"app.css":"text/css","app.js":"application/javascript","manifest.json":"application/manifest+json","sw.js":"application/javascript"}
    if filename not in allowed: raise HTTPException(404)
    p=STORE/slug/filename
    if not p.exists(): raise HTTPException(404)
    return Response(p.read_text(encoding="utf-8"),media_type=allowed[filename])

@app.get("/download/{slug}")
def download(slug:str):
    p=STORE/(slug+".zip")
    if not p.exists(): raise HTTPException(404)
    return FileResponse(p,media_type="application/zip",filename=p.name)

@app.get("/health")
def health():
    return {"status":"ok","version":"3"}
