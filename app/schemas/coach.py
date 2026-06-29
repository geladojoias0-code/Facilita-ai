from pydantic import BaseModel
from typing import Optional

class CoachRequest(BaseModel):
    place_id: str
    pergunta: str

class PropostaRequest(BaseModel):
    place_id: str
    dados: dict

class BriefingRequest(BaseModel):
    place_id: str
    dados: dict
