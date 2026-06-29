from pydantic import BaseModel
from typing import Optional, List

class ConversaSchema(BaseModel):
    place_id: str
    autor: str
    texto: str

class MensagemOut(BaseModel):
    id: int
    place_id: str
    autor: str
    texto: str
    data_criacao: str
