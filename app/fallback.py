
from .schemas import (
    BuildPlan, PageSpec, FeatureSpec, GeneratedProject, GeneratedFile,
    DiscoveryResult, ClarifyingQuestion, ContextProfile
)

def _q(id, question, why="", type="text", options=None, recommended=None):
    return ClarifyingQuestion(
        id=id, question=question, why=why, type=type,
        options=options or [], recommended_answer=recommended
    )

def fallback_discovery(app_name: str, prompt: str) -> DiscoveryResult:
    p = prompt.lower()
    questions, features, assumptions = [], [], []
    industry = ""
    target_users = []
    core_goal = ""
    workflow = []
    objects = []
    integrations = []
    risks = []

    # Industry/context detection
    if any(x in p for x in ["schoonmaak", "cleaning"]):
        industry = "schoonmaakbedrijf"
        target_users = ["planner/kantoor", "schoonmaakmedewerkers"]
        core_goal = "opdrachten plannen en uitvoer eenvoudig registreren"
        workflow = ["opdracht aanmaken", "medewerker inplannen", "naar locatie", "werk uitvoeren", "opleveren"]
        objects = ["klanten", "opdrachten", "medewerkers", "locaties", "foto's", "uren"]
        integrations = ["navigatie/kaarten", "e-mail"]
        features = [
            FeatureSpec(name="Dag- en weekplanning", description="Opdrachten per medewerker plannen"),
            FeatureSpec(name="Opdrachtstatus", description="Gepland, onderweg, bezig, afgerond"),
            FeatureSpec(name="Foto's voor/na", description="Uitvoering vastleggen"),
            FeatureSpec(name="Klantondertekening", description="Oplevering bevestigen"),
        ]
        questions = [
            _q("recurring", "Hebben jullie terugkerende schoonmaakopdrachten die automatisch opnieuw gepland moeten worden?", "Veel schoonmaakbedrijven werken met vaste wekelijkse of maandelijkse bezoeken.", "boolean", recommended="Ja"),
            _q("planning_view", "Welke planning is het belangrijkst voor kantoor?", "Dit bepaalt het hoofdscherm voor planners.", "choice", ["Dagplanning","Weekplanning","Beide"], "Beide"),
            _q("travel", "Moet de app reistijd of route tussen adressen helpen plannen?", "Handig bij meerdere opdrachten op één dag.", "boolean", recommended="Ja"),
            _q("completion", "Wat moet een medewerker bij afronding vastleggen?", "Zo blijft de mobiele flow kort maar compleet.", "choice", ["Alleen status","Status + foto's","Status + foto's + handtekening"], "Status + foto's + handtekening"),
            _q("customer_notice", "Moet de klant automatisch bericht krijgen wanneer de opdracht is afgerond?", "Dit kan telefoontjes naar kantoor verminderen.", "boolean", recommended="Nee"),
        ]
    elif any(x in p for x in ["dierenarts", "veterinary", "dierenkliniek"]):
        industry = "dierenartspraktijk"
        target_users = ["balie", "dierenarts", "assistente"]
        core_goal = "afspraken en dierdossiers beheren"
        workflow = ["eigenaar registreren", "dier registreren", "afspraak plannen", "consult", "behandeling vastleggen", "herinnering"]
        objects = ["eigenaren", "dieren", "afspraken", "consulten", "vaccinaties", "medicatie"]
        integrations = ["e-mail/SMS herinneringen"]
        risks = ["privacygevoelige dossierinformatie"]
        features = [
            FeatureSpec(name="Dierdossier", description="Historie per dier"),
            FeatureSpec(name="Afspraken", description="Agenda voor consulten"),
            FeatureSpec(name="Vaccinatieherinneringen", description="Automatische opvolging"),
        ]
        questions = [
            _q("multi_pet", "Moet één eigenaar meerdere dieren kunnen hebben?", "Dit is meestal nodig in een dierenartsdossier.", "boolean", recommended="Ja"),
            _q("online_booking", "Mogen klanten zelf online afspraken aanvragen of boeken?", "Dit verandert de planning en toegangsrechten.", "boolean", recommended="Ja"),
            _q("medical", "Welke medische informatie moet minimaal in het dossier staan?", "Dit bepaalt het dossierontwerp.", "choice", ["Consultnotities","Consultnotities + medicatie","Consultnotities + medicatie + vaccinaties"], "Consultnotities + medicatie + vaccinaties"),
            _q("reminders", "Wil je automatische herinneringen voor afspraken of vaccinaties?", "Dit is een veelgebruikte functie in dierenartssoftware.", "choice", ["Alleen afspraken","Alleen vaccinaties","Beide","Geen"], "Beide"),
        ]
    elif any(x in p for x in ["bouw", "aannemer", "schilder", "glas", "monteur", "werkbon", "servicebedrijf"]):
        industry = "service-/bouwbedrijf"
        target_users = ["medewerkers buiten", "kantoor/planning"]
        core_goal = "werkzaamheden snel registreren en kantoor automatisch informeren"
        workflow = ["opdracht ontvangen", "naar locatie", "werk uitvoeren", "materialen/uren registreren", "klant akkoord", "exporteren"]
        objects = ["klanten", "opdrachten", "medewerkers", "materialen", "uren", "foto's"]
        integrations = ["Excel", "e-mail"]
        features = [
            FeatureSpec(name="Snelle mobiele invoer", description="Zo weinig mogelijk tikken op locatie"),
            FeatureSpec(name="Foto's", description="Situatie voor/na vastleggen"),
            FeatureSpec(name="Handtekening", description="Akkoord opdrachtgever"),
            FeatureSpec(name="Excel-export", description="Kantoor krijgt een direct bruikbaar overzicht"),
        ]
        questions = [
            _q("speed", "Moet de app vooral extreem snel zijn voor spoedklussen, of mag er iets meer detail in?", "Dit bepaalt hoeveel velden op het hoofdscherm staan.", "choice", ["Zo snel mogelijk","Balans tussen snel en compleet","Veel detail"], "Zo snel mogelijk"),
            _q("photos", "Wil je foto's voor, na of beide kunnen toevoegen?", "Handig voor bewijs en oplevering.", "choice", ["Voor","Na","Beide","Geen"], "Beide"),
            _q("signature", "Moet de opdrachtgever digitaal tekenen?", "Dan kan de werkbon direct worden afgerond.", "boolean", recommended="Ja"),
            _q("export", "Wat moet kantoor ontvangen na afronding?", "Dit bepaalt de exportflow.", "choice", ["Excel","PDF","Excel + PDF","E-mail zonder bijlage"], "Excel + PDF"),
        ]
    elif any(x in p for x in ["offerte", "quote", "quotation"]):
        industry = "algemeen bedrijf"
        target_users = ["kantoor/verkoop"]
        core_goal = "snel professionele offertes maken en versturen"
        workflow = ["klant kiezen", "regels toevoegen", "prijzen/btw berekenen", "controleren", "versturen"]
        objects = ["klanten", "offertes", "offerte-regels", "prijzen", "btw"]
        integrations = ["PDF", "e-mail"]
        features = [
            FeatureSpec(name="Meerdere offertregels", description="Aantal, omschrijving, prijs en btw"),
            FeatureSpec(name="Automatische totalen", description="Subtotaal, btw en eindtotaal"),
            FeatureSpec(name="PDF", description="Professionele offerte exporteren"),
        ]
        questions = [
            _q("customer_db", "Wil je klanten kunnen opslaan en later opnieuw kiezen?", "Dat bespaart tijd bij terugkerende klanten.", "boolean", recommended="Ja"),
            _q("approval", "Moet een klant de offerte digitaal kunnen accepteren?", "Dit maakt opvolging makkelijker.", "boolean", recommended="Ja"),
            _q("vat", "Welke btw-tarieven moeten beschikbaar zijn?", "Voor correcte berekening.", "choice", ["21%","9% en 21%","0%, 9% en 21%"], "0%, 9% en 21%"),
            _q("mail", "Wil je offertes direct uit de app mailen?", "Dan hoeft kantoor niets te downloaden en opnieuw bij te voegen.", "boolean", recommended="Ja"),
        ]
    elif any(x in p for x in ["game", "spel", "quiz", "memory", "reactie", "clicker"]):
        industry = "entertainment / game"
        target_users = ["spelers"]
        core_goal = "een leuk en direct speelbaar spel maken"
        workflow = ["start", "spelen", "score/tijd meten", "resultaat", "opnieuw"]
        objects = ["spelronde", "score", "highscore"]
        features = [
            FeatureSpec(name="Highscore", description="Beste resultaat bewaren"),
            FeatureSpec(name="Mobiele feedback", description="Geluid en/of trilling"),
            FeatureSpec(name="Opnieuw spelen", description="Direct een nieuwe ronde"),
        ]
        questions = [
            _q("scoring", "Hoe wil je winnen of scoren?", "Dit bepaalt de spelregels.", "choice", ["Punten","Snelste tijd","Langste reeks","Levels"], "Snelste tijd"),
            _q("difficulty", "Moet het spel steeds moeilijker worden?", "Geeft meer uitdaging en herspeelbaarheid.", "boolean", recommended="Ja"),
            _q("feedback", "Wil je geluid, trilling of allebei?", "Dit maakt mobiele games duidelijker.", "choice", ["Geluid","Trilling","Beide","Geen"], "Beide"),
            _q("players", "Is het voor één speler of moeten meerdere spelers om de beurt kunnen spelen?", "Dit verandert score-opslag en schermflow.", "choice", ["1 speler","2 spelers lokaal","Meerdere spelers"], "1 speler"),
        ]
    else:
        industry = "onbekend / maatwerk"
        target_users = ["nog te bepalen"]
        core_goal = "het beschreven proces digitaliseren"
        workflow = ["start", "hoofdactie", "resultaat"]
        objects = ["gegevens"]
        features = [
            FeatureSpec(name="Mobiel ontwerp", description="Goed bruikbaar op telefoon"),
            FeatureSpec(name="Opslag", description="Gegevens of voortgang bewaren indien nodig"),
        ]
        questions = [
            _q("users", "Wie gaat deze app dagelijks gebruiken?", "Dit bepaalt hoe eenvoudig of uitgebreid de bediening moet zijn.", "text", recommended="Medewerkers"),
            _q("main_job", "Wat is de belangrijkste handeling die iemand in de app moet kunnen doen?", "Dit hoort centraal op het hoofdscherm te staan.", "text"),
            _q("data", "Moet de app gegevens bewaren voor later?", "Dan is een database of lokale opslag nodig.", "boolean", recommended="Ja"),
            _q("device", "Waar wordt de app vooral gebruikt?", "Dit bepaalt het ontwerp.", "choice", ["Telefoon","Desktop/laptop","Beide"], "Beide"),
        ]

    # Only ask style if genuinely not stated.
    if not any(x in p for x in ["donker", "dark", "licht", "clean", "professioneel", "modern", "minimalistisch", "speels", "rood", "groen", "blauw"]):
        questions.append(_q("style", "Welke uitstraling past het best?", "De app kan daarop worden vormgegeven.", "choice", ["Clean en professioneel","Donker en modern","Licht en minimalistisch","Kleurrijk en speels"], "Clean en professioneel"))

    context = ContextProfile(
        industry=industry,
        target_users=target_users,
        core_goal=core_goal,
        core_workflow=workflow,
        important_objects=objects,
        possible_integrations=integrations,
        risks_or_constraints=risks,
    )
    return DiscoveryResult(
        summary=f"Ik begrijp dit als een app voor {industry}. Het belangrijkste doel lijkt: {core_goal}. Ik stel alleen vragen over keuzes die echt invloed hebben op de app.",
        detected_app_type=industry,
        context=context,
        suggested_features=features,
        questions=questions[:6],
        assumptions=assumptions,
    )

# Keep build fallback generic but responsive to augmented prompt.
def fallback_plan(app_name: str, prompt: str) -> BuildPlan:
    p = prompt.lower()
    if "schoonmaak" in p:
        app_type="planning-app"
        pages=[
            PageSpec(name="Vandaag",route="/",purpose="Dagplanning en status"),
            PageSpec(name="Planning",route="/planning",purpose="Dag- en weekplanning"),
            PageSpec(name="Opdrachten",route="/opdrachten",purpose="Werkopdrachten beheren"),
            PageSpec(name="Medewerkers",route="/medewerkers",purpose="Beschikbaarheid en toewijzing"),
        ]
        features=[
            FeatureSpec(name="Statusworkflow",description="Gepland, onderweg, bezig, afgerond"),
            FeatureSpec(name="Foto's",description="Voor/na foto's"),
            FeatureSpec(name="Handtekening",description="Klant akkoord"),
        ]
        entities=["Klant","Opdracht","Medewerker","Foto","Planning"]
    elif "dierenarts" in p:
        app_type="dierenarts-app"
        pages=[PageSpec(name="Agenda",route="/",purpose="Afspraken"),PageSpec(name="Dieren",route="/dieren",purpose="Dierdossiers"),PageSpec(name="Eigenaren",route="/eigenaren",purpose="Eigenaren beheren")]
        features=[FeatureSpec(name="Dierdossier",description="Historie per dier"),FeatureSpec(name="Herinneringen",description="Afspraken/vaccinaties")]
        entities=["Eigenaar","Dier","Afspraak","Consult","Vaccinatie"]
    elif "game" in p or "spel" in p or "reactie" in p:
        app_type="game"
        pages=[PageSpec(name="Spel",route="/",purpose="Spelen")]
        features=[FeatureSpec(name="Score",description="Resultaat bijhouden"),FeatureSpec(name="Highscore",description="Beste resultaat bewaren")]
        entities=["GameSession"]
    elif "voorraad" in p or "barcode" in p:
        app_type="voorraad-app"
        pages=[PageSpec(name="Dashboard",route="/",purpose="Overzicht"),PageSpec(name="Producten",route="/producten",purpose="Producten")]
        features=[FeatureSpec(name="Scanner",description="Barcode scannen"),FeatureSpec(name="Minimumvoorraad",description="Lage voorraad")]
        entities=["Product","Mutatie"]
    else:
        app_type="maatwerk-app"
        pages=[PageSpec(name="Dashboard",route="/",purpose="Hoofdscherm"),PageSpec(name="Nieuw",route="/nieuw",purpose="Nieuwe invoer")]
        features=[FeatureSpec(name="Opslaan",description="Gegevens bewaren")]
        entities=["Record"]

    style="clean, modern, professional"
    colors="dark navy with bright accent"
    return BuildPlan(app_name=app_name,app_type=app_type,visual_style=style,color_direction=colors,pages=pages,features=features,data_entities=entities,notes=[])

def fallback_project(plan: BuildPlan, prompt: str) -> GeneratedProject:
    # Use a rich dashboard/list pattern instead of one universal form.
    title=plan.app_name
    cards="".join([f"<div class='feature'><strong>{f.name}</strong><span>{f.description}</span></div>" for f in plan.features])
    nav="".join([f"<button>{p.name}</button>" for p in plan.pages])
    html=f"""<!doctype html><html lang='nl'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1,viewport-fit=cover'><link rel='stylesheet' href='/static/app.css'><title>{title}</title></head><body><header><div class='logo'>A</div><div><strong>{title}</strong><small>{plan.app_type}</small></div></header><main><section class='hero'><span>Gebouwd uit context</span><h1>{title}</h1><p>{prompt}</p></section><section class='nav'>{nav}</section><section class='grid'>{cards}</section><section class='panel'><h2>Hoofdactie</h2><p>Deze fallback laat de structuur zien. Met een AI-key wordt de volledige interface vanuit de context gegenereerd.</p><button class='primary'>Start</button></section></main></body></html>"""
    css="""*{box-sizing:border-box}body{margin:0;background:#f4f7fb;color:#122033;font-family:Inter,system-ui,-apple-system,sans-serif}header{height:70px;background:#0f172a;color:white;padding:0 20px;display:flex;align-items:center;gap:12px}.logo{width:42px;height:42px;border-radius:13px;background:#2563eb;display:grid;place-items:center;font-weight:900}header strong{display:block}header small{opacity:.65}main{max-width:1050px;margin:auto;padding:26px 18px}.hero{background:linear-gradient(135deg,#0f172a,#1e3a5f);color:white;border-radius:26px;padding:30px}.hero h1{font-size:40px;margin:7px 0}.hero p{color:#d9e4f0}.nav{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}.nav button{border:0;background:white;padding:11px 14px;border-radius:12px;box-shadow:0 6px 20px #00000010}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.feature,.panel{background:white;border-radius:20px;padding:20px;box-shadow:0 10px 30px #00000010}.feature strong{display:block}.feature span{display:block;color:#65758a;margin-top:6px}.panel{margin-top:12px}.primary{border:0;border-radius:13px;background:#2563eb;color:white;padding:14px 18px;font-weight:850}@media(max-width:650px){.grid{grid-template-columns:1fr}.hero h1{font-size:31px}}"""
    return GeneratedProject(plan=plan,files=[GeneratedFile(path="app/templates/index.html",content=html),GeneratedFile(path="app/static/app.css",content=css),GeneratedFile(path="app/static/app.js",content="")])
