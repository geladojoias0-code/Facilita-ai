from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.lead import LeadCreate, LeadOut, LeadUpdateStatus
from app.core.auth import get_api_key
from app.services.lead_service import LeadService
from app.services.producao_service import IntegrationService
from app.core.config import settings

router = APIRouter(prefix="", tags=["leads"], dependencies=[Depends(get_api_key)])

lead_service = LeadService()
integration = IntegrationService()

@router.get("/lead/{place_id}")
def get_lead(place_id: str):
    l = lead_service.get_lead(place_id)
    if not l:
        raise HTTPException(status_code=404, detail="Lead not found")
    return l

@router.get("/leads")
def get_leads(limit: int = 100):
    return lead_service.list_leads(limit)

@router.get("/lead")
def find_lead(place_id: str):
    l = lead_service.get_lead(place_id)
    if not l:
        raise HTTPException(status_code=404, detail="Lead not found")
    return l

@router.post("/buscar-leads")
def buscar_leads(q: str = 'empresa'):
    count = integration.importar_leads(q)
    return {"importados": count}

@router.patch("/lead/{place_id}/status")
def update_status(place_id: str, payload: LeadUpdateStatus):
    lead_service.update_status(place_id, payload.status)
    return {"ok": True}
