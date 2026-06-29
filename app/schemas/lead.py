from pydantic import BaseModel, Field
from typing import Optional, List

class LeadCreate(BaseModel):
    place_id: str
    nome: Optional[str]
    bairro: Optional[str]
    whatsapp: Optional[str]
    link_maps: Optional[str]
    avaliacoes: Optional[int]
    nicho: Optional[str]
    score: Optional[float]
    status: Optional[str]

class LeadUpdateStatus(BaseModel):
    status: str

class LeadOut(BaseModel):
    place_id: str
    nome: Optional[str]
    bairro: Optional[str]
    whatsapp: Optional[str]
    link_maps: Optional[str]
    avaliacoes: Optional[int]
    nicho: Optional[str]
    score: Optional[float]
    status: Optional[str]

class ConversaCreate(BaseModel):
    place_id: str
    autor: str
    texto: str

class ConversaOut(BaseModel):
    id: int
    place_id: str
    autor: str
    texto: str
    data_criacao: str

class ProducaoCreate(BaseModel):
    place_id: str
    briefing: Optional[str]

class ProducaoOut(BaseModel):
    place_id: str
    briefing: Optional[str]
    status: Optional[str]
    data_criacao: Optional[str]
    data_atualizacao: Optional[str]
