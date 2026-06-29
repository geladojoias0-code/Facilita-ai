from dataclasses import dataclass
from typing import Optional

@dataclass
class Producao:
    place_id: str
    briefing: Optional[str]
    status: Optional[str]
    data_criacao: Optional[str]
    data_atualizacao: Optional[str]
