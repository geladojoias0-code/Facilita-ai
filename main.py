from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from serpapi import GoogleSearch
import openai
import json
from cachetools import TTLCache
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse

load_dotenv()
MINHA_API_KEY = os.getenv("MINHA_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
DB_PATH = os.getenv("DB_PATH", "crm_facilita.db")
SERP_LL = os.getenv("SERP_LL", "@-23.5505,-46.6333,20z")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-r1-0528:free")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openrouter.ai/v1")

openai.api_key = OPENROUTER_KEY
openai.api_base = OPENAI_API_BASE

app = FastAPI(title="FACILITA AI CRM")

origins = ["https://facilitaweb.shop", "http://facilitaweb.shop", "http://localhost:3000", "https://localhost:3000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

# Caches
serp_cache = TTLCache(maxsize=1000, ttl=21600)
ia_cache = TTLCache(maxsize=1000, ttl=86400)

# DB init
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS leads(place_id TEXT PRIMARY KEY, nome TEXT, bairro TEXT, whatsapp TEXT, link_maps TEXT, avaliacoes INTEGER, nicho TEXT, score REAL, dor TEXT, cta TEXT, mensagem_whats TEXT, status TEXT, data_criacao TEXT, data_atualizacao TEXT, obs TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS conversas(id INTEGER PRIMARY KEY AUTOINCREMENT, place_id TEXT, autor TEXT, texto TEXT, data_criacao TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS producao(place_id TEXT PRIMARY KEY, briefing TEXT, status TEXT, data_criacao TEXT, data_atualizacao TEXT)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_conversas_place_id ON conversas(place_id)")
conn.commit()

# Nichos and statuses
NICHOS = ["barbearia", "salão de beleza", "clínica de estética", "restaurante", "pet shop", "estúdio de tatuagem", "clínica odontológica", "academia", "manicure", "spa", "fisioterapia"]
VALID_STATUS = ["novo", "abordado", "respondeu", "interessado", "proposta", "reuniao", "fechado", "em_producao", "homologacao", "entregue", "perdido"]

# Helpers

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if MINHA_API_KEY is None:
        raise HTTPException(status_code=500, detail="Server missing MINHA_API_KEY")
    if x_api_key != MINHA_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")


def get_now_iso():
    return datetime.utcnow().isoformat()


def get_lead(place_id: str) -> Optional[Dict[str, Any]]:
    row = conn.execute("SELECT * FROM leads WHERE place_id = ?", (place_id,)).fetchone()
    return dict(row) if row else None


def salvar_lead(lead: Dict[str, Any]):
    now = get_now_iso()
    conn.execute("INSERT OR REPLACE INTO leads(place_id,nome,bairro,whatsapp,link_maps,avaliacoes,nicho,score,dor,cta,mensagem_whats,status,data_criacao,data_atualizacao,obs) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (lead.get("place_id"), lead.get("nome"), lead.get("bairro"), lead.get("whatsapp"), lead.get("link_maps"), lead.get("avaliacoes"), lead.get("nicho"), lead.get("score"), lead.get("dor"), lead.get("cta"), lead.get("mensagem_whats"), lead.get("status", "novo"), lead.get("data_criacao", now), lead.get("data_atualizacao", now), lead.get("obs")))
    conn.commit()


def filtro_valido(item: Dict[str, Any]) -> bool:
    try:
        rating = float(item.get("rating", 0))
    except Exception:
        rating = 0.0
    reviews = int(item.get("reviews", 0) or 0)
    phone = item.get("phone") or item.get("whatsapp")
    website = item.get("website", "") or ""
    if rating < 4.8:
        return False
    if reviews < 4 or reviews > 45:
        return False
    if not phone:
        return False
    blocked = ["agendamento", "booking", "reservas", "reservar", "agenda"]
    for b in blocked:
        if b in website.lower():
            return False
    return True


def buscar_no_serp(nicho: str, ll: str = SERP_LL) -> List[Dict[str, Any]]:
    key = f"serp::{nicho}::{ll}"
    if key in serp_cache:
        return serp_cache[key]
    params = {"engine": "google_maps", "q": nicho, "ll": ll}
    try:
        search = GoogleSearch(params, serpapi_api_key=SERPAPI_KEY)
        results = search.get_dict()
        places = results.get("local_results", {}).get("places", []) or results.get("places_results", []) or []
    except Exception:
        places = []
    filtered = []
    for p in places:
        item = {"place_id": p.get("place_id") or p.get("id"), "nome": p.get("title") or p.get("name"), "bairro": p.get("address") or p.get("snippet"), "whatsapp": p.get("phone"), "link_maps": p.get("gps_coordinates") or p.get("link"), "avaliacoes": p.get("reviews") or p.get("reviews_count") or p.get("review_count"), "rating": p.get("rating"), "website": p.get("website")}
        if filtro_valido(item):
            filtered.append(item)
            salvar_lead({"place_id": item.get("place_id"), "nome": item.get("nome"), "bairro": item.get("bairro"), "whatsapp": item.get("whatsapp"), "link_maps": item.get("link_maps"), "avaliacoes": item.get("avaliacoes"), "nicho": nicho, "score": None, "status": "novo", "obs": "importado_serp"})
    serp_cache[key] = filtered
    return filtered


def json_ia(system_prompt: str, user_prompt: str, model: str = OPENROUTER_MODEL) -> Dict[str, Any]:
    key = f"ia::{model}::{user_prompt}"
    if key in ia_cache:
        return ia_cache[key]
    try:
        response = openai.ChatCompletion.create(model=model, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.2, max_tokens=800)
        text = ""
        if isinstance(response, dict):
            choices = response.get("choices", [])
            if choices:
                text = choices[0].get("message", {}).get("content", "")
        else:
            text = getattr(response, "choices", [])[0].message["content"]
        try:
            data = json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    data = json.loads(text[start:end+1])
                except Exception:
                    data = {"text": text}
            else:
                data = {"text": text}
    except Exception as e:
        data = {"error": str(e)}
    ia_cache[key] = data
    return data


def gerar_kit_vendas(lead: Dict[str, Any]) -> Dict[str, Any]:
    system = "Você é um assistente de vendas que responde em JSON válido. Sempre retorne apenas JSON, sem markdown. Tom: humano, direto, vendedor. Sem emojis. Mensagens curtas em pt-BR. Não prometa resultado garantido."
    user = "Gere um JSON com as chaves: score (0-100), dor (frase curta), cta (frase curta), mensagens (lista de 3 mensagens curtas para WhatsApp). Dados do lead: nome:%s, bairro:%s, nicho:%s, avaliacoes:%s, telefone:%s. Preencha campos com base nos dados e considerando que o serviço custa R$790 pagamento único, sem mensalidade, prazos até 7 dias. Responda somente JSON." % (lead.get("nome"), lead.get("bairro"), lead.get("nicho"), lead.get("avaliacoes"), lead.get("whatsapp"))
    out = json_ia(system, user)
    return out

# Pydantic models
class ConversaIn(BaseModel):
    place_id: str
    autor: str
    texto: str

class CoachIn(BaseModel):
    place_id: str

class PropostaIn(BaseModel):
    place_id: str
    itens: Optional[List[str]] = None
    valor: Optional[float] = 790.0

class BriefingIn(BaseModel):
    place_id: str
    briefing: str

class StatusIn(BaseModel):
    status: str

# Endpoints
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/lead")
@limiter.limit("30/minute")
async def next_lead(x_api_key: Optional[str] = Depends(verify_api_key)):
    row = conn.execute("SELECT * FROM leads WHERE status = ? ORDER BY RANDOM() LIMIT 1", ("novo",)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No leads available")
    lead = dict(row)
    return lead

@app.get("/leads")
@limiter.limit("30/minute")
async def list_leads(status: Optional[str] = None, page: int = 1, page_size: int = 20, x_api_key: Optional[str] = Depends(verify_api_key)):
    offset = (page - 1) * page_size
    if status:
        rows = conn.execute("SELECT * FROM leads WHERE status = ? ORDER BY data_criacao DESC LIMIT ? OFFSET ?", (status, page_size, offset)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM leads ORDER BY data_criacao DESC LIMIT ? OFFSET ?", (page_size, offset)).fetchall()
    return [dict(r) for r in rows]

@app.get("/lead/{place_id}")
@limiter.limit("30/minute")
async def get_lead_endpoint(place_id: str, x_api_key: Optional[str] = Depends(verify_api_key)):
    lead = get_lead(place_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@app.get("/mensagens/{place_id}")
@limiter.limit("30/minute")
async def mensagens(place_id: str, x_api_key: Optional[str] = Depends(verify_api_key)):
    lead = get_lead(place_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    key = f"mensagens::{place_id}"
    if key in ia_cache:
        return ia_cache[key]
    kit = gerar_kit_vendas(lead)
    ia_cache[key] = kit
    return kit

@app.get("/abordagem/{place_id}")
@limiter.limit("30/minute")
async def abordagem(place_id: str, x_api_key: Optional[str] = Depends(verify_api_key)):
    if not get_lead(place_id):
        raise HTTPException(status_code=404, detail="Lead not found")
    now = get_now_iso()
    conn.execute("UPDATE leads SET status = ?, data_atualizacao = ? WHERE place_id = ?", ("abordado", now, place_id))
    conn.commit()
    return {"place_id": place_id, "status": "abordado"}

@app.post("/conversa")
@limiter.limit("30/minute")
async def save_conversa(payload: ConversaIn, x_api_key: Optional[str] = Depends(verify_api_key)):
    if not get_lead(payload.place_id):
        raise HTTPException(status_code=404, detail="Lead not found")
    now = get_now_iso()
    conn.execute("INSERT INTO conversas(place_id, autor, texto, data_criacao) VALUES(?,?,?,?)", (payload.place_id, payload.autor, payload.texto, now))
    conn.commit()
    return {"ok": True}

@app.get("/conversa/{place_id}")
@limiter.limit("30/minute")
async def list_conversa(place_id: str, x_api_key: Optional[str] = Depends(verify_api_key)):
    rows = conn.execute("SELECT * FROM conversas WHERE place_id = ? ORDER BY data_criacao ASC", (place_id,)).fetchall()
    return [dict(r) for r in rows]

@app.post("/coach")
@limiter.limit("30/minute")
async def coach(payload: CoachIn, x_api_key: Optional[str] = Depends(verify_api_key)):
    conv = conn.execute("SELECT * FROM conversas WHERE place_id = ? ORDER BY data_criacao ASC", (payload.place_id,)).fetchall()
    if not conv:
        raise HTTPException(status_code=404, detail="No conversation found")
    messages_text = "\n".join([f"{r['autor']}: {r['texto']}" for r in conv])
    system = "Você é um assistente de vendas que sugere a próxima mensagem curta em português brasileiro, tom humano e vendedor. Retorne JSON com chave 'mensagem' contendo a mensagem sugerida." 
    user = "Conversa:\n%s\nResponda com JSON válido sem markdown e sem emojis." % (messages_text)
    out = json_ia(system, user)
    return out

@app.post("/proposta")
@limiter.limit("30/minute")
async def proposta(payload: PropostaIn, x_api_key: Optional[str] = Depends(verify_api_key)):
    lead = get_lead(payload.place_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    system = "Você é um gerador de propostas comerciais. Retorne JSON válido com campos: titulo, itens (lista), valor, prazo (dias), condicoes (texto curto). Sem markdown." 
    itens_text = "\n".join(payload.itens or ["Criação do site", "Configuração do sistema", "Entrega final"]) 
    user = "Gere proposta para: nome:%s, nicho:%s. Itens:\n%s\nValor sugerido: R$%.2f. Prazo máximo: 7 dias. Responda apenas JSON." % (lead.get("nome"), lead.get("nicho"), itens_text, payload.valor or 790.0)
    out = json_ia(system, user)
    return out

@app.post("/briefing")
@limiter.limit("30/minute")
async def briefing(payload: BriefingIn, x_api_key: Optional[str] = Depends(verify_api_key)):
    now = get_now_iso()
    conn.execute("INSERT OR REPLACE INTO producao(place_id, briefing, status, data_criacao, data_atualizacao) VALUES(?,?,?,?,?)", (payload.place_id, payload.briefing, "em_producao", now, now))
    conn.commit()
    conn.execute("UPDATE leads SET status = ?, data_atualizacao = ? WHERE place_id = ?", ("em_producao", now, payload.place_id))
    conn.commit()
    return {"ok": True}

@app.patch("/lead/{place_id}/status")
@limiter.limit("30/minute")
async def update_status(place_id: str, payload: StatusIn, x_api_key: Optional[str] = Depends(verify_api_key)):
    if payload.status not in VALID_STATUS:
        raise HTTPException(status_code=400, detail="Invalid status")
    now = get_now_iso()
    conn.execute("UPDATE leads SET status = ?, data_atualizacao = ? WHERE place_id = ?", (payload.status, now, place_id))
    conn.commit()
    return {"place_id": place_id, "status": payload.status}

@app.get("/producao/{place_id}")
@limiter.limit("30/minute")
async def get_producao(place_id: str, x_api_key: Optional[str] = Depends(verify_api_key)):
    row = conn.execute("SELECT * FROM producao WHERE place_id = ?", (place_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Producao not found")
    return dict(row)

@app.patch("/producao/{place_id}")
@limiter.limit("30/minute")
async def patch_producao(place_id: str, payload: StatusIn, x_api_key: Optional[str] = Depends(verify_api_key)):
    now = get_now_iso()
    conn.execute("UPDATE producao SET status = ?, data_atualizacao = ? WHERE place_id = ?", (payload.status, now, place_id))
    conn.commit()
    return {"place_id": place_id, "status": payload.status}

@app.get("/dashboard")
@limiter.limit("30/minute")
async def dashboard(x_api_key: Optional[str] = Depends(verify_api_key)):
    rows = conn.execute("SELECT status, COUNT(*) as count FROM leads GROUP BY status").fetchall()
    data = {r["status"]: r["count"] for r in rows}
    fechado = data.get("fechado", 0)
    perdido = data.get("perdido", 0)
    total_decisao = fechado + perdido
    taxa_fechamento = (fechado / total_decisao) if total_decisao > 0 else None
    return {"pipeline": data, "taxa_fechamento": taxa_fechamento}

# Small endpoint to trigger serp fetch for a nicho
@app.post("/importar/{nicho}")
@limiter.limit("30/minute")
async def importar(nicho: str, x_api_key: Optional[str] = Depends(verify_api_key)):
    if nicho not in NICHOS:
        raise HTTPException(status_code=400, detail="Nicho inválido")
    items = buscar_no_serp(nicho)
    return {"importados": len(items)}
