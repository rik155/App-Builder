# AI App Studio V6 — Contextual Discovery

V6 analyseert niet alleen het app-type, maar probeert eerst het echte proces te begrijpen:

- branche / domein
- gebruikers
- hoofddoel
- workflow
- belangrijke objecten
- mogelijke integraties
- operationele beperkingen

Daarna stelt hij alleen vragen die voor dat specifieke proces relevant zijn.

Voorbeeld:
- schoonmaakplanning => terugkerende opdrachten, planning, routes, oplevering
- dierenarts => meerdere dieren per eigenaar, afspraken, dossier, vaccinatieherinneringen
- game => scoring, levels, multiplayer, geluid/trilling
- voorraad => scanner, mutaties, minimumvoorraad, export

Met `AI_API_KEY` worden discovery, planning en codegeneratie door een OpenAI-compatible model uitgevoerd.
Zonder key gebruikt V6 de uitgebreidere lokale fallback.
