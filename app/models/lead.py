from typing import Optional
from dataclasses import dataclass

@dataclass
class Lead:
    place_id: str
    nome: Optional[str] = None
    bairro: Optional[str] = None
    whatsapp: Optional[str] = None
    link_maps: Optional[str] = None
    avaliacoes: Optional[int] = None
    nicho: Optional[str] = None
    score: Optional[float] = None
    dor: Optional[str] = None
    cta: Optional[str] = None
    mensagem_whats: Optional[str] = None
    status: Optional[str] = None
    data_criacao: Optional[str] = None
    data_atualizacao: Optional[str] = None
    obs: Optional[str] = None
