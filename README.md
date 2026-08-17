# AI App Studio V4

Dit is de eerste versie die niet meer alleen uit vaste formuliertemplates bestaat.

## Hoe werkt het?
1. Prompt invoeren.
2. AI maakt een product-/UX-plan.
3. AI genereert HTML, CSS en JavaScript.
4. Direct live preview.
5. Downloadbare FastAPI/Render ZIP.

## AI aansluiten
Kopieer `.env.example` naar je Render Environment Variables:

- `AI_API_KEY`
- `AI_BASE_URL`
- `AI_MODEL`

De backend verwacht een OpenAI-compatible `/chat/completions` endpoint.

Zonder API-key blijft de builder werken in fallback-modus. De fallback kan o.a. offertegeneratoren, games, voorraadapps en formulieren maken.

## Render
Upload deze map naar GitHub en maak er een bestaande Docker Web Service van.
