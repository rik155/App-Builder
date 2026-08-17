# AI App Studio V7 — Software Architect

Belangrijkste wijzigingen:
- interne discovery-context wordt nooit meer in de gebouwde UI gezet;
- codegenerator krijgt alleen een schoon bouwplan;
- architectuurcheck vóór het bouwen:
  1. branche
  2. gebruikers
  3. workflow
  4. schermen
  5. data
  6. integraties
  7. visuele stijl
- domeinspecifieke fallback-schermen voor planning, dierenarts, games, voorraad en offertes;
- live preview + ZIP;
- met AI_API_KEY wordt discovery/planning/codegeneratie door een OpenAI-compatible model uitgevoerd.

Environment:
AI_API_KEY=
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-5-mini
