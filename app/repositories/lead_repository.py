from app.core.database import get_conn
from typing import Optional, List, Dict
import sqlite3

DB = None

def _conn(db_path: str):
    return get_conn(db_path)

class LeadRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get(self, place_id: str) -> Optional[Dict]:
        conn = _conn(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM leads WHERE place_id = ?", (place_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def list(self, limit: int = 100) -> List[Dict]:
        conn = _conn(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM leads ORDER BY data_criacao DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def create_or_update(self, data: Dict):
        conn = _conn(self.db_path)
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO leads(place_id,nome,bairro,whatsapp,link_maps,avaliacoes,nicho,score,dor,cta,mensagem_whats,status,data_criacao,data_atualizacao,obs) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (data.get('place_id'),data.get('nome'),data.get('bairro'),data.get('whatsapp'),data.get('link_maps'),data.get('avaliacoes'),data.get('nicho'),data.get('score'),data.get('dor'),data.get('cta'),data.get('mensagem_whats'),data.get('status'),data.get('data_criacao'),data.get('data_atualizacao'),data.get('obs')))
        conn.commit()
        conn.close()

    def update_status(self, place_id: str, status: str):
        conn = _conn(self.db_path)
        cur = conn.cursor()
        cur.execute("UPDATE leads SET status = ?, data_atualizacao = datetime('now') WHERE place_id = ?", (status, place_id))
        conn.commit()
        conn.close()

    def count(self) -> int:
        conn = _conn(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) as c FROM leads")
        row = cur.fetchone()
        conn.close()
        return row['c'] if row else 0

    def pipeline_by_status(self) -> List[Dict]:
        conn = _conn(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT status, COUNT(1) as cnt FROM leads GROUP BY status")
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def count_closed(self) -> int:
        conn = _conn(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) as c FROM leads WHERE status = 'fechado'")
        row = cur.fetchone()
        conn.close()
        return row['c'] if row else 0

    def count_in_production(self) -> int:
        conn = _conn(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) as c FROM producao WHERE status = 'em_producao'")
        row = cur.fetchone()
        conn.close()
        return row['c'] if row else 0
