
import os, json, httpx
from .schemas import ProductBrief, ModuleSpec, GeneratedFile, QAResult

SYSTEM_PROMPT = (
    "You are a product manager for an AI app builder. "
    "First understand the real requested product. Do not write code. "
    "Do not reduce a complex app to a generic planning app just because planning is one feature. "
    "Return JSON only with app_name, app_type, industry, target_users, primary_goal, modules, workflow and design_direction."
)

def settings(mode="turbo"):
    base = os.getenv("OLLAMA_BASE_URL","http://127.0.0.1:11434/v1").rstrip("/")
    model = os.getenv("OLLAMA_EXPERT_MODEL","gpt-oss:20b") if mode=="expert" else os.getenv("OLLAMA_TURBO_MODEL","qwen2.5-coder:7b")
    return base, model

async def status():
    base, _ = settings()
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            r=await client.get(base+"/models")
            r.raise_for_status()
            data=r.json()
            return {"online":True,"turbo":"qwen2.5-coder:7b","expert":"gpt-oss:20b","models":[x.get("id","") for x in data.get("data",[])]}
    except Exception:
        return {"online":False,"turbo":"qwen2.5-coder:7b","expert":"gpt-oss:20b","models":[]}

def extract_json(text):
    text=(text or "").strip()
    a,b=text.find("{"),text.rfind("}")
    if a>=0 and b>a:
        text=text[a:b+1]
    return json.loads(text)

async def make_brief(app_name,prompt,mode="turbo"):
    base,model=settings(mode)
    try:
        async with httpx.AsyncClient(timeout=420 if mode=="expert" else 240) as client:
            r=await client.post(
                base+"/chat/completions",
                headers={"Authorization":"Bearer ollama","Content-Type":"application/json"},
                json={"model":model,"messages":[
                    {"role":"system","content":SYSTEM_PROMPT},
                    {"role":"user","content":"APP NAME: "+app_name+"\\n\\nREQUEST:\\n"+prompt}
                ],"temperature":0.1,"stream":False}
            )
            r.raise_for_status()
            raw=extract_json(r.json()["choices"][0]["message"]["content"])
            raw["app_name"]=app_name
            return ProductBrief.model_validate(raw),True
    except Exception:
        return fallback_brief(app_name,prompt),False

def fallback_brief(app_name,prompt):
    p=prompt.lower()
    if any(x in p for x in ["wagenpark","bedrijfsbus","voertuig","fleet"]):
        raw=[
            ("Dashboard","KPI's, waarschuwingen en snelle acties","must"),
            ("Voertuigen","Bedrijfswagens, status, bestuurder en kilometerstand","must"),
            ("Busvoorraad","Materiaal en gereedschap per bus","must"),
            ("Barcode scanner","Materiaal met camera scannen","must"),
            ("Onderhoud","APK, service, verzekering en storingen","must"),
            ("Medewerkers","Bestuurders en voertuigtoewijzing","should"),
            ("Rapportages","Excel en mutatiehistorie","must"),
            ("GPS tracking","Later voertuigen live op kaart tonen","could")
        ]
        return ProductBrief(
            app_name=app_name,app_type="wagenpark- en busvoorraadplatform",industry="installatie/service",
            target_users=["monteurs","planners","beheerders"],
            primary_goal="voertuigen, busvoorraad en onderhoud centraal beheren",
            modules=[ModuleSpec(name=a,description=b,priority=c) for a,b,c in raw],
            workflow=["dashboard","voertuig kiezen","materiaal scannen","aantal registreren","projectnotitie toevoegen","onderhoud opvolgen","rapport exporteren"],
            design_direction="donker en professioneel met vaste zijbalk op desktop"
        )
    return ProductBrief(
        app_name=app_name,app_type="maatwerk bedrijfsapp",industry="maatwerk",
        target_users=["gebruikers"],primary_goal="het beschreven proces digitaliseren",
        modules=[
            ModuleSpec(name="Dashboard",description="Overzicht en snelle acties",priority="must"),
            ModuleSpec(name="Beheer",description="Belangrijkste gegevens beheren",priority="must")
        ],
        workflow=["overzicht","hoofdactie","opslaan","resultaat"],
        design_direction="clean en professioneel"
    )

def make_app(brief):
    modules=[m for m in brief.modules if m.enabled] or [ModuleSpec(name="Dashboard",description=brief.primary_goal,priority="must")]
    nav=[];mobile=[];views=[];icons=["H","M","V","S","R","I"]
    for i,m in enumerate(modules):
        active=" active" if i==0 else ""
        nav.append('<button class="nav%s" data-v="v%d"><span>%s</span>%s</button>'%(active,i,icons[i%len(icons)],m.name))
        if i<5:
            mobile.append('<button class="mnav%s" data-v="v%d">%s</button>'%(active,i,m.name[:8]))
        kpis=""
        if i==0:
            kpis='<div class="kpis"><article><span>Vandaag</span><b>12</b></article><article><span>Open</span><b>4</b></article><article><span>Waarschuwingen</span><b>3</b></article><article><span>Gereed</span><b>92%</b></article></div>'
        views.append(
            '<section class="view%s" id="v%d">'%(active,i)+
            '<div class="hero"><div><small>%s</small><h1>%s</h1><p>%s</p></div><button>+ Nieuw</button></div>'%(brief.industry,m.name,m.description)+
            kpis+
            '<div class="grid"><article class="card"><h2>%s</h2><p>%s</p><div class="rows">'%(m.name,m.description)+
            '<div><b>Voorbeeld A</b><span>Actief</span></div><div><b>Voorbeeld B</b><span>Gepland</span></div><div><b>Voorbeeld C</b><span>Afgerond</span></div></div></article>'+
            '<article class="card"><h2>Snelle acties</h2><button class="action">Nieuwe invoer</button><button class="action">Zoeken en filteren</button><button class="action">Rapportage</button></article></div></section>'
        )

    html=(
        '<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+
        '<link rel="stylesheet" href="/static/app.css"><title>'+brief.app_name+'</title></head><body>'+
        '<div class="shell"><aside><div class="brand"><b>A</b><div><strong>'+brief.app_name+'</strong><small>'+brief.app_type+'</small></div></div><nav>'+''.join(nav)+'</nav></aside>'+
        '<main><header><strong id="title">'+modules[0].name+'</strong><span>'+brief.design_direction+'</span></header>'+''.join(views)+'</main><nav class="mobile">'+''.join(mobile)+'</nav></div>'+
        '<script src="/static/app.js"></script></body></html>'
    )
    css="*{box-sizing:border-box}body{margin:0;background:#edf3f8;color:#132236;font-family:Inter,system-ui,sans-serif}.shell{min-height:100vh;display:grid;grid-template-columns:235px 1fr}aside{height:100vh;position:sticky;top:0;background:#0b1526;color:white;padding:18px 12px}.brand{display:flex;gap:10px;align-items:center;margin-bottom:24px}.brand>b{width:42px;height:42px;border-radius:13px;background:#2563eb;display:grid;place-items:center}.brand strong,.brand small{display:block}.brand small{color:#8290a5}.nav{width:100%;border:0;background:transparent;color:#8e9db1;text-align:left;padding:12px;border-radius:11px}.nav.active{background:#1c2a42;color:white}.nav span{display:inline-block;width:24px}main{padding:0 22px 70px}header{height:72px;display:flex;align-items:center;justify-content:space-between}header span{color:#718096;font-size:12px}.view{display:none}.view.active{display:block}.hero{background:linear-gradient(135deg,#10213a,#1e3a5f);color:white;border-radius:22px;padding:23px;display:flex;justify-content:space-between;align-items:center}.hero small{color:#93c5fd;text-transform:uppercase;letter-spacing:.1em}.hero h1{font-size:29px;margin:5px 0}.hero p{margin:0;color:#c8d5e3}.hero button,.action{border:0;border-radius:10px;padding:10px 13px;font-weight:800}.hero button{background:#2563eb;color:white}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:11px}.kpis article,.card{background:white;border:1px solid #dde6ef;border-radius:16px}.kpis article{padding:15px}.kpis span{display:block;color:#718096;font-size:12px}.kpis b{display:block;font-size:24px;margin-top:5px}.grid{display:grid;grid-template-columns:1.4fr 1fr;gap:11px;margin-top:11px}.card{padding:16px}.rows>div{display:flex;justify-content:space-between;padding:11px 0;border-bottom:1px solid #edf1f5}.rows span{color:#047857}.action{width:100%;text-align:left;background:#eef4ff;color:#1d4ed8;margin:6px 0}.mobile{display:none}@media(max-width:800px){.shell{display:block}aside{display:none}main{padding:0 12px 80px}.grid{grid-template-columns:1fr}.kpis{grid-template-columns:1fr 1fr}.mobile{position:fixed;display:grid;grid-template-columns:repeat(5,1fr);bottom:0;left:0;right:0;background:white;border-top:1px solid #dce4ec}.mnav{border:0;background:white;padding:10px 2px;color:#718096}.mnav.active{color:#2563eb}}"
    js="const titles=[...document.querySelectorAll('.nav')].map(x=>x.textContent.trim());function show(id){document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));document.getElementById(id).classList.add('active');document.querySelectorAll('.nav,.mnav').forEach(b=>b.classList.toggle('active',b.dataset.v===id));title.textContent=titles[Number(id.slice(1))]||'Dashboard'}document.querySelectorAll('[data-v]').forEach(b=>b.onclick=()=>show(b.dataset.v));"
    return [GeneratedFile(path="app/templates/index.html",content=html),GeneratedFile(path="app/static/app.css",content=css),GeneratedFile(path="app/static/app.js",content=js)]

def qa(brief,files):
    html=next(f.content for f in files if f.path.endswith("index.html")).lower()
    missing=[m.name for m in brief.modules if m.enabled and m.priority=="must" and m.name.lower() not in html]
    score=max(50,100-len(missing)*10)
    return QAResult(passed=score>=80,score=score,summary="Productplan gecontroleerd")
