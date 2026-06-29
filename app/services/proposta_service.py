from app.services.lead_service import LeadService
from app.services.ia_service import IAService

lead_service = LeadService()
ia = IAService()

class PropostaService:
    def criar_proposta(self, place_id: str, dados: dict):
        lead = lead_service.get_lead(place_id)
        if not lead:
            raise ValueError('Lead não encontrado')
        prompt = f"Crie uma proposta curta em português como JSON: {dados}"
        res = ia.chat(prompt)
        return res
