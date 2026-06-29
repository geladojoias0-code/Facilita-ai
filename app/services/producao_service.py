from app.services.serp_service import SerpService
from app.services.lead_service import LeadService, ConversaService, ProducaoService
from app.core.config import settings
from datetime import datetime

serp = SerpService()
lead_service = LeadService()
conversa_service = ConversaService()
producao_service = ProducaoService()

class IntegrationService:
    def importar_leads(self, query: str = 'empresa'):
        items = serp.buscar(query)
        for it in items:
            payload = {**it, 'status': 'novo', 'data_criacao': datetime.utcnow().isoformat(), 'data_atualizacao': datetime.utcnow().isoformat()}
            lead_service.create_or_update(payload)
        return len(items)
