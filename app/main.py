
from pathlib import Path
import json
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .generator import build_preview, create_export_zip

app = FastAPI(title="Bedrijfsapp Builder V2")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
STORE = Path("generated_apps")
STORE.mkdir(exist_ok=True)

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/build", response_class=HTMLResponse)
def build(
    request: Request,
    app_name: str = Form(...),
    prompt: str = Form(...),
    database: bool = Form(False),
    excel: bool = Form(False),
    photos: bool = Form(False),
    signature: bool = Form(False),
    barcode: bool = Form(False),
    pwa: bool = Form(False),
    email: bool = Form(False),
):
    modules = {
        "database": database, "excel": excel, "photos": photos,
        "signature": signature, "barcode": barcode, "pwa": pwa, "email": email,
    }
    slug, files = build_preview(app_name, prompt, modules)
    folder = STORE / slug
    folder.mkdir(exist_ok=True)

    for filename, content in files.items():
        (folder / filename).write_text(content, encoding="utf-8")

    (folder / "meta.json").write_text(
        json.dumps({"app_name": app_name, "prompt": prompt, "modules": modules}),
        encoding="utf-8"
    )

    zip_path = STORE / f"{slug}.zip"
    create_export_zip(app_name, prompt, modules, zip_path)

    return templates.TemplateResponse(
        "done.html",
        {"request": request, "slug": slug, "app_name": app_name}
    )

@app.get("/apps/{slug}", response_class=HTMLResponse)
def preview(slug: str):
    path = STORE / slug / "preview.html"
    if not path.exists():
        raise HTTPException(404, "App niet gevonden")
    return HTMLResponse(path.read_text(encoding="utf-8"))

@app.get("/generated/{slug}/{filename}")
def generated_asset(slug: str, filename: str):
    allowed = {"app.css", "app.js", "manifest.json", "sw.js"}
    if filename not in allowed:
        raise HTTPException(404)
    path = STORE / slug / filename
    if not path.exists():
        raise HTTPException(404)
    media = {
        "app.css": "text/css",
        "app.js": "application/javascript",
        "manifest.json": "application/manifest+json",
        "sw.js": "application/javascript",
    }[filename]
    return Response(path.read_text(encoding="utf-8"), media_type=media)

@app.get("/download/{slug}")
def download(slug: str):
    path = STORE / f"{slug}.zip"
    if not path.exists():
        raise HTTPException(404)
    return FileResponse(path, media_type="application/zip", filename=path.name)

@app.get("/health")
def health():
    return {"status": "ok"}
