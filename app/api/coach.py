from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_api_key
from app.schemas.coach import CoachRequest, PropostaRequest, BriefingRequest
from app.services.coach_service import CoachService
from app.services.proposta_service import PropostaService
from app.services.briefing_service import BriefingService

router = APIRouter(prefix="", tags=["coach"], dependencies=[Depends(get_api_key)])
coach_service = CoachService()
proposta_service = PropostaService()
briefing_service = BriefingService()

@router.post("/coach")
def coach(req: CoachRequest):
    try:
        res = coach_service.gerar_abordagem(req.place_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/proposta")
def proposta(req: PropostaRequest):
    try:
        return proposta_service.criar_proposta(req.place_id, req.dados)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/briefing")
def briefing(req: BriefingRequest):
    try:
        return briefing_service.criar_briefing(req.place_id, req.dados)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
