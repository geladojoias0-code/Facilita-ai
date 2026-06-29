from fastapi import APIRouter
from app.schemas.conversa import ConversaSchema
from app.services.lead_service import ConversaService

router = APIRouter(prefix="", tags=["conversas"])
conversa_service = ConversaService()

@router.post("/conversa")
def post_conversa(payload: ConversaSchema):
    conversa_service.add_message(payload.place_id, payload.autor, payload.texto)
    return {"ok": True}

@router.get("/conversa/{place_id}")
def get_conversa(place_id: str):
    return conversa_service.get_messages(place_id)

@router.get("/mensagens/{place_id}")
def mensagens(place_id: str):
    return conversa_service.get_messages(place_id)
