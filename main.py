from fastapi import FastAPI, HTTPException, Depends, Security, Request, Query
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from serpapi import GoogleSearch
from dotenv import load_dotenv
from cachetools import TTLCache
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from openai import OpenAI

import os
import json
import sqlite3
import random
import logging
import datetime


load_dotenv()

DB = os.getenv("DB_PATH", "crm_facilita.db")

API_KEY = os.getenv("MINHA_API_KEY")
SERP_KEY = os.getenv("SERPAPI_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

API_KEY_NAME = "X-API-Key"

if not API_KEY:
    raise RuntimeError("MINHA_API_KEY não configurada no .env.")

if not SERP_KEY:
    raise RuntimeError("SERPAPI_KEY não configurada no .env.")

if not OPENROUTER_KEY:
    raise RuntimeError("OPENROUTER_KEY não configurada no .env.")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

app = FastAPI(
    title="FACILITA AI CRM API",
    version="1.0.0",
    description="API de prospecção, abordagem, fechamento, proposta e produção da FACILITA WEB."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://facilitaweb.shop",
        "https://www.facilitaweb.shop",
        "https://api.facilitaweb.shop",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

client_ai = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY
)

cache_serp = TTLCache(maxsize=250, ttl=21600)
cache_ai = TTLCache(maxsize=400, ttl=86400)

LL_PADRAO = os.getenv("SERP_LL", "@-23.5505,-46.6333,20z")

NICHOS = [
    "barbearia",
    "salão de beleza",
    "clínica de estética",
    "restaurante",
    "pet shop",
    "estúdio de tatuagem",
    "clínica odontológica",
    "academia",
    "manicure",
    "spa",
    "fisioterapia"
]

STATUS = [
    "novo",
    "abordado",
    "respondeu",
    "interessado",
    "proposta",
    "reuniao",
    "fechado",
    "em_producao",
    "homologacao",
    "entregue",
    "perdido"
]


def agora():
    return datetime.datetime.now().isoformat()


def get_conn():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with get_conn() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            place_id TEXT PRIMARY KEY,
            nome TEXT,
            bairro TEXT,
            whatsapp TEXT,
            link_maps TEXT,
            avaliacoes TEXT,
            nicho TEXT,
            score INTEGER DEFAULT 0,
            dor TEXT,
            cta TEXT,
            mensagem_whats TEXT,
            status TEXT DEFAULT 'novo',
            data_criacao TEXT,
            data_atualizacao TEXT,
            obs TEXT
        )
        """)

        con.execute("""
        CREATE TABLE IF NOT EXISTS conversas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id TEXT,
            autor TEXT,
            texto TEXT,
            data_criacao TEXT
        )
        """)

        con.execute("""
        CREATE TABLE IF NOT EXISTS producao (
            place_id TEXT PRIMARY KEY,
            briefing TEXT,
            status TEXT DEFAULT 'aguardando_inicio',
            data_criacao TEXT,
            data_atualizacao TEXT
        )
        """)

        con.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)
        """)

        con.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score)
        """)

        con.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversas_place_id ON conversas(place_id)
        """)

        con.commit()


init_db()


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header

    raise HTTPException(status_code=403, detail="API Key inválida.")


class LeadOut(BaseModel):
    place_id: str
    nome: str
    bairro: str
    whatsapp: str
    link_maps: str
    avaliacoes: str
    nicho: str
    score: int
    status: str
    dor: str
    cta: str
    mensagem_whats: str


class StatusUpdate(BaseModel):
    status: str
    obs: str | None = None


class ConversaInput(BaseModel):
    place_id: str
    autor: str
    texto: str


class CoachInput(BaseModel):
    place_id: str | None = None
    conversa: str


class PropostaInput(BaseModel):
    place_id: str
    servico: str | None = "Sistema de agendamento"
    valor: str | None = "R$790 pagamento único"
    prazo: str | None = "até 7 dias"


class BriefingInput(BaseModel):
    place_id: str
    informacoes_cliente: str


class ProducaoStatusInput(BaseModel):
    status: str


def json_ia(prompt: str, cache_key: str | None = None, max_tokens: int = 900) -> dict:
    if cache_key and cache_key in cache_ai:
        return cache_ai[cache_key]

    try:
        res = client_ai.chat.completions.create(
            model=os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free"),
            messages=[
                {
                    "role": "system",
                    "content": "Você responde apenas JSON válido, sem markdown e sem texto fora do JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )

        content = res.choices[0].message.content or "{}"
        data = json.loads(content)

        if cache_key:
            cache_ai[cache_key] = data

        return data

    except Exception as e:
        logging.error(f"Erro IA: {e}")
        return {}


def buscar_no_serp(nicho: str, bairro: str | None, start: int):
    query = f"{nicho} {bairro}" if bairro else nicho
    cache_key = f"{query}_{start}_{LL_PADRAO}"

    if cache_key in cache_serp:
        return cache_serp[cache_key]

    params = {
        "engine": "google_maps",
        "q": query,
        "ll": LL_PADRAO,
        "type": "search",
        "num": "20",
        "start": start,
        "rating": "4.8",
        "api_key": SERP_KEY
    }

    data = GoogleSearch(params).get_dict()
    cache_serp[cache_key] = data
    return data


def filtro_valido(lugar: dict) -> bool:
    try:
        nota = float(lugar.get("rating", 0))
        reviews = int(lugar.get("reviews", 0))
        phone = lugar.get("phone")
        site = (lugar.get("website") or "").lower()

        bloqueados = [
            "booksy",
            "fresha",
            "ifood",
            "agenda",
            "reservar",
            "trinks",
            "getin",
            "ubereats",
            "anota.ai",
            "sympla",
            "doctoralia"
        ]

        if any(b in site for b in bloqueados):
            return False

        return nota >= 4.8 and 4 <= reviews <= 45 and bool(phone)

    except Exception:
        return False


def gerar_kit_vendas(nicho: str, nome: str, avaliacoes: str) -> dict:
    fallback_primeiro = (
        f"Oi, tudo bem?\n"
        f"Vi a {nome} e fiquei com uma dúvida rápida: como vocês organizam os agendamentos hoje?\n"
        f"Tenho um sistema de agenda por R$790, só paga depois de pronto. Responde 1 que eu te mostro."
    )

    prompt = f"""
Você é o vendedor especialista da FACILITA WEB.

Produto:
Sistema de agendamento para negócios locais.
Valor: R$790 pagamento único.
Sem mensalidade inicial.
Cliente só paga depois de pronto e aprovado.
Prazo: até 7 dias.

Lead:
Nome: {nome}
Nicho: {nicho}
Avaliações: {avaliacoes}
Situação provável: atende por WhatsApp ou telefone, sem agenda online clara.

Retorne somente JSON válido com esta estrutura:

{{
  "score": número de 0 a 100,
  "dor": "frase curta, direta e específica",
  "cta": "frase curta de chamada",
  "mensagem_whats": "primeira mensagem pronta com 3 linhas",
  "mensagens": {{
    "primeiro_contato": "...",
    "followup_24h": "...",
    "followup_72h": "...",
    "perguntou_preco": "...",
    "achou_caro": "...",
    "vou_pensar": "...",
    "falar_com_socio": "...",
    "sem_tempo": "...",
    "ja_tenho_sistema": "...",
    "interessado": "...",
    "fechamento": "..."
  }}
}}

Regras:
Mensagens curtas.
Português do Brasil.
Tom humano, direto e vendedor.
Sem emoji.
Sem travessão.
Não prometa resultado garantido.
Não seja agressivo demais.
"""

    data = json_ia(prompt, cache_key=f"kit_{nicho}_{nome}_{avaliacoes}", max_tokens=1200)

    mensagens = data.get("mensagens") or {}

    return {
        "score": int(data.get("score", 75)),
        "dor": data.get("dor") or "Você pode estar perdendo agendamentos quando ninguém responde.",
        "cta": data.get("cta") or "Quer ver como funciona?",
        "mensagem_whats": data.get("mensagem_whats") or mensagens.get("primeiro_contato") or fallback_primeiro,
        "mensagens": mensagens
    }


def salvar_lead(lugar: dict, nicho: str, kit: dict):
    with get_conn() as con:
        con.execute("""
        INSERT OR IGNORE INTO leads (
            place_id, nome, bairro, whatsapp, link_maps, avaliacoes,
            nicho, score, dor, cta, mensagem_whats,
            data_criacao, data_atualizacao
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            lugar["place_id"],
            lugar.get("title", ""),
            lugar.get("address", "SP").split(",")[0],
            lugar.get("phone", ""),
            lugar.get("link", ""),
            f"{lugar.get('rating', '')} ⭐ {lugar.get('reviews', '')}",
            nicho,
            kit["score"],
            kit["dor"],
            kit["cta"],
            kit["mensagem_whats"],
            agora(),
            agora()
        ))
        con.commit()


def get_lead(place_id: str) -> dict:
    with get_conn() as con:
        lead = con.execute(
            "SELECT * FROM leads WHERE place_id=?",
            (place_id,)
        ).fetchone()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado.")

    return dict(lead)


@app.get("/")
def root():
    return {
        "ok": True,
        "app": "FACILITA AI CRM API",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "app": "FACILITA AI CRM API",
        "version": "1.0.0",
        "domain": "api.facilitaweb.shop"
    }


@app.get("/lead", response_model=LeadOut, dependencies=[Depends(get_api_key)])
@limiter.limit("30/minute")
def buscar_proximo_lead(request: Request, bairro: str | None = None):
    for nicho in random.sample(NICHOS, len(NICHOS)):
        for start in [0, 20, 40, 60]:
            data = buscar_no_serp(nicho, bairro, start)

            for lugar in data.get("local_results", []):
                place_id = lugar.get("place_id")

                if not place_id:
                    continue

                with get_conn() as con:
                    existe = con.execute(
                        "SELECT 1 FROM leads WHERE place_id=?",
                        (place_id,)
                    ).fetchone()

                if existe:
                    continue

                if filtro_valido(lugar):
                    avaliacoes = f"{lugar.get('rating', '')} ⭐ {lugar.get('reviews', '')}"
                    kit = gerar_kit_vendas(
                        nicho=nicho,
                        nome=lugar.get("title", ""),
                        avaliacoes=avaliacoes
                    )

                    salvar_lead(lugar, nicho, kit)

                    return LeadOut(
                        place_id=place_id,
                        nome=lugar.get("title", ""),
                        bairro=lugar.get("address", "SP").split(",")[0],
                        whatsapp=lugar.get("phone", ""),
                        link_maps=lugar.get("link", ""),
                        avaliacoes=avaliacoes,
                        nicho=nicho,
                        score=kit["score"],
                        status="novo",
                        dor=kit["dor"],
                        cta=kit["cta"],
                        mensagem_whats=kit["mensagem_whats"]
                    )

    raise HTTPException(status_code=404, detail="Sem leads novos.")


@app.get("/leads", dependencies=[Depends(get_api_key)])
def listar_leads(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
):
    if status and status not in STATUS:
        raise HTTPException(status_code=400, detail=f"Status inválido. Use: {STATUS}")

    with get_conn() as con:
        if status:
            rows = con.execute("""
                SELECT * FROM leads
                WHERE status=?
                ORDER BY score DESC, data_criacao DESC
                LIMIT ? OFFSET ?
            """, (status, limit, offset)).fetchall()
        else:
            rows = con.execute("""
                SELECT * FROM leads
                ORDER BY score DESC, data_criacao DESC
                LIMIT ? OFFSET ?
            """, (limit, offset)).fetchall()

    return [dict(row) for row in rows]


@app.get("/lead/{place_id}", dependencies=[Depends(get_api_key)])
def detalhe_lead(place_id: str):
    return get_lead(place_id)


@app.get("/mensagens/{place_id}", dependencies=[Depends(get_api_key)])
def mensagens_prontas(place_id: str):
    lead = get_lead(place_id)

    kit = gerar_kit_vendas(
        nicho=lead["nicho"],
        nome=lead["nome"],
        avaliacoes=lead["avaliacoes"]
    )

    return {
        "lead": lead["nome"],
        "whatsapp": lead["whatsapp"],
        "score": kit["score"],
        "dor": kit["dor"],
        "cta": kit["cta"],
        "mensagem_principal": kit["mensagem_whats"],
        "mensagens": kit["mensagens"]
    }


@app.get("/abordagem/{place_id}", dependencies=[Depends(get_api_key)])
def abordagem(place_id: str):
    lead = get_lead(place_id)

    with get_conn() as con:
        con.execute("""
            UPDATE leads
            SET status='abordado', data_atualizacao=?
            WHERE place_id=?
        """, (agora(), place_id))
        con.commit()

    return {
        "nome": lead["nome"],
        "whatsapp": lead["whatsapp"],
        "mensagem_pronta": lead["mensagem_whats"],
        "proximo_passo": "Cole no WhatsApp. Se responder, salve em POST /conversa e use POST /coach."
    }


@app.post("/conversa", dependencies=[Depends(get_api_key)])
def salvar_conversa(body: ConversaInput):
    if body.autor not in ["eu", "cliente"]:
        raise HTTPException(status_code=400, detail="autor deve ser 'eu' ou 'cliente'.")

    get_lead(body.place_id)

    with get_conn() as con:
        con.execute("""
            INSERT INTO conversas (place_id, autor, texto, data_criacao)
            VALUES (?,?,?,?)
        """, (body.place_id, body.autor, body.texto, agora()))

        if body.autor == "cliente":
            con.execute("""
                UPDATE leads
                SET status='respondeu', data_atualizacao=?
                WHERE place_id=?
            """, (agora(), body.place_id))

        con.commit()

    return {"ok": True}


@app.get("/conversa/{place_id}", dependencies=[Depends(get_api_key)])
def listar_conversa(place_id: str):
    get_lead(place_id)

    with get_conn() as con:
        rows = con.execute("""
            SELECT autor, texto, data_criacao
            FROM conversas
            WHERE place_id=?
            ORDER BY id ASC
        """, (place_id,)).fetchall()

    return [dict(row) for row in rows]


@app.post("/coach", dependencies=[Depends(get_api_key)])
def coach(body: CoachInput):
    contexto_lead = ""

    if body.place_id:
        lead = get_lead(body.place_id)
        contexto_lead = f"""
Lead:
Nome: {lead['nome']}
Nicho: {lead['nicho']}
Avaliações: {lead['avaliacoes']}
Dor inicial: {lead['dor']}
Status: {lead['status']}
"""

    prompt = f"""
Você é o Modo Fechador da FACILITA WEB.

Produto:
Sistema de agendamento para negócios locais.
Valor: R$790 pagamento único.
Cliente só paga depois de pronto e aprovado.
Prazo: até 7 dias.

{contexto_lead}

Conversa:
{body.conversa}

Retorne somente JSON válido:

{{
  "fase": "...",
  "emocao_cliente": "...",
  "objecao": "...",
  "chance_fechamento": número de 0 a 100,
  "analise": "...",
  "nao_fale": "...",
  "proximo_objetivo": "...",
  "mensagem_pronta": "mensagem curta para mandar no WhatsApp"
}}

Regras:
Mensagem curta.
Humana.
Sem emoji.
Sem pressão exagerada.
Não ofereça desconto sem necessidade.
Sempre conduza para demonstração, proposta ou fechamento.
"""

    data = json_ia(prompt, max_tokens=900)

    return {
        "fase": data.get("fase", "negociação"),
        "emocao_cliente": data.get("emocao_cliente", "neutro"),
        "objecao": data.get("objecao", "não identificada"),
        "chance_fechamento": data.get("chance_fechamento", 50),
        "analise": data.get("analise", "Continue a conversa com uma pergunta simples."),
        "nao_fale": data.get("nao_fale", "Não envie desconto agora."),
        "proximo_objetivo": data.get("proximo_objetivo", "entender a necessidade"),
        "mensagem_pronta": data.get(
            "mensagem_pronta",
            "Entendi. Me conta uma coisa: hoje como vocês organizam os agendamentos quando ninguém consegue responder?"
        )
    }


@app.post("/proposta", dependencies=[Depends(get_api_key)])
def gerar_proposta(body: PropostaInput):
    lead = get_lead(body.place_id)

    prompt = f"""
Crie uma proposta comercial curta para WhatsApp.

Cliente:
{lead['nome']}

Nicho:
{lead['nicho']}

Serviço:
{body.servico}

Valor:
{body.valor}

Prazo:
{body.prazo}

Condição:
Cliente só paga depois que estiver pronto e aprovado.

Retorne somente JSON válido:
{{
  "proposta_whatsapp": "...",
  "resumo": "...",
  "mensagem_fechamento": "..."
}}

Sem emoji.
Sem markdown.
Tom vendedor e direto.
"""

    data = json_ia(prompt, max_tokens=900)

    with get_conn() as con:
        con.execute("""
            UPDATE leads
            SET status='proposta', data_atualizacao=?
            WHERE place_id=?
        """, (agora(), body.place_id))
        con.commit()

    return {
        "cliente": lead["nome"],
        "whatsapp": lead["whatsapp"],
        "proposta_whatsapp": data.get(
            "proposta_whatsapp",
            f"Proposta para {lead['nome']}:\nSistema de agendamento por {body.valor}.\nPrazo: {body.prazo}.\nVocê só paga depois que estiver pronto e aprovado."
        ),
        "resumo": data.get("resumo", ""),
        "mensagem_fechamento": data.get("mensagem_fechamento", "")
    }


@app.post("/briefing", dependencies=[Depends(get_api_key)])
def gerar_briefing(body: BriefingInput):
    lead = get_lead(body.place_id)

    prompt = f"""
Você é gerente de produção da FACILITA WEB.

Crie um briefing organizado para desenvolver um sistema de agendamento.

Cliente:
{lead['nome']}

Nicho:
{lead['nicho']}

Informações coletadas:
{body.informacoes_cliente}

Retorne somente JSON válido:

{{
  "briefing": "...",
  "checklist_cliente": ["..."],
  "checklist_producao": ["..."],
  "pendencias": ["..."],
  "primeira_tarefa": "..."
}}
"""

    data = json_ia(prompt, max_tokens=1200)

    briefing = data.get("briefing", body.informacoes_cliente)

    with get_conn() as con:
        con.execute("""
            INSERT OR REPLACE INTO producao (
                place_id, briefing, status, data_criacao, data_atualizacao
            )
            VALUES (?,?,?,?,?)
        """, (
            body.place_id,
            json.dumps(data, ensure_ascii=False),
        
