
import re
from .schemas import BuildPlan, PageSpec, FeatureSpec, GeneratedProject, GeneratedFile, DiscoveryResult, ClarifyingQuestion

def fallback_discovery(app_name: str, prompt: str) -> DiscoveryResult:
    p = prompt.lower()
    questions = []
    features = []
    assumptions = []

    if any(x in p for x in ["offerte", "quotation", "quote"]):
        app_type = "offertegenerator"
        features = [
            FeatureSpec(name="BTW-berekening", description="Automatisch 0%, 9% of 21% btw per regel"),
            FeatureSpec(name="Meerdere offertregels", description="Aantal, omschrijving en prijs per regel"),
            FeatureSpec(name="PDF / print", description="Nette offerte kunnen printen of als PDF bewaren"),
            FeatureSpec(name="Klanten", description="Klantgegevens hergebruiken"),
        ]
        if "pdf" not in p:
            questions.append(ClarifyingQuestion(id="pdf", question="Wil je offertes als PDF kunnen downloaden of printen?", why="Dit hoort meestal bij een offerte-app.", type="boolean", recommended_answer="Ja"))
        if "logo" not in p:
            questions.append(ClarifyingQuestion(id="logo", question="Moet er een bedrijfslogo en eigen huisstijl in de offerte komen?", why="Dan ziet de offerte er professioneel uit.", type="boolean", recommended_answer="Ja"))
        if "mail" not in p and "email" not in p and "e-mail" not in p:
            questions.append(ClarifyingQuestion(id="email", question="Wil je een offerte vanuit de app per e-mail kunnen versturen?", why="Dit voorkomt downloaden en daarna handmatig mailen.", type="boolean", recommended_answer="Ja"))
        questions.append(ClarifyingQuestion(id="vat", question="Welke btw-tarieven moeten beschikbaar zijn?", why="Voor correcte berekening.", type="choice", options=["21%","9% en 21%","0%, 9% en 21%"], recommended_answer="0%, 9% en 21%"))
    elif any(x in p for x in ["spel", "game", "quiz", "memory", "clicker", "reactie"]):
        app_type = "game"
        features = [
            FeatureSpec(name="Score", description="Score of tijd bijhouden"),
            FeatureSpec(name="Opnieuw spelen", description="Nieuwe ronde starten"),
            FeatureSpec(name="Mobiel", description="Goed speelbaar op telefoon"),
        ]
        if not any(x in p for x in ["score","punten","tijd"]):
            questions.append(ClarifyingQuestion(id="score", question="Hoe wil je de score bepalen?", why="Dat bepaalt de spelregels.", type="choice", options=["Punten","Tijd","Highscore","Geen score"], recommended_answer="Highscore"))
        questions.append(ClarifyingQuestion(id="sound", question="Wil je geluid en/of trilling gebruiken?", why="Dat maakt een spel vaak leuker op mobiel.", type="choice", options=["Geluid","Trilling","Beide","Geen"], recommended_answer="Beide"))
        questions.append(ClarifyingQuestion(id="difficulty", question="Moet het spel moeilijker worden naarmate je verder komt?", why="Voor meer uitdaging.", type="boolean", recommended_answer="Ja"))
    elif any(x in p for x in ["voorraad", "magazijn", "barcode"]):
        app_type = "voorraadapp"
        features = [
            FeatureSpec(name="Barcode scanner", description="Producten snel scannen"),
            FeatureSpec(name="Minimumvoorraad", description="Melding bij lage voorraad"),
            FeatureSpec(name="Mutaties", description="Historie van in- en uitboekingen"),
        ]
        if "barcode" not in p:
            questions.append(ClarifyingQuestion(id="barcode", question="Wil je producten met de telefooncamera via barcode scannen?", why="Dit maakt in- en uitboeken veel sneller.", type="boolean", recommended_answer="Ja"))
        questions.append(ClarifyingQuestion(id="who", question="Moet worden bijgehouden wie voorraad wijzigt?", why="Handig voor mutatiegeschiedenis.", type="boolean", recommended_answer="Ja"))
        questions.append(ClarifyingQuestion(id="export", question="Wil je een Excel- of CSV-export van voorraad en mutaties?", why="Handig voor kantoor en back-up.", type="choice", options=["Excel","CSV","Beide","Geen"], recommended_answer="Excel"))
    else:
        app_type = "maatwerk webapp"
        features = [
            FeatureSpec(name="Mobiel ontwerp", description="Goed bruikbaar op telefoon"),
            FeatureSpec(name="Opslaan", description="Gegevens of voortgang bewaren"),
        ]
        questions.append(ClarifyingQuestion(id="users", question="Wie gaat deze app vooral gebruiken?", why="Daarop kan de bediening worden afgestemd.", type="text", recommended_answer="Medewerkers"))
        questions.append(ClarifyingQuestion(id="login", question="Moeten gebruikers inloggen?", why="Nodig als gegevens per gebruiker afgeschermd moeten worden.", type="boolean", recommended_answer="Nee"))
        questions.append(ClarifyingQuestion(id="data", question="Moet de app gegevens permanent opslaan?", why="Dan is een database nodig.", type="boolean", recommended_answer="Ja"))

    if not any(x in p for x in ["iphone","telefoon","mobiel","mobile","desktop","pc"]):
        questions.append(ClarifyingQuestion(id="device", question="Waar moet de app vooral goed op werken?", why="Dit bepaalt de lay-out.", type="choice", options=["iPhone/Android","Desktop/laptop","Beide"], recommended_answer="Beide"))
    if not any(x in p for x in ["donker","dark","rood","groen","blauw","stijl","modern","clean"]):
        questions.append(ClarifyingQuestion(id="style", question="Welke uitstraling wil je?", why="De AI gebruikt dit voor het ontwerp.", type="choice", options=["Clean en professioneel","Donker en modern","Licht en minimalistisch","Kleurrijk en speels"], recommended_answer="Clean en professioneel"))

    return DiscoveryResult(
        summary=f"Ik denk dat je een {app_type} wilt bouwen. Ik wil eerst een paar keuzes bevestigen zodat de app beter bij je doel past.",
        detected_app_type=app_type,
        suggested_features=features,
        questions=questions[:6],
        assumptions=assumptions
    )

def fallback_plan(app_name: str, prompt: str) -> BuildPlan:
    p = prompt.lower()
    app_type = "web app"
    features = []
    entities = []
    pages = []

    if any(x in p for x in ["offerte", "quotation", "quote"]):
        app_type = "offertegenerator"
        pages = [
            PageSpec(name="Dashboard", route="/", purpose="Overzicht van offertes en snelle acties"),
            PageSpec(name="Nieuwe offerte", route="/offerte", purpose="Offerte opstellen"),
            PageSpec(name="Klanten", route="/klanten", purpose="Klanten beheren"),
        ]
        features = [
            FeatureSpec(name="Offerte regels", description="Meerdere regels met omschrijving, aantal, prijs en btw"),
            FeatureSpec(name="Automatische totalen", description="Subtotaal, btw en eindtotaal"),
            FeatureSpec(name="PDF/print", description="Printvriendelijke offerte"),
        ]
        entities = ["Klant", "Offerte", "OfferteRegel"]
    elif any(x in p for x in ["spel", "game", "quiz", "memory", "clicker", "reactie"]):
        app_type = "game"
        pages = [PageSpec(name="Spel", route="/", purpose="Direct spelen")]
        features = [FeatureSpec(name="Score", description="Score bijhouden"), FeatureSpec(name="Opnieuw", description="Nieuwe ronde starten")]
        entities = ["GameSession"]
    elif any(x in p for x in ["voorraad", "magazijn", "barcode"]):
        app_type = "voorraadapp"
        pages = [PageSpec(name="Dashboard", route="/", purpose="Voorraadoverzicht"), PageSpec(name="Producten", route="/producten", purpose="Producten beheren")]
        features = [FeatureSpec(name="Voorraad aanpassen", description="In- en uitboeken"), FeatureSpec(name="Minimumvoorraad", description="Waarschuwing bij lage voorraad")]
        entities = ["Product", "Mutatie"]
    else:
        pages = [PageSpec(name="Dashboard", route="/", purpose="Hoofdscherm"), PageSpec(name="Nieuw", route="/nieuw", purpose="Nieuwe invoer")]
        features = [FeatureSpec(name="Opslaan", description="Invoer bewaren"), FeatureSpec(name="Mobiel", description="Responsive interface")]
        entities = ["Record"]

    style = "clean, modern, professional"
    colors = "dark navy with a bright accent"
    if "donker" in p or "dark" in p:
        style = "dark, sleek, modern"
    if "rood" in p:
        colors = "black, white and red"
    if "groen" in p:
        colors = "white, deep green and mint"

    return BuildPlan(
        app_name=app_name, app_type=app_type, visual_style=style, color_direction=colors,
        pages=pages, features=features, data_entities=entities, notes=[]
    )

def fallback_project(plan: BuildPlan, prompt: str) -> GeneratedProject:
    app_name = plan.app_name
    kind = plan.app_type

    if kind == "offertegenerator":
        body = """
<section class="hero"><div><span class="eyebrow">Nieuwe offerte</span><h1>Maak in minuten een nette offerte</h1><p>Voeg klantgegevens en regels toe. BTW en totaal worden direct berekend.</p></div><button id="printBtn" class="ghost">Print / PDF</button></section>
<section class="layout"><div class="panel"><h2>Klant</h2><div class="two"><label>Naam<input id="customer" placeholder="Klantnaam"></label><label>Datum<input type="date" id="date"></label></div><label>Adres<input id="address" placeholder="Straat, plaats"></label></div>
<div class="panel"><div class="section-head"><h2>Offerte regels</h2><button id="addRow" class="small">+ Regel</button></div><div id="rows"></div><div class="totals"><div><span>Subtotaal</span><strong id="subtotal">€ 0,00</strong></div><div><span>BTW</span><strong id="vat">€ 0,00</strong></div><div class="grand"><span>Totaal</span><strong id="total">€ 0,00</strong></div></div></div></section>
"""
        js = """
const rows=document.getElementById('rows');function euro(n){return new Intl.NumberFormat('nl-NL',{style:'currency',currency:'EUR'}).format(n||0)}
function calc(){let sub=0,vat=0;document.querySelectorAll('.quote-row').forEach(r=>{const q=Number(r.querySelector('.qty').value||0),p=Number(r.querySelector('.price').value||0),v=Number(r.querySelector('.vat').value||0);sub+=q*p;vat+=q*p*(v/100)});subtotal.textContent=euro(sub);document.getElementById('vat').textContent=euro(vat);total.textContent=euro(sub+vat)}
function addRow(){const r=document.createElement('div');r.className='quote-row';r.innerHTML=`<input class="desc" placeholder="Omschrijving"><input class="qty" type="number" value="1"><input class="price" type="number" step=".01" placeholder="Prijs"><select class="vat"><option value="21">21%</option><option value="9">9%</option><option value="0">0%</option></select><button class="remove">×</button>`;r.querySelectorAll('input,select').forEach(x=>x.addEventListener('input',calc));r.querySelector('.remove').onclick=()=>{r.remove();calc()};rows.appendChild(r);calc()}addRow();addRow();addRow();document.getElementById('addRow').onclick=addRow;document.getElementById('printBtn').onclick=()=>window.print();document.getElementById('date').valueAsDate=new Date();
"""
    elif kind == "game":
        body = """
<section class="hero"><div><span class="eyebrow">Game</span><h1>Reactiespel</h1><p>Wacht op groen en klik zo snel mogelijk.</p></div></section>
<section class="panel game-panel"><div class="best">Beste tijd: <strong id="best">—</strong></div><button id="reaction" class="reaction">START</button><p id="message">Klaar?</p></section>
"""
        js = """
const b=document.getElementById('reaction'),m=document.getElementById('message'),bestEl=document.getElementById('best');let ready=false,start=0,timer=null,best=Number(localStorage.getItem('bestReaction')||0);if(best)bestEl.textContent=best+' ms';b.onclick=()=>{if(ready){const t=Math.round(performance.now()-start);ready=false;b.className='reaction';b.textContent='NOG EEN KEER';m.textContent=t+' ms';if(!best||t<best){best=t;localStorage.setItem('bestReaction',best);bestEl.textContent=best+' ms'}return}clearTimeout(timer);b.className='reaction waiting';b.textContent='WACHT...';timer=setTimeout(()=>{ready=true;start=performance.now();b.className='reaction go';b.textContent='NU!';m.textContent='Klik!'},1200+Math.random()*2200)};
"""
    elif kind == "voorraadapp":
        body = """
<section class="hero"><div><span class="eyebrow">Voorraad</span><h1>Alles direct in beeld</h1><p>Bekijk, zoek en pas voorraad aan.</p></div><button class="ghost">+ Product</button></section>
<section class="stats"><div class="stat"><span>Producten</span><strong>24</strong></div><div class="stat danger"><span>Bijbestellen</span><strong>3</strong></div></section><section class="panel"><input id="search" class="search" placeholder="Zoek product..."><div id="productList"></div></section>
"""
        js = """
let products=[['Kit wit',18,5],['Roller 10 cm',6,8],['Afplaktape',22,10],['Schuurspons',3,5]];function render(q=''){productList.innerHTML='';products.filter(p=>p[0].toLowerCase().includes(q.toLowerCase())).forEach(p=>{const d=document.createElement('div');d.className='product';d.innerHTML=`<div><strong>${p[0]}</strong><small>${p[1]<=p[2]?'Onder minimum':'Op voorraad'}</small></div><div class="stock"><button data-d="-1">−</button><b>${p[1]}</b><button data-d="1">+</button></div>`;d.querySelectorAll('button').forEach(b=>b.onclick=()=>{p[1]=Math.max(0,p[1]+Number(b.dataset.d));render(search.value)});productList.appendChild(d)})}search.oninput=()=>render(search.value);render();
"""
    else:
        body = """
<section class="hero"><div><span class="eyebrow">Nieuwe app</span><h1>Snelle invoer</h1><p>Een moderne basis die uit je prompt en antwoorden is opgebouwd.</p></div></section>
<section class="panel"><div class="two"><label>Naam<input placeholder="Naam"></label><label>Datum<input type="date"></label></div><label>Omschrijving<textarea rows="5" placeholder="Schrijf hier..."></textarea></label><button class="primary">Opslaan</button></section>
"""
        js = ""

    html = f"""<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#0f172a"><link rel="stylesheet" href="/static/app.css"><link rel="manifest" href="/static/manifest.json"><title>{app_name}</title></head><body><header><div class="brandmark">◆</div><div><strong>{app_name}</strong><small>{kind}</small></div></header><main>{body}</main><script src="/static/app.js"></script></body></html>"""
    css = """*{box-sizing:border-box}body{margin:0;background:#f4f7fb;color:#122033;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}header{height:72px;display:flex;align-items:center;gap:12px;padding:0 24px;background:#0f172a;color:#fff;position:sticky;top:0;z-index:20}header strong{display:block;font-size:16px}header small{display:block;opacity:.6}.brandmark{width:40px;height:40px;border-radius:13px;background:linear-gradient(135deg,#7c3aed,#2563eb);display:grid;place-items:center}main{max-width:1120px;margin:auto;padding:32px 22px 90px}.hero{border-radius:28px;padding:34px;background:linear-gradient(135deg,#0f172a,#1e3a5f);color:#fff;display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:22px}.hero h1{font-size:38px;margin:7px 0}.hero p{max-width:700px;color:#d9e3f0}.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:11px;font-weight:900;color:#93c5fd}.panel,.stat{background:#fff;border-radius:22px;box-shadow:0 10px 34px rgba(20,38,63,.07);border:1px solid #e5ebf2}.panel{padding:22px;margin-bottom:20px}.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}label{display:block;font-size:13px;font-weight:800;margin-bottom:14px}input,textarea,select{width:100%;margin-top:7px;border:1px solid #d8e1ea;background:#fbfdff;border-radius:12px;padding:13px;font:inherit}.primary,.ghost,.small,.stock button,.remove{border:0;border-radius:12px;font-weight:800;cursor:pointer}.primary{background:#2563eb;color:#fff;padding:14px 19px}.ghost{background:#fff;color:#0f172a;padding:12px 16px}.small{background:#eef4ff;color:#1d4ed8;padding:10px 13px}.section-head{display:flex;align-items:center;justify-content:space-between}.quote-row{display:grid;grid-template-columns:3fr .8fr 1.1fr .8fr 42px;gap:8px;margin-bottom:9px}.quote-row input,.quote-row select{margin:0}.remove{background:#fff0f0;color:#c24141}.totals{margin-left:auto;max-width:360px;margin-top:24px;border-top:1px solid #e5e7eb;padding-top:10px}.totals>div{display:flex;justify-content:space-between;padding:7px 0}.totals .grand{font-size:20px;border-top:1px solid #e5e7eb;margin-top:5px;padding-top:14px}.stats{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px}.stat{padding:22px}.stat span{display:block;color:#64748b}.stat strong{display:block;font-size:38px}.stat.danger strong{color:#dc2626}.search{margin:0 0 12px}.product{display:flex;align-items:center;justify-content:space-between;padding:14px 4px;border-bottom:1px solid #edf1f5}.product small{display:block;color:#64748b}.stock{display:flex;align-items:center;gap:12px}.stock button{width:38px;height:38px;background:#eef4ff;color:#1d4ed8;font-size:20px}.reaction{width:100%;min-height:300px;border:0;border-radius:24px;background:#2563eb;color:#fff;font-size:34px;font-weight:900}.reaction.waiting{background:#f59e0b}.reaction.go{background:#16a34a}.game-panel{text-align:center}.best{margin-bottom:14px;color:#64748b}@media(max-width:720px){main{padding:18px 14px 70px}.hero{padding:24px}.hero h1{font-size:30px}.two{grid-template-columns:1fr}.quote-row{grid-template-columns:1fr 70px 90px 70px 38px}}"""
    return GeneratedProject(plan=plan,files=[GeneratedFile(path="app/templates/index.html",content=html),GeneratedFile(path="app/static/app.css",content=css),GeneratedFile(path="app/static/app.js",content=js)])
