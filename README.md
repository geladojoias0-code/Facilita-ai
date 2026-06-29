# FACILITA AI CRM

Projeto FastAPI modular pronto para deploy no Render.com.

Instalação:

1. Copie `.env.example` para `.env` e preencha as chaves.
2. pip install -r requirements.txt
3. uvicorn main:app --reload

Endpoints principais:
- GET /health
- GET /lead, /leads, /lead/{place_id}
- GET /mensagens/{place_id}
- GET /abordagem/{place_id}
- POST /conversa
- GET /conversa/{place_id}
- POST /coach
- POST /proposta
- POST /briefing
- PATCH /lead/{place_id}/status
- GET /producao/{place_id}
- PATCH /producao/{place_id}
- GET /dashboard
- POST /buscar-leads

Autenticação: X-API-Key header (MINHA_API_KEY)
Rate limit: 30 req/min

Banco: SQLite (criado automaticamente)
