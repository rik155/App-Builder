# AI App Studio V5

V5 voegt een discovery-fase toe.

Flow:
1. Gebruiker beschrijft een app.
2. AI herkent het soort app.
3. AI stelt 2-6 gerichte vragen over functies die logisch bij dat type app passen.
4. Antwoorden worden meegenomen in het bouwplan.
5. AI genereert de app.
6. Live preview + ZIP.

Met `AI_API_KEY` gebruikt V5 een OpenAI-compatible model voor discovery, planning en codegeneratie.
Zonder key gebruikt hij de ingebouwde slimme fallback.

Environment:
- AI_API_KEY
- AI_BASE_URL=https://api.openai.com/v1
- AI_MODEL=gpt-5-mini
