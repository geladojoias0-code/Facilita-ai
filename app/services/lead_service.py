from app.repositories.lead_repository import LeadRepository
from app.repositories.conversa_repository import ConversaRepository
from app.repositories.producao_repository import ProducaoRepository
from app.core.config import settings
from typing import List, Dict, Optional
from datetime import datetime

lead_repo = LeadRepository(settings.DB_PATH)
conversa_repo = ConversaRepository(settings.DB_PATH)
producao_repo = ProducaoRepository(settings.DB_PATH)

class LeadService:
    def get_lead(self, place_id: str) -> Optional[Dict]:
        return lead_repo.get(place_id)

    def list_leads(self, limit: int = 100) -> List[Dict]:
        return lead_repo.list(limit)

    def create_or_update(self, data: Dict):
        data.setdefault('data_criacao', datetime.utcnow().isoformat())
        data['data_atualizacao'] = datetime.utcnow().isoformat()
        lead_repo.create_or_update(data)

    def update_status(self, place_id: str, status: str):
        lead_repo.update_status(place_id, status)

class ConversaService:
    def add_message(self, place_id: str, autor: str, texto: str):
        conversa_repo.create(place_id, autor, texto, datetime.utcnow().isoformat())

    def get_messages(self, place_id: str) -> List[Dict]:
        return conversa_repo.list_by_place(place_id)

class ProducaoService:
    def get(self, place_id: str) -> Optional[Dict]:
        return producao_repo.get(place_id)

    def create_or_update(self, place_id: str, briefing: str, status: str = 'pendente'):
        producao_repo.create_or_update(place_id, briefing, status)

    def update_status(self, place_id: str, status: str):
        producao_repo.update_status(place_id, status)

class DashboardService:
    def __init__(self):
        self.repo = lead_repo

    def stats(self):
        total = self.repo.count()
        pipeline = self.repo.pipeline_by_status()
        closed = self.repo.count_closed()
        in_prod = self.repo.count_in_production()
        rate = (closed / total * 100) if total else 0
        return {"total": total, "pipeline": pipeline, "fechados": closed, "taxa_fechamento": rate, "em_producao": in_prod}
