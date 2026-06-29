# FACILITA AI CRM API

API REST profissional para gerenciamento de leads e CRM integrada com IA.

## Stack

- **FastAPI** - Framework web de alta performance
- **SQLite** - Banco de dados local
- **Pydantic v2** - Validação de dados
- **OpenRouter** - Integração com IA
- **SerpApi** - Busca de leads no Google Maps
- **SlowAPI** - Rate limiting
- **Python 3.12**

## Instalação

### Pré-requisitos

- Python 3.12+
- pip

### Setup Local

```bash
# Clone o repositório
git clone https://github.com/geladojoias0-code/Facilita-ai.git
cd Facilita-ai

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt

# Crie arquivo .env
cp .env.example .env
```

## Rodando Localmente

```bash
# Desenvolvimento com reload
uvicorn main:app --reload

# Produção
uvicorn main:app --host 0.0.0.0 --port 8000
```

A API estará disponível em `http://localhost:8000`

## Swagger Documentation

Acesse em: `http://localhost:8000/docs`

## Setup Inicial

Ao iniciar a API pela primeira vez, chame o endpoint de setup:

```bash
curl -X POST http://localhost:8000/setup \
  -H "Content-Type: application/json" \
  -d '{}'
```

Isso criará as configurações iniciais no banco de dados.

## Autenticação

Todos os endpoints (exceto `/health` e `/setup` inicial) requerem:

```bash
X-API-Key: Tz1533$$@@
```

## Endpoints Principais

### Health Check
```bash
GET /health
```

### Leads
```bash
GET /lead                  # Próximo lead aleatório
GET /leads                 # Listar leads com filtros
GET /lead/{place_id}       # Detalhes do lead
POST /buscar-leads         # Buscar novos leads no Google Maps
GET /abordagem/{place_id}  # Marcar como abordado
PATCH /lead/{place_id}/status  # Atualizar status
```

### Conversas
```bash
GET /mensagens/{place_id}  # Gerar kit de mensagens com IA
POST /conversa             # Salvar mensagem
GET /conversa/{place_id}   # Listar conversa
POST /coach                # Analisar conversa com IA
```

### Propostas e Produção
```bash
POST /proposta             # Gerar proposta comercial
POST /briefing             # Criar briefing de produção
GET /producao/{place_id}   # Ver status de produção
PATCH /producao/{place_id} # Atualizar produção
```

### Dashboard e Config
```bash
GET /dashboard             # Métricas gerais
GET /configuracoes         # Listar todas as configurações
GET /configuracoes/{chave} # Uma configuração específica
POST /configuracoes        # Criar/atualizar configuração
PATCH /configuracoes/{chave}  # Atualizar configuração
DELETE /configuracoes/{chave} # Deletar configuração
```

## Conectar Painel Web Next.js

No painel, configure:

```javascript
const API_URL = 'http://localhost:8000'; // ou URL de produção
const API_KEY = 'Tz1533$$@@';

const headers = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY,
};

// Exemplo: buscar próximo lead
fetch(`${API_URL}/lead`, {
  method: 'GET',
  headers,
})
  .then(res => res.json())
  .then(data => console.log(data));
```

## Deploy no Render

### Passo 1: Push para GitHub
```bash
git add .
git commit -m "feat: FACILITA AI CRM API"
git push origin feature/api-rest-crm
```

### Passo 2: Conectar ao Render

1. Acesse https://render.com
2. Conecte sua conta GitHub
3. Clique em "New +" → "Web Service"
4. Selecione o repositório `Facilita-ai`
5. Configure:
   - **Name**: `facilita-api`
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free (ou pago)

### Passo 3: Variáveis de Ambiente

Adicione na configuração do Render:
```
DB_PATH=./facilita_ai.db
```

### Passo 4: Deploy

Clique em "Create Web Service" e aguarde o deploy.

A API estará disponível em: `https://facilita-api.onrender.com`

## Testes

```bash
# Rodar todos os testes
pytest

# Com verbose
pytest -v

# Coverage
pytest --cov=app tests/
```

## Estrutura do Projeto

```
Facilita-ai/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── cache.py
│   │   ├── logger.py
│   │   └── security.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── lead_repository.py
│   │   ├── conversa_repository.py
│   │   ├── producao_repository.py
│   │   └── config_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── lead_service.py
│   │   ├── conversa_service.py
│   │   ├── producao_service.py
│   │   ├── config_service.py
│   │   ├── serp_service.py
│   │   ├── ia_service.py
│   │   ├── coach_service.py
│   │   ├── proposta_service.py
│   │   ├── briefing_service.py
│   │   └── dashboard_service.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── lead.py
│   │   ├── conversa.py
│   │   ├── producao.py
│   │   ├── configuracao.py
│   │   ├── setup.py
│   │   ├── coach.py
│   │   ├── proposta.py
│   │   ├── briefing.py
│   │   └── dashboard.py
│   └── utils/
│       ├── __init__.py
│       └── validators.py
├── tests/
│   ├── __init__.py
│   ├── test_health.py
│   ├── test_setup.py
│   ├── test_auth.py
│   ├── test_leads.py
│   ├── test_conversa.py
│   ├── test_configuracoes.py
│   ├── test_dashboard.py
│   └── test_producao.py
├── main.py
├── requirements.txt
├── runtime.txt
├── render.yaml
├── .env.example
├── .gitignore
└── README.md
```

## Configurações Iniciais

A API cria automaticamente essas configurações no banco:

- `MINHA_API_KEY`: Chave de autenticação
- `SERPAPI_KEY`: Chave SerpApi para busca de leads
- `OPENROUTER_KEY`: Chave OpenRouter para IA
- `OPENROUTER_MODEL`: Modelo de IA (padrão: deepseek/deepseek-r1-0528:free)
- `SERP_LL`: Localização para busca (padrão: São Paulo, Brazil)
- `APP_NAME`: Nome da aplicação
- `APP_VERSION`: Versão da API
- `EMPRESA`: Nome da empresa
- `ALLOWED_ORIGINS`: CORS origins permitidos

## Nichos Suportados

- Barbearia
- Salão de beleza
- Clínica de estética
- Restaurante
- Pet shop
- Estúdio de tatuagem
- Clínica odontológica
- Academia
- Manicure
- Spa
- Fisioterapia

## Status de Lead

- novo
- abordado
- respondeu
- interessado
- proposta
- reuniao
- fechado
- em_producao
- homologacao
- entregue
- perdido

## Produto

**Sistema de Agendamento**
- Preço: R$790
- Pagamento único
- Sem mensalidade
- Prazo máximo: 7 dias

## Suporte

Para dúvidas ou problemas, abra uma issue no repositório.