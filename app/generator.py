
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json
import re

def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()
    return value or "nieuwe-app"

def fields_for(prompt: str):
    p = prompt.lower()
    if any(w in p for w in ["voorraad", "magazijn", "barcode"]):
        return [
            ("Productnaam", "text"), ("Barcode", "text"), ("Voorraad", "number"),
            ("Minimumvoorraad", "number"), ("Eenheid", "text")
        ]
    if "weekrapport" in p or "week rapport" in p:
        return [
            ("Opdrachtgever", "text"), ("Object / project", "text"),
            ("Weeknummer", "number"), ("Voorman", "text"), ("Opmerking", "textarea")
        ]
    if "meerwerk" in p:
        return [
            ("Opdrachtgever", "text"), ("Werkadres", "text"),
            ("Omschrijving meerwerk", "textarea"), ("Extra uren", "number"),
            ("Materialen", "textarea")
        ]
    return [
        ("Klantnaam", "text"), ("Werkadres", "text"), ("Medewerker", "text"),
        ("Datum", "date"), ("Werkzaamheden", "textarea"), ("Duur (minuten)", "number")
    ]

def build_preview(app_name: str, prompt: str, modules: dict):
    slug = slugify(app_name)
    parts = []
    for label, typ in fields_for(prompt):
        name = slugify(label).replace("-", "_")
        if typ == "textarea":
            parts.append(f'<label>{label}<textarea name="{name}" rows="3"></textarea></label>')
        else:
            parts.append(f'<label>{label}<input type="{typ}" name="{name}"></label>')

    if modules.get("photos"):
        parts.append('<label>Foto\'s<input type="file" name="photos" accept="image/*" multiple></label>')

    if modules.get("signature"):
        parts.append(
            '<label>Handtekening'
            '<canvas id="signature" width="800" height="240"></canvas>'
            '<button type="button" id="clearSig" class="secondary">Wissen</button>'
            '</label>'
        )

    html = f"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#17324d">
<link rel="manifest" href="/generated/{slug}/manifest.json">
<link rel="stylesheet" href="/generated/{slug}/app.css">
<title>{app_name}</title>
</head>
<body>
<header><div class="app-icon">APP</div><div><strong>{app_name}</strong><small>Digitale bedrijfsapp</small></div></header>
<main>
<section class="hero"><span>Live preview</span><h1>{app_name}</h1><p>{prompt}</p></section>
<form id="mainForm">
<div class="card">{''.join(parts)}</div>
<button class="primary" type="button" onclick="alert('Preview klaar. In de geëxporteerde app wordt opslaan verder gekoppeld.')">Opslaan</button>
</form>
</main>
<script src="/generated/{slug}/app.js"></script>
</body>
</html>"""

    css = """*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,-apple-system,sans-serif;background:#f2f6f9;color:#17324d}
header{background:#17324d;color:#fff;padding:14px 18px;display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:3}
.app-icon{width:44px;height:44px;border-radius:13px;background:#e31c3d;display:grid;place-items:center;font-weight:900}
header strong{display:block}header small{display:block;opacity:.7;margin-top:2px}
main{max-width:760px;margin:auto;padding:18px 16px 80px}.hero{background:linear-gradient(135deg,#17324d,#2b5876);color:#fff;padding:24px;border-radius:24px;margin-bottom:16px;box-shadow:0 14px 36px rgba(23,50,77,.18)}
.hero h1{font-size:30px;margin:7px 0}.hero p{opacity:.88;line-height:1.45}.hero span{font-size:12px;text-transform:uppercase;letter-spacing:.1em;font-weight:900;opacity:.7}
.card{background:#fff;border-radius:22px;padding:20px;box-shadow:0 10px 30px rgba(23,50,77,.08)}
label{display:block;font-weight:800;margin-bottom:14px}input,textarea{width:100%;padding:14px;margin-top:7px;border:1px solid #cfdae3;border-radius:13px;font:inherit;background:#fff}
.primary,.secondary{border:0;border-radius:14px;padding:15px 18px;font-weight:900;font-size:16px}.primary{width:100%;margin-top:16px;background:#e31c3d;color:#fff}.secondary{background:#e8eef3;color:#17324d}
canvas{width:100%;height:140px;border:2px dashed #b9c7d2;border-radius:13px;touch-action:none;background:#fff;margin:8px 0}"""

    js = """const c=document.getElementById('signature');
if(c){
 const x=c.getContext('2d'); let d=false;
 const p=e=>{const r=c.getBoundingClientRect(),q=e.touches?e.touches[0]:e;return[(q.clientX-r.left)*c.width/r.width,(q.clientY-r.top)*c.height/r.height]};
 const s=e=>{d=true;const[a,b]=p(e);x.beginPath();x.moveTo(a,b);e.preventDefault()};
 const m=e=>{if(!d)return;const[a,b]=p(e);x.lineWidth=4;x.lineCap='round';x.lineTo(a,b);x.stroke();e.preventDefault()};
 ['mousedown','touchstart'].forEach(n=>c.addEventListener(n,s,{passive:false}));
 ['mousemove','touchmove'].forEach(n=>c.addEventListener(n,m,{passive:false}));
 ['mouseup','mouseleave','touchend'].forEach(n=>c.addEventListener(n,()=>d=false));
 document.getElementById('clearSig').onclick=()=>x.clearRect(0,0,c.width,c.height);
}"""

    manifest = json.dumps({
        "name": app_name,
        "short_name": app_name[:20],
        "start_url": f"/apps/{slug}",
        "display": "standalone",
        "background_color": "#f2f6f9",
        "theme_color": "#17324d"
    })

    return slug, {
        "preview.html": html,
        "app.css": css,
        "app.js": js,
        "manifest.json": manifest,
        "sw.js": "self.addEventListener('fetch',()=>{});"
    }

def create_export_zip(app_name: str, prompt: str, modules: dict, zip_path: Path):
    slug, preview = build_preview(app_name, prompt, modules)

    exported_html = (
        preview["preview.html"]
        .replace(f"/generated/{slug}/app.css", "/static/app.css")
        .replace(f"/generated/{slug}/app.js", "/static/app.js")
        .replace(f"/generated/{slug}/manifest.json", "/static/manifest.json")
    )
    exported_manifest = preview["manifest.json"].replace(f"/apps/{slug}", "/")

    requirements = [
        "fastapi==0.115.0",
        "uvicorn[standard]==0.30.6",
        "jinja2==3.1.4",
        "python-multipart==0.0.12",
    ]
    if modules.get("excel"):
        requirements.append("openpyxl==3.1.5")
    if modules.get("database"):
        requirements += ["sqlalchemy==2.0.36", "psycopg[binary]==3.2.3"]

    dockerfile = """FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
"""

    app_main = f"""from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title={app_name!r})
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {{"request": request}})

@app.get("/health")
def health():
    return {{"status": "ok"}}
"""

    with ZipFile(zip_path, "w", ZIP_DEFLATED) as z:
        z.writestr("requirements.txt", "\n".join(requirements) + "\n")
        z.writestr("Dockerfile", dockerfile)
        z.writestr("README.md", f"# {app_name}\n\nGegenereerd door Bedrijfsapp Builder V2.\n\nPrompt:\n{prompt}\n")
        z.writestr("app/__init__.py", "")
        z.writestr("app/main.py", app_main)
        z.writestr("app/templates/index.html", exported_html)
        z.writestr("app/static/app.css", preview["app.css"])
        z.writestr("app/static/app.js", preview["app.js"])
        z.writestr("app/static/manifest.json", exported_manifest)
        z.writestr("app/static/sw.js", preview["sw.js"])

    return slug
