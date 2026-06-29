from dataclasses import dataclass
from typing import Optional

@dataclass
class Conversa:
    id: int | None
    place_id: str
    autor: str
    texto: str
    data_criacao: str
