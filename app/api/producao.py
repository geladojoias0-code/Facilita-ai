from fastapi import APIRouter, HTTPException
from app.services.producao_service import producao_service
from app.schemas.lead import ProducaoCreate

router = APIRouter(prefix="", tags=["producao"])

@router.get("/producao/{place_id}")
def get_producao(place_id: str):
    p = producao_service.get(place_id)
    if not p:
        raise HTTPException(status_code=404, detail="Producao not found")
    return p

@router.patch("/producao/{place_id}")
def patch_producao(place_id: str, status: str):
    producao_service.update_status(place_id, status)
    return {"ok": True}
