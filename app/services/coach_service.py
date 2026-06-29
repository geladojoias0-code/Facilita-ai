from app.services.lead_service import lead_repo, LeadService
from app.services.ia_service import IAService
from app.utils.prompts import PROMPT_LEAD_ABORDAGEM

lead_service = LeadService()
ia = IAService()

class CoachService:
    def gerar_abordagem(self, place_id: str):
        lead = lead_service.get_lead(place_id)
        if not lead:
            raise ValueError('Lead não encontrado')
        prompt = PROMPT_LEAD_ABORDAGEM + f"\nDados: {lead}"
        res = ia.chat(prompt)
        return res
