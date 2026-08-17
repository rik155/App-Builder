
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json, re

def slugify(s):
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", s.strip()).strip("-").lower()
    return s or "app"

def classify(prompt):
    p = prompt.lower()
    if any(x in p for x in ["quiz","memory","clicker","reactiespel","reaction game","spelletje","game"]):
        kind = "game"
    elif any(x in p for x in ["voorraad","magazijn","barcode"]):
        kind = "inventory"
    elif any(x in p for x in ["dashboard","kpi","statistiek","overzicht"]):
        kind = "dashboard"
    elif any(x in p for x in ["calculator","bereken","rekenmachine"]):
        kind = "calculator"
    elif any(x in p for x in ["website","landing page","homepage"]):
        kind = "landing"
    else:
        kind = "form"

    if "quiz" in p:
        subtype = "quiz"
    elif "memory" in p:
        subtype = "memory"
    elif "reactie" in p or "reaction" in p:
        subtype = "reaction"
    else:
        subtype = "clicker"

    if "donker" in p or "dark" in p or "zwart" in p:
        theme = "dark"
    elif "rood" in p:
        theme = "red"
    elif "groen" in p:
        theme = "green"
    else:
        theme = "blue"

    return {"kind":kind,"subtype":subtype,"theme":theme}

def theme_values(theme):
    themes = {
        "blue": {"primary":"#17324d","accent":"#1f6feb","bg":"#eef3f7","card":"#ffffff","text":"#17324d"},
        "red": {"primary":"#301314","accent":"#e31c3d","bg":"#f8eeee","card":"#ffffff","text":"#321619"},
        "green": {"primary":"#113d2e","accent":"#21a66b","bg":"#edf7f2","card":"#ffffff","text":"#15372c"},
        "dark": {"primary":"#0b1020","accent":"#7c3aed","bg":"#0b1020","card":"#171f31","text":"#f5f7fb"},
    }
    return themes[theme]

def css_for(theme):
    t=theme_values(theme)
    return "*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,-apple-system,sans-serif;background:"+t["bg"]+";color:"+t["text"]+"}" +     "header{position:sticky;top:0;background:"+t["primary"]+";color:#fff;padding:14px 18px;display:flex;gap:12px;align-items:center;z-index:5}" +     ".logo{width:42px;height:42px;border-radius:13px;background:"+t["accent"]+";display:grid;place-items:center;font-weight:900}" +     "header small{display:block;opacity:.7}main{max-width:820px;margin:auto;padding:18px 16px 90px}" +     ".hero{background:"+t["primary"]+";color:#fff;border-radius:24px;padding:24px;margin-bottom:16px;box-shadow:0 14px 36px rgba(0,0,0,.14)}" +     ".card{background:"+t["card"]+";border-radius:22px;padding:20px;box-shadow:0 10px 28px rgba(0,0,0,.08);margin-bottom:16px}" +     "h1{margin:6px 0 10px}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.big{font-size:42px;font-weight:900}" +     "label{display:block;font-weight:800;margin-bottom:14px}input,textarea,select{width:100%;padding:14px;margin-top:7px;border:1px solid #cbd5df;border-radius:13px;font:inherit}" +     "button,.btn{border:0;border-radius:14px;padding:15px 18px;font-weight:900;font-size:16px;cursor:pointer;text-decoration:none}" +     ".primary{background:"+t["accent"]+";color:#fff}.secondary{background:#e8eef3;color:#17324d}" +     "@media(max-width:600px){.grid{grid-template-columns:1fr}}"

def wrap(title, prompt, body, theme):
    return (
        "<!doctype html><html lang='nl'><head>"
        "<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'>"
        "<link rel='stylesheet' href='./app.css'><link rel='manifest' href='./manifest.json'>"
        "<title>"+title+"</title></head><body>"
        "<header><div class='logo'>AI</div><div><strong>"+title+"</strong><small>Gegenereerde app</small></div></header>"
        "<main><section class='hero'><span>Live app</span><h1>"+title+"</h1><p>"+prompt+"</p></section>"+body+"</main>"
        "<script src='./app.js'></script></body></html>"
    )

def form_fields(prompt):
    p=prompt.lower()
    defs=[
        ("Klantnaam","text",["klant"]),
        ("Adres","text",["adres"]),
        ("Telefoon","tel",["telefoon"]),
        ("E-mail","email",["email","e-mail"]),
        ("Medewerker","text",["medewerker"]),
        ("Datum","date",["datum"]),
        ("Tijd","time",["tijd"]),
        ("Project","text",["project"]),
        ("Werkzaamheden","textarea",["werkzaamheden"]),
        ("Omschrijving","textarea",["omschrijving"]),
        ("Materialen","textarea",["materiaal"]),
        ("Opmerking","textarea",["opmerking"]),
        ("Aantal","number",["aantal"]),
        ("Uren","number",["uren"]),
    ]
    out=[]
    for label,typ,keys in defs:
        if any(k in p for k in keys):
            out.append((label,typ))
    if not out:
        out=[("Naam","text"),("Datum","date"),("Omschrijving","textarea")]
    return out

def build_form(prompt, modules):
    fields=form_fields(prompt)
    html=["<section class='card'>"]
    for label,typ in fields:
        name=slugify(label).replace("-","_")
        if typ=="textarea":
            html.append("<label>"+label+"<textarea name='"+name+"' rows='3'></textarea></label>")
        else:
            html.append("<label>"+label+"<input type='"+typ+"' name='"+name+"'></label>")
    if modules.get("photos"):
        html.append("<label>Foto's<input type='file' accept='image/*' multiple></label>")
    if modules.get("signature"):
        html.append("<label>Handtekening<canvas id='sig' width='800' height='240' style='width:100%;height:140px;border:2px dashed #b8c6d1;border-radius:12px;touch-action:none'></canvas><button type='button' id='clear' class='secondary'>Wissen</button></label>")
    html.append("<button class='primary' onclick=\"alert('Opgeslagen in preview')\">Opslaan</button></section>")
    js=""
    if modules.get("signature"):
        js="const c=document.getElementById('sig'),x=c.getContext('2d');let d=false;const p=e=>{const r=c.getBoundingClientRect(),q=e.touches?e.touches[0]:e;return[(q.clientX-r.left)*c.width/r.width,(q.clientY-r.top)*c.height/r.height]};const s=e=>{d=true;const[a,b]=p(e);x.beginPath();x.moveTo(a,b);e.preventDefault()};const m=e=>{if(!d)return;const[a,b]=p(e);x.lineWidth=4;x.lineTo(a,b);x.stroke();e.preventDefault()};['mousedown','touchstart'].forEach(n=>c.addEventListener(n,s,{passive:false}));['mousemove','touchmove'].forEach(n=>c.addEventListener(n,m,{passive:false}));['mouseup','mouseleave','touchend'].forEach(n=>c.addEventListener(n,()=>d=false));document.getElementById('clear').onclick=()=>x.clearRect(0,0,c.width,c.height);"
    return "".join(html),js

def build_inventory():
    body=(
        "<section class='grid'>"
        "<div class='card'><div>Producten</div><div class='big'>12</div></div>"
        "<div class='card'><div>Onder minimum</div><div class='big'>3</div></div>"
        "</section>"
        "<section class='card'><h2>Producten</h2>"
        "<div class='product'><b>Kit wit</b><p>Voorraad: <span>18</span></p><button class='secondary minus'>-1</button> <button class='primary plus'>+1</button></div><hr>"
        "<div class='product'><b>Roller 10 cm</b><p>Voorraad: <span>6</span></p><button class='secondary minus'>-1</button> <button class='primary plus'>+1</button></div>"
        "</section>"
    )
    js="document.querySelectorAll('.plus,.minus').forEach(b=>b.onclick=()=>{const s=b.parentElement.querySelector('span');let n=Number(s.textContent);n+=b.classList.contains('plus')?1:-1;s.textContent=Math.max(0,n)});"
    return body,js

def build_dashboard():
    body=(
        "<section class='grid'>"
        "<div class='card'><div>Vandaag</div><div class='big'>24</div><small>registraties</small></div>"
        "<div class='card'><div>Open</div><div class='big'>7</div><small>acties</small></div>"
        "<div class='card'><div>Deze week</div><div class='big'>126</div><small>totaal</small></div>"
        "<div class='card'><div>Gereed</div><div class='big'>92%</div><small>voortgang</small></div>"
        "</section>"
    )
    return body,""

def build_calculator():
    body="<section class='card'><label>Getal 1<input id='a' type='number' value='10'></label><label>Getal 2<input id='b' type='number' value='5'></label><button id='calc' class='primary'>Bereken</button><h2>Uitkomst: <span id='r'>15</span></h2></section>"
    js="document.getElementById('calc').onclick=()=>document.getElementById('r').textContent=Number(document.getElementById('a').value)+Number(document.getElementById('b').value);"
    return body,js

def build_landing():
    body="<section class='card'><h2>Welkom</h2><p>Een moderne mobiele pagina, gegenereerd vanuit je prompt.</p><button class='primary'>Neem contact op</button></section><section class='grid'><div class='card'><h3>Snel</h3><p>Mobiel ontwerp</p></div><div class='card'><h3>Duidelijk</h3><p>Eenvoudige structuur</p></div></section>"
    return body,""

def build_game(subtype):
    if subtype=="quiz":
        body="<section class='card'><h2>Wat is 2 + 2?</h2><div class='grid'><button class='secondary ans'>3</button><button class='primary ans' data-good='1'>4</button><button class='secondary ans'>5</button><button class='secondary ans'>6</button></div><h3>Score: <span id='score'>0</span></h3></section>"
        js="let s=0;document.querySelectorAll('.ans').forEach(b=>b.onclick=()=>{if(b.dataset.good){s++;b.textContent='✓ Goed'}else b.textContent='✕';document.getElementById('score').textContent=s});"
    elif subtype=="memory":
        body="<section class='card'><div id='memory' class='grid'></div><h3>Paren: <span id='pairs'>0</span>/4</h3></section>"
        js="const vals=['🍎','🚗','🔑','🎨','🍎','🚗','🔑','🎨'].sort(()=>Math.random()-.5);let open=[],pairs=0,m=document.getElementById('memory');vals.forEach(v=>{let b=document.createElement('button');b.className='secondary';b.style.minHeight='90px';b.textContent='?';b.onclick=()=>{if(open.length<2&&b.textContent==='?'){b.textContent=v;open.push([b,v]);if(open.length===2)setTimeout(()=>{if(open[0][1]===open[1][1]){pairs++;document.getElementById('pairs').textContent=pairs}else{open[0][0].textContent='?';open[1][0].textContent='?'}open=[]},450)}};m.appendChild(b)});"
    elif subtype=="reaction":
        body="<section class='card'><button id='reaction' class='primary' style='width:100%;height:240px;font-size:30px'>Start</button><h3 id='msg'>Druk op start</h3></section>"
        js="const b=document.getElementById('reaction'),m=document.getElementById('msg');let start=0,ready=false;b.onclick=()=>{if(ready){m.textContent=(performance.now()-start).toFixed(0)+' ms';ready=false;b.textContent='Nog een keer'}else{b.textContent='Wacht...';m.textContent='Niet te vroeg';setTimeout(()=>{ready=true;start=performance.now();b.textContent='NU!';m.textContent='Klik!'},1000+Math.random()*2500)}};"
    else:
        body="<section class='card' style='text-align:center'><div class='big' id='score'>0</div><p>punten</p><button id='clicker' class='primary' style='width:100%;height:180px;font-size:28px'>KLIK!</button></section>"
        js="let s=0;document.getElementById('clicker').onclick=()=>document.getElementById('score').textContent=++s;"
    return body,js

def build_app(title,prompt,modules):
    plan=classify(prompt)
    if plan["kind"]=="form":
        body,js=build_form(prompt,modules)
    elif plan["kind"]=="inventory":
        body,js=build_inventory()
    elif plan["kind"]=="dashboard":
        body,js=build_dashboard()
    elif plan["kind"]=="calculator":
        body,js=build_calculator()
    elif plan["kind"]=="landing":
        body,js=build_landing()
    else:
        body,js=build_game(plan["subtype"])

    html=wrap(title,prompt,body,plan["theme"])
    css=css_for(plan["theme"])
    manifest=json.dumps({"name":title,"short_name":title[:20],"start_url":"./index.html","display":"standalone","background_color":theme_values(plan["theme"])["bg"],"theme_color":theme_values(plan["theme"])["primary"]})
    return plan,{"index.html":html,"app.css":css,"app.js":js,"manifest.json":manifest,"sw.js":"self.addEventListener('fetch',()=>{});"}

def export_zip(title,prompt,modules,path):
    plan,files=build_app(title,prompt,modules)
    with ZipFile(path,"w",ZIP_DEFLATED) as z:
        for name,content in files.items():
            z.writestr(name,content)
        z.writestr("README.txt","Gegenereerd door Smart App Builder V3\nType: "+plan["kind"]+"\nPrompt: "+prompt+"\n")
    return plan
