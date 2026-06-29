from app.core.database import get_conn
from typing import Optional, Dict

class ProducaoRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get(self, place_id: str) -> Optional[Dict]:
        conn = get_conn(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM producao WHERE place_id = ?", (place_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def create_or_update(self, place_id: str, briefing: str, status: str):
        conn = get_conn(self.db_path)
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO producao(place_id,briefing,status,data_criacao,data_atualizacao) VALUES(?,?,?,?,datetime('now'))", (place_id,briefing,status,datetime('now')))
        conn.commit()
        conn.close()

    def update_status(self, place_id: str, status: str):
        conn = get_conn(self.db_path)
        cur = conn.cursor()
        cur.execute("UPDATE producao SET status = ?, data_atualizacao = datetime('now') WHERE place_id = ?", (status, place_id))
        conn.commit()
        conn.close()
