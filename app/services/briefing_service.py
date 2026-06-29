from app.services.lead_service import LeadService
from app.services.ia_service import IAService

lead_service = LeadService()
ia = IAService()

class BriefingService:
    def criar_briefing(self, place_id: str, dados: dict):
        lead = lead_service.get_lead(place_id)
        if not lead:
            raise ValueError('Lead não encontrado')
        # business rule: generate briefing with IA
        prompt = f"Crie um briefing curto em português sem markdown como JSON: {dados}"
        res = ia.chat(prompt)
        return res
