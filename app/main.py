
from pathlib import Path
import uuid,time,re,shutil
from zipfile import ZipFile,ZIP_DEFLATED
from fastapi import FastAPI,Request,Form,HTTPException
from fastapi.responses import HTMLResponse,FileResponse,Response,RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .product_engine import make_brief,make_app,qa,status
from .schemas import ProductBrief,ModuleSpec

app=FastAPI(title="AI App Studio V13")
app.mount("/static",StaticFiles(directory="app/static"),name="static")
templates=Jinja2Templates(directory="app/templates")
WORKSPACE=Path("workspace");WORKSPACE.mkdir(exist_ok=True)
SESSIONS={}

def slug(v): return re.sub(r"[^a-zA-Z0-9_-]+","-",v.strip()).strip("-").lower() or "app"

def save_project(brief,files,q):
    s=slug(brief.app_name);folder=WORKSPACE/s
    if folder.exists(): shutil.rmtree(folder)
    (folder/"app"/"templates").mkdir(parents=True);(folder/"app"/"static").mkdir(parents=True)
    by={f.path:f.content for f in files}
    (folder/"app"/"__init__.py").write_text("",encoding="utf-8")
    (folder/"app"/"templates"/"index.html").write_text(by["app/templates/index.html"],encoding="utf-8")
    (folder/"app"/"static"/"app.css").write_text(by["app/static/app.css"],encoding="utf-8")
    (folder/"app"/"static"/"app.js").write_text(by["app/static/app.js"],encoding="utf-8")
    app_main="from fastapi import FastAPI, Request\\nfrom fastapi.responses import HTMLResponse\\nfrom fastapi.templating import Jinja2Templates\\nfrom fastapi.staticfiles import StaticFiles\\napp=FastAPI()\\napp.mount('/static',StaticFiles(directory='app/static'),name='static')\\ntemplates=Jinja2Templates(directory='app/templates')\\n@app.get('/',response_class=HTMLResponse)\\ndef home(request:Request): return templates.TemplateResponse('index.html',{'request':request})\\n"
    (folder/"app"/"main.py").write_text(app_main,encoding="utf-8")
    (folder/"requirements.txt").write_text("fastapi==0.115.0\\nuvicorn[standard]==0.30.6\\njinja2==3.1.4\\n",encoding="utf-8")
    (folder/"product_brief.json").write_text(brief.model_dump_json(indent=2),encoding="utf-8")
    zpath=WORKSPACE/(s+".zip")
    with ZipFile(zpath,"w",ZIP_DEFLATED) as z:
        for p in folder.rglob("*"):
            if p.is_file(): z.write(p,p.relative_to(folder))
    return s

@app.get("/",response_class=HTMLResponse)
async def home(request:Request):
    return templates.TemplateResponse("index.html",{"request":request,"ollama":await status()})

@app.post("/analyze",response_class=HTMLResponse)
async def analyze(request:Request,app_name:str=Form(...),prompt:str=Form(...),mode:str=Form("turbo")):
    t0=time.perf_counter();brief,_=await make_brief(app_name,prompt,mode);sid=uuid.uuid4().hex
    SESSIONS[sid]={"app_name":app_name,"prompt":prompt,"mode":mode,"brief":brief.model_dump()}
    return templates.TemplateResponse("review.html",{"request":request,"sid":sid,"brief":brief,"elapsed":round(time.perf_counter()-t0,1)})

@app.post("/build/{sid}")
async def build(sid:str,request:Request):
    s=SESSIONS.get(sid)
    if not s: raise HTTPException(404)
    form=await request.form();brief=ProductBrief.model_validate(s["brief"]);enabled=set(form.getlist("module"))
    for m in brief.modules: m.enabled=m.name in enabled
    custom=str(form.get("custom_module","")).strip()
    if custom: brief.modules.append(ModuleSpec(name=custom,description="Door gebruiker toegevoegd",priority="should",enabled=True))
    t0=time.perf_counter();files=make_app(brief);q=qa(brief,files);slugv=save_project(brief,files,q)
    s.update({"brief":brief.model_dump(),"slug":slugv,"qa":q.model_dump(),"elapsed":round(time.perf_counter()-t0,1),"version":1})
    return RedirectResponse(f"/studio/{sid}",status_code=303)

@app.get("/studio/{sid}",response_class=HTMLResponse)
async def studio(request:Request,sid:str):
    s=SESSIONS.get(sid)
    if not s or "slug" not in s: raise HTTPException(404)
    return templates.TemplateResponse("studio.html",{"request":request,"sid":sid,"app_name":s["app_name"],"slug":s["slug"],"qa":s["qa"],"elapsed":s["elapsed"],"version":s["version"]})

@app.post("/studio/{sid}/module")
async def module(sid:str,module:str=Form(...)):
    s=SESSIONS.get(sid)
    if not s: raise HTTPException(404)
    brief=ProductBrief.model_validate(s["brief"]);module=module.strip()
    if module and not any(m.name.lower()==module.lower() for m in brief.modules):
        brief.modules.append(ModuleSpec(name=module,description="Toegevoegd vanuit studio",priority="should",enabled=True))
    files=make_app(brief);q=qa(brief,files);slugv=save_project(brief,files,q)
    s.update({"brief":brief.model_dump(),"slug":slugv,"qa":q.model_dump(),"elapsed":0.1,"version":s["version"]+1})
    return RedirectResponse(f"/studio/{sid}",status_code=303)

@app.get("/apps/{slug}",response_class=HTMLResponse)
def preview(slug:str):
    p=WORKSPACE/slug/"app"/"templates"/"index.html"
    html=p.read_text(encoding="utf-8").replace('href="/static/app.css"',f'href="/apps/{slug}/static/app.css"').replace('src="/static/app.js"',f'src="/apps/{slug}/static/app.js"')
    return HTMLResponse(html)

@app.get("/apps/{slug}/static/{filename}")
def asset(slug:str,filename:str):
    types={"app.css":"text/css","app.js":"application/javascript"};p=WORKSPACE/slug/"app"/"static"/filename
    if filename not in types or not p.exists(): raise HTTPException(404)
    return Response(p.read_text(encoding="utf-8"),media_type=types[filename])

@app.get("/download/{slug}")
def download(slug:str):
    p=WORKSPACE/(slug+".zip");return FileResponse(p,media_type="application/zip",filename=p.name)
