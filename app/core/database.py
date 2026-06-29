import sqlite3
from sqlite3 import Connection
import logging

logger = logging.getLogger(__name__)

SCHEMA = [
    "CREATE TABLE IF NOT EXISTS leads(place_id TEXT PRIMARY KEY,nome TEXT,bairro TEXT,whatsapp TEXT,link_maps TEXT,avaliacoes INTEGER,nicho TEXT,score REAL,dor TEXT,cta TEXT,mensagem_whats TEXT,status TEXT,data_criacao TEXT,data_atualizacao TEXT,obs TEXT)",
    "CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)",
    "CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score)",
    "CREATE TABLE IF NOT EXISTS conversas(id INTEGER PRIMARY KEY AUTOINCREMENT,place_id TEXT,autor TEXT,texto TEXT,data_criacao TEXT)",
    "CREATE INDEX IF NOT EXISTS idx_conversas_place_id ON conversas(place_id)",
    "CREATE TABLE IF NOT EXISTS producao(place_id TEXT PRIMARY KEY,briefing TEXT,status TEXT,data_criacao TEXT,data_atualizacao TEXT)",
]


def get_conn(db_path: str) -> Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = "./facilita_ai.db"):
    conn = get_conn(db_path)
    cur = conn.cursor()
    for stmt in SCHEMA:
        cur.execute(stmt)
    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", db_path)
