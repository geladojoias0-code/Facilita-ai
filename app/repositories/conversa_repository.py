from app.core.database import get_conn
from typing import List, Dict

class ConversaRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def create(self, place_id: str, autor: str, texto: str, data_criacao: str):
        conn = get_conn(self.db_path)
        cur = conn.cursor()
        cur.execute("INSERT INTO conversas(place_id,autor,texto,data_criacao) VALUES(?,?,?,?)", (place_id,autor,texto,data_criacao))
        conn.commit()
        conn.close()

    def list_by_place(self, place_id: str) -> List[Dict]:
        conn = get_conn(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM conversas WHERE place_id = ? ORDER BY data_criacao ASC", (place_id,))
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
