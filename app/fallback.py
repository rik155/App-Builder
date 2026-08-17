
from .schemas import (
    BuildPlan, PageSpec, FeatureSpec, GeneratedProject, GeneratedFile,
    DiscoveryResult, ClarifyingQuestion, ContextProfile, ArchitectureReview
)

def _q(id, question, why="", type="text", options=None, recommended=None):
    return ClarifyingQuestion(
        id=id, question=question, why=why, type=type,
        options=options or [], recommended_answer=recommended
    )

def fallback_discovery(app_name: str, prompt: str) -> DiscoveryResult:
    p=prompt.lower()
    questions=[]; features=[]; assumptions=[]
    industry="onbekend / maatwerk"; users=["nog te bepalen"]; goal="het beschreven proces digitaliseren"
    workflow=["start","hoofdactie","resultaat"]; objects=["gegevens"]; integrations=[]; risks=[]

    if any(x in p for x in ["schoonmaak","cleaning"]):
        industry="schoonmaakbedrijf"; users=["planner/kantoor","schoonmaakmedewerkers"]
        goal="opdrachten plannen en uitvoering eenvoudig registreren"
        workflow=["opdracht aanmaken","medewerker inplannen","naar locatie","werk uitvoeren","opleveren"]
        objects=["klanten","opdrachten","medewerkers","locaties","foto's","uren"]
        integrations=["navigatie/kaarten","e-mail"]
        features=[
            FeatureSpec(name="Dag- en weekplanning",description="Opdrachten per medewerker plannen"),
            FeatureSpec(name="Opdrachtstatus",description="Gepland, onderweg, bezig, afgerond"),
            FeatureSpec(name="Foto's voor/na",description="Uitvoering vastleggen"),
            FeatureSpec(name="Klantondertekening",description="Oplevering bevestigen"),
        ]
        questions=[
            _q("recurring","Hebben jullie terugkerende schoonmaakopdrachten die automatisch opnieuw gepland moeten worden?","Veel schoonmaakbedrijven werken met vaste bezoeken.","boolean",recommended="Ja"),
            _q("planning_view","Welke planning is het belangrijkst voor kantoor?","Dit bepaalt het hoofdscherm.","choice",["Dagplanning","Weekplanning","Beide"],"Beide"),
            _q("travel","Moet de app reistijd of route tussen adressen helpen plannen?","Handig bij meerdere opdrachten per dag.","boolean",recommended="Ja"),
            _q("completion","Wat moet een medewerker bij afronding vastleggen?","Zo blijft de mobiele flow kort maar compleet.","choice",["Alleen status","Status + foto's","Status + foto's + handtekening"],"Status + foto's + handtekening"),
        ]
    elif any(x in p for x in ["dierenarts","veterinary","dierenkliniek"]):
        industry="dierenartspraktijk"; users=["balie","dierenarts","assistente"]
        goal="afspraken en dierdossiers beheren"
        workflow=["eigenaar registreren","dier registreren","afspraak plannen","consult","behandeling vastleggen","herinnering"]
        objects=["eigenaren","dieren","afspraken","consulten","vaccinaties","medicatie"]
        integrations=["e-mail/SMS herinneringen"]; risks=["privacygevoelige dossierinformatie"]
        features=[
            FeatureSpec(name="Dierdossier",description="Historie per dier"),
            FeatureSpec(name="Afspraken",description="Agenda voor consulten"),
            FeatureSpec(name="Vaccinatieherinneringen",description="Automatische opvolging"),
        ]
        questions=[
            _q("multi_pet","Moet één eigenaar meerdere dieren kunnen hebben?","Dit is meestal nodig in een dierenartsdossier.","boolean",recommended="Ja"),
            _q("online_booking","Mogen klanten zelf online afspraken aanvragen of boeken?","Dit verandert de planning en toegangsrechten.","boolean",recommended="Ja"),
            _q("medical","Welke medische informatie moet minimaal in het dossier staan?","Dit bepaalt het dossierontwerp.","choice",["Consultnotities","Consultnotities + medicatie","Consultnotities + medicatie + vaccinaties"],"Consultnotities + medicatie + vaccinaties"),
            _q("reminders","Wil je automatische herinneringen voor afspraken of vaccinaties?","Veelgebruikte functie in dierenartssoftware.","choice",["Alleen afspraken","Alleen vaccinaties","Beide","Geen"],"Beide"),
        ]
    elif any(x in p for x in ["game","spel","quiz","memory","reactie","clicker"]):
        industry="entertainment / game"; users=["spelers"]; goal="een leuk en direct speelbaar spel maken"
        workflow=["start","spelen","score/tijd meten","resultaat","opnieuw"]; objects=["spelronde","score","highscore"]
        features=[
            FeatureSpec(name="Highscore",description="Beste resultaat bewaren"),
            FeatureSpec(name="Mobiele feedback",description="Geluid en/of trilling"),
            FeatureSpec(name="Opnieuw spelen",description="Direct nieuwe ronde"),
        ]
        questions=[
            _q("scoring","Hoe wil je winnen of scoren?","Dit bepaalt de spelregels.","choice",["Punten","Snelste tijd","Langste reeks","Levels"],"Snelste tijd"),
            _q("difficulty","Moet het spel steeds moeilijker worden?","Geeft meer uitdaging.","boolean",recommended="Ja"),
            _q("feedback","Wil je geluid, trilling of allebei?","Geeft duidelijke mobiele feedback.","choice",["Geluid","Trilling","Beide","Geen"],"Beide"),
        ]
    elif any(x in p for x in ["voorraad","magazijn","barcode"]):
        industry="voorraadbeheer"; users=["magazijnmedewerkers","kantoor"]; goal="voorraad snel en betrouwbaar bijhouden"
        workflow=["product zoeken/scannen","aantal aanpassen","mutatie opslaan","lage voorraad signaleren"]
        objects=["producten","barcodes","mutaties","minimumvoorraad"]
        integrations=["Excel"]
        features=[
            FeatureSpec(name="Barcode scanner",description="Producten snel scannen"),
            FeatureSpec(name="Minimumvoorraad",description="Waarschuwing bij lage voorraad"),
            FeatureSpec(name="Mutaties",description="Historie van wijzigingen"),
        ]
        questions=[
            _q("barcode","Wil je producten met de telefooncamera scannen?","Dit versnelt dagelijks gebruik.","boolean",recommended="Ja"),
            _q("who","Moet worden bijgehouden wie de voorraad wijzigt?","Handig voor mutatiegeschiedenis.","boolean",recommended="Ja"),
            _q("export","Wil je een Excel- of CSV-export?","Handig voor kantoor en back-up.","choice",["Excel","CSV","Beide","Geen"],"Excel"),
        ]
    elif any(x in p for x in ["offerte","quote","quotation"]):
        industry="offerte/verkoop"; users=["kantoor/verkoop"]; goal="professionele offertes maken en versturen"
        workflow=["klant kiezen","regels toevoegen","prijzen/btw berekenen","controleren","versturen"]
        objects=["klanten","offertes","offerte-regels","prijzen","btw"]; integrations=["PDF","e-mail"]
        features=[
            FeatureSpec(name="Meerdere offertregels",description="Aantal, omschrijving, prijs en btw"),
            FeatureSpec(name="Automatische totalen",description="Subtotaal, btw en eindtotaal"),
            FeatureSpec(name="PDF",description="Professionele offerte exporteren"),
        ]
        questions=[
            _q("customer_db","Wil je klanten opslaan en later opnieuw kiezen?","Bespaart tijd bij terugkerende klanten.","boolean",recommended="Ja"),
            _q("approval","Moet een klant de offerte digitaal kunnen accepteren?","Maakt opvolging makkelijker.","boolean",recommended="Ja"),
            _q("vat","Welke btw-tarieven moeten beschikbaar zijn?","Voor correcte berekening.","choice",["21%","9% en 21%","0%, 9% en 21%"],"0%, 9% en 21%"),
        ]
    else:
        features=[
            FeatureSpec(name="Mobiel ontwerp",description="Goed bruikbaar op telefoon"),
            FeatureSpec(name="Opslag",description="Gegevens of voortgang bewaren indien nodig"),
        ]
        questions=[
            _q("users","Wie gaat deze app dagelijks gebruiken?","Dit bepaalt hoe eenvoudig of uitgebreid de bediening moet zijn.","text",recommended="Medewerkers"),
            _q("main_job","Wat is de belangrijkste handeling die iemand in de app moet kunnen doen?","Dit hoort centraal op het hoofdscherm te staan.","text"),
            _q("data","Moet de app gegevens bewaren voor later?","Dan is opslag nodig.","boolean",recommended="Ja"),
        ]

    if not any(x in p for x in ["donker","dark","licht","clean","professioneel","modern","minimalistisch","speels","rood","groen","blauw"]):
        questions.append(_q("style","Welke uitstraling past het best?","De app kan daarop worden vormgegeven.","choice",["Clean en professioneel","Donker en modern","Licht en minimalistisch","Kleurrijk en speels"],"Clean en professioneel"))

    return DiscoveryResult(
        summary=f"Ik begrijp dit als een app voor {industry}. Het belangrijkste doel lijkt: {goal}.",
        detected_app_type=industry,
        context=ContextProfile(
            industry=industry,target_users=users,core_goal=goal,core_workflow=workflow,
            important_objects=objects,possible_integrations=integrations,risks_or_constraints=risks
        ),
        suggested_features=features,questions=questions[:6],assumptions=assumptions
    )

def fallback_plan(app_name: str, prompt: str) -> BuildPlan:
    p=prompt.lower()
    if "schoonmaak" in p or "planning" in p:
        app_type="planning-app"
        pages=[
            PageSpec(name="Vandaag",route="/",purpose="Dagplanning en status"),
            PageSpec(name="Planning",route="/planning",purpose="Weekplanning"),
            PageSpec(name="Opdrachten",route="/opdrachten",purpose="Opdrachten beheren"),
            PageSpec(name="Medewerkers",route="/medewerkers",purpose="Beschikbaarheid en toewijzing"),
        ]
        features=[
            FeatureSpec(name="Statusworkflow",description="Gepland, onderweg, bezig, afgerond"),
            FeatureSpec(name="Foto's",description="Voor/na foto's"),
            FeatureSpec(name="Handtekening",description="Klant akkoord"),
            FeatureSpec(name="Routes",description="Adres en routeknop"),
        ]
        entities=["Klant","Opdracht","Medewerker","Foto","Planning"]
    elif "dierenarts" in p:
        app_type="dierenarts-app"
        pages=[
            PageSpec(name="Agenda",route="/",purpose="Afspraken"),
            PageSpec(name="Dieren",route="/dieren",purpose="Dierdossiers"),
            PageSpec(name="Eigenaren",route="/eigenaren",purpose="Eigenaren beheren"),
        ]
        features=[
            FeatureSpec(name="Dierdossier",description="Historie per dier"),
            FeatureSpec(name="Herinneringen",description="Afspraken en vaccinaties"),
        ]
        entities=["Eigenaar","Dier","Afspraak","Consult","Vaccinatie"]
    elif "game" in p or "spel" in p or "reactie" in p:
        app_type="game"
        pages=[PageSpec(name="Spel",route="/",purpose="Direct spelen")]
        features=[
            FeatureSpec(name="Score",description="Resultaat bijhouden"),
            FeatureSpec(name="Highscore",description="Beste resultaat bewaren"),
        ]
        entities=["GameSession"]
    elif "voorraad" in p or "barcode" in p:
        app_type="voorraad-app"
        pages=[
            PageSpec(name="Dashboard",route="/",purpose="Overzicht"),
            PageSpec(name="Producten",route="/producten",purpose="Producten beheren"),
        ]
        features=[
            FeatureSpec(name="Scanner",description="Barcode scannen"),
            FeatureSpec(name="Minimumvoorraad",description="Lage voorraad"),
        ]
        entities=["Product","Mutatie"]
    elif "offerte" in p:
        app_type="offertegenerator"
        pages=[
            PageSpec(name="Dashboard",route="/",purpose="Overzicht"),
            PageSpec(name="Nieuwe offerte",route="/offerte",purpose="Offerte maken"),
            PageSpec(name="Klanten",route="/klanten",purpose="Klanten beheren"),
        ]
        features=[
            FeatureSpec(name="Offerte regels",description="Aantal, prijs, btw"),
            FeatureSpec(name="Automatische totalen",description="Subtotaal en totaal"),
            FeatureSpec(name="PDF",description="Printvriendelijke offerte"),
        ]
        entities=["Klant","Offerte","OfferteRegel"]
    else:
        app_type="maatwerk-app"
        pages=[
            PageSpec(name="Dashboard",route="/",purpose="Hoofdscherm"),
            PageSpec(name="Nieuw",route="/nieuw",purpose="Nieuwe invoer"),
        ]
        features=[FeatureSpec(name="Opslaan",description="Gegevens bewaren")]
        entities=["Record"]

    return BuildPlan(
        app_name=app_name,app_type=app_type,visual_style="clean, modern, professional",
        color_direction="dark navy with bright accent",pages=pages,features=features,
        data_entities=entities,notes=[],
        architecture_review=ArchitectureReview(
            understands_industry=True,understands_users=True,understands_workflow=True,
            understands_screens=True,understands_data=True,understands_integrations=True,
            understands_visual_style=True,notes=["Fallback architectuurcheck voltooid."]
        )
    )

def fallback_project(plan: BuildPlan) -> GeneratedProject:
    # Domain-specific fallback screens. No raw prompt/context is ever displayed.
    kind=plan.app_type
    title=plan.app_name

    if kind=="planning-app":
        body="""
<section class="topbar">
  <div><span class="eyebrow">Vandaag</span><h1>Planning</h1><p>4 opdrachten · 3 medewerkers actief</p></div>
  <button class="primary">+ Opdracht</button>
</section>
<section class="stats"><div><span>Vandaag</span><strong>4</strong></div><div><span>Bezig</span><strong>2</strong></div><div><span>Afgerond</span><strong>1</strong></div></section>
<section class="panel">
  <div class="sectionhead"><h2>Dagplanning</h2><div class="tabs"><button class="active">Vandaag</button><button>Week</button></div></div>
  <div class="job"><div class="time">08:30</div><div class="jobmain"><strong>Kantoor De Vries</strong><span>Keizersgracht 14 · Amsterdam</span><small>Lisa & Omar</small></div><button class="status done">Afgerond</button></div>
  <div class="job"><div class="time">10:30</div><div class="jobmain"><strong>Van Dijk Advocaten</strong><span>Stationsplein 6 · Utrecht</span><small>Lisa</small></div><button class="status busy">Bezig</button></div>
  <div class="job"><div class="time">13:00</div><div class="jobmain"><strong>Studio Nova</strong><span>Veemarkt 22 · Rotterdam</span><small>Omar</small></div><button class="status planned">Gepland</button></div>
</section>
<section class="grid"><div class="panel"><h3>Medewerkers</h3><div class="person"><span>L</span><div><strong>Lisa</strong><small>2 opdrachten</small></div></div><div class="person"><span>O</span><div><strong>Omar</strong><small>2 opdrachten</small></div></div></div><div class="panel"><h3>Snelle acties</h3><button class="action">Open routeplanning</button><button class="action">Nieuwe terugkerende opdracht</button></div></section>
"""
        js="document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('active'));b.classList.add('active')});"
    elif kind=="dierenarts-app":
        body="""
<section class="topbar"><div><span class="eyebrow">Dierenarts</span><h1>Agenda vandaag</h1><p>6 afspraken · 2 vaccinaties</p></div><button class="primary">+ Afspraak</button></section>
<section class="panel"><div class="appt"><div class="time">09:00</div><div><strong>Luna · Labrador</strong><span>Eigenaar: M. de Boer</span><small>Jaarcontrole + vaccinatie</small></div><button class="pill">Dossier</button></div><div class="appt"><div class="time">09:45</div><div><strong>Milo · Europese korthaar</strong><span>Eigenaar: S. Jansen</span><small>Controle wond</small></div><button class="pill">Dossier</button></div></section>
<section class="grid"><div class="panel"><h3>Herinneringen</h3><p>3 vaccinaties verlopen deze maand.</p><button class="action">Bekijk herinneringen</button></div><div class="panel"><h3>Nieuwe patiënt</h3><p>Registreer eigenaar en dier in één flow.</p><button class="action">Toevoegen</button></div></section>
"""
        js=""
    elif kind=="game":
        body="""
<section class="gamewrap"><span class="eyebrow">Reactiespel</span><h1>Hoe snel ben jij?</h1><p id="msg">Druk op start en wacht op groen.</p><div class="scoreline"><span>Beste tijd</span><strong id="best">—</strong></div><button id="reaction" class="reaction">START</button></section>
"""
        js="""const b=document.getElementById('reaction'),m=document.getElementById('msg'),bestEl=document.getElementById('best');let ready=false,start=0,best=Number(localStorage.getItem('v7best')||0);if(best)bestEl.textContent=best+' ms';b.onclick=()=>{if(ready){const t=Math.round(performance.now()-start);ready=false;b.className='reaction';b.textContent='NOG EEN KEER';m.textContent=t+' ms';if(!best||t<best){best=t;localStorage.setItem('v7best',best);bestEl.textContent=best+' ms'}return}b.className='reaction wait';b.textContent='WACHT...';m.textContent='Niet te vroeg';setTimeout(()=>{ready=true;start=performance.now();b.className='reaction go';b.textContent='NU!';m.textContent='Klik!'},1000+Math.random()*2500)};"""
    elif kind=="voorraad-app":
        body="""
<section class="topbar"><div><span class="eyebrow">Voorraad</span><h1>Magazijn</h1><p>24 producten · 3 onder minimum</p></div><button class="primary">Scan barcode</button></section>
<section class="stats"><div><span>Producten</span><strong>24</strong></div><div class="warn"><span>Bijbestellen</span><strong>3</strong></div><div><span>Vandaag gewijzigd</span><strong>8</strong></div></section>
<section class="panel"><input id="search" class="search" placeholder="Zoek product..."><div id="products"></div></section>
"""
        js="""let data=[['Kit wit',18,5],['Roller 10 cm',6,8],['Afplaktape',22,10],['Schuurspons',3,5]];function render(){products.innerHTML='';data.filter(p=>p[0].toLowerCase().includes(search.value.toLowerCase())).forEach(p=>{const d=document.createElement('div');d.className='product';d.innerHTML=`<div><strong>${p[0]}</strong><small>${p[1]<=p[2]?'Onder minimum':'Op voorraad'}</small></div><div class="counter"><button data-d="-1">−</button><b>${p[1]}</b><button data-d="1">+</button></div>`;d.querySelectorAll('button').forEach(b=>b.onclick=()=>{p[1]=Math.max(0,p[1]+Number(b.dataset.d));render()});products.appendChild(d)})}search.oninput=render;render();"""
    elif kind=="offertegenerator":
        body="""
<section class="topbar"><div><span class="eyebrow">Nieuwe offerte</span><h1>Offerte opstellen</h1><p>Voeg regels toe en laat totalen automatisch berekenen.</p></div><button id="printBtn" class="primary">Print / PDF</button></section>
<section class="grid"><div class="panel"><h3>Klant</h3><label>Naam<input placeholder="Klantnaam"></label><label>Adres<input placeholder="Adres"></label></div><div class="panel"><h3>Details</h3><label>Offertenummer<input value="OFF-2026-001"></label><label>Datum<input id="date" type="date"></label></div></section>
<section class="panel"><div class="sectionhead"><h2>Regels</h2><button id="addRow" class="action">+ Regel</button></div><div id="rows"></div><div class="totals"><div><span>Subtotaal</span><strong id="sub">€ 0,00</strong></div><div><span>BTW</span><strong id="vat">€ 0,00</strong></div><div class="grand"><span>Totaal</span><strong id="total">€ 0,00</strong></div></div></section>
"""
        js="""const rows=document.getElementById('rows');function euro(n){return new Intl.NumberFormat('nl-NL',{style:'currency',currency:'EUR'}).format(n||0)}function calc(){let s=0,v=0;document.querySelectorAll('.quote').forEach(r=>{let q=+r.querySelector('.q').value||0,p=+r.querySelector('.p').value||0,b=+r.querySelector('.b').value||0;s+=q*p;v+=q*p*b/100});sub.textContent=euro(s);vat.textContent=euro(v);total.textContent=euro(s+v)}function add(){let r=document.createElement('div');r.className='quote';r.innerHTML=`<input placeholder="Omschrijving"><input class="q" type="number" value="1"><input class="p" type="number" step=".01" placeholder="Prijs"><select class="b"><option>21</option><option>9</option><option>0</option></select><button>×</button>`;r.querySelectorAll('input,select').forEach(x=>x.oninput=calc);r.querySelector('button').onclick=()=>{r.remove();calc()};rows.appendChild(r);calc()}add();add();addRow.onclick=add;printBtn.onclick=()=>window.print();date.valueAsDate=new Date();"""
    else:
        body="""
<section class="topbar"><div><span class="eyebrow">Maatwerk</span><h1>Dashboard</h1><p>De structuur is klaar om verder uit te bouwen.</p></div><button class="primary">+ Nieuw</button></section>
<section class="grid"><div class="panel"><h3>Vandaag</h3><strong class="metric">12</strong></div><div class="panel"><h3>Open</h3><strong class="metric">4</strong></div></section>
"""
        js=""

    html=f"""<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><link rel="stylesheet" href="/static/app.css"><link rel="manifest" href="/static/manifest.json"><title>{title}</title></head><body><header><div class="brand">A</div><div><strong>{title}</strong><small>{kind}</small></div></header><main>{body}</main><script src="/static/app.js"></script></body></html>"""
    css="""*{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:#142235;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}header{height:70px;background:#102a43;color:#fff;padding:0 22px;display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:20}.brand{width:42px;height:42px;border-radius:13px;background:linear-gradient(135deg,#7c3aed,#2563eb);display:grid;place-items:center;font-weight:900}header strong{display:block}header small{display:block;opacity:.65}main{max-width:1100px;margin:auto;padding:28px 18px 90px}.topbar{background:linear-gradient(135deg,#102a43,#1e3a5f);color:#fff;border-radius:27px;padding:30px;display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:18px}.topbar h1,.gamewrap h1{font-size:38px;margin:7px 0}.topbar p{margin:0;color:#d6e0ea}.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:11px;font-weight:900;color:#93c5fd}.primary,.action,.pill,.tabs button,.counter button,.quote button{border:0;border-radius:12px;font-weight:850;cursor:pointer}.primary{background:#2563eb;color:#fff;padding:13px 17px}.panel,.stats>div{background:#fff;border:1px solid #e2e9f0;border-radius:21px;box-shadow:0 10px 32px #12203310}.panel{padding:20px;margin-bottom:16px}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px}.stats>div{padding:18px}.stats span{display:block;color:#66778a}.stats strong{font-size:34px}.stats .warn strong{color:#dc2626}.sectionhead{display:flex;align-items:center;justify-content:space-between}.tabs{display:flex;gap:6px}.tabs button{padding:8px 11px;background:#eef3f7;color:#54677b}.tabs button.active{background:#102a43;color:#fff}.job,.appt,.product,.person{display:flex;align-items:center;gap:14px;padding:14px 0;border-bottom:1px solid #edf1f4}.time{font-weight:900;color:#2563eb;min-width:58px}.jobmain,.appt>div:nth-child(2){flex:1}.job strong,.appt strong,.product strong,.person strong{display:block}.job span,.appt span,.product small,.person small{display:block;color:#66778a;margin-top:3px}.status{padding:8px 10px;border:0;border-radius:999px;font-weight:800}.status.done{background:#dcfce7;color:#166534}.status.busy{background:#dbeafe;color:#1d4ed8}.status.planned{background:#f1f5f9;color:#475569}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.person span{width:38px;height:38px;border-radius:50%;background:#dbeafe;color:#1d4ed8;display:grid;place-items:center;font-weight:900}.action{background:#eef4ff;color:#1d4ed8;padding:10px 13px;margin:4px 5px 4px 0}.pill{background:#eef4ff;color:#1d4ed8;padding:8px 10px;margin-left:auto}label{display:block;font-size:13px;font-weight:800;margin-bottom:13px}input,textarea,select{width:100%;border:1px solid #d8e1ea;border-radius:12px;padding:12px;margin-top:6px;font:inherit}.search{margin:0 0 8px}.product{justify-content:space-between}.counter{display:flex;align-items:center;gap:10px}.counter button{width:38px;height:38px;background:#eef4ff;color:#1d4ed8;font-size:19px}.gamewrap{max-width:700px;margin:40px auto;text-align:center;background:#fff;border-radius:28px;padding:30px;box-shadow:0 15px 50px #00000014}.reaction{width:100%;min-height:300px;border:0;border-radius:24px;background:#2563eb;color:#fff;font-size:34px;font-weight:900;cursor:pointer}.reaction.wait{background:#f59e0b}.reaction.go{background:#16a34a}.scoreline{display:flex;justify-content:space-between;margin:20px 0;color:#64748b}.quote{display:grid;grid-template-columns:3fr .7fr 1fr .7fr 40px;gap:8px;margin-bottom:8px}.quote input,.quote select{margin:0}.quote button{background:#fff0f0;color:#b91c1c}.totals{max-width:360px;margin:22px 0 0 auto}.totals>div{display:flex;justify-content:space-between;padding:7px 0}.totals .grand{font-size:20px;border-top:1px solid #e5e7eb;margin-top:5px;padding-top:13px}.metric{font-size:40px}@media(max-width:720px){main{padding:16px 13px 70px}.topbar{padding:23px;align-items:flex-start}.topbar h1,.gamewrap h1{font-size:30px}.stats{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr}.quote{grid-template-columns:1fr 60px 85px 60px 36px}.job,.appt{align-items:flex-start}.status{margin-left:auto}}"""
    return GeneratedProject(
        plan=plan,
        files=[
            GeneratedFile(path="app/templates/index.html",content=html),
            GeneratedFile(path="app/static/app.css",content=css),
            GeneratedFile(path="app/static/app.js",content=js),
        ]
    )
