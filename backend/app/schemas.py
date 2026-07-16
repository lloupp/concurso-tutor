"""Schemas Pydantic (entrada/saída da API)."""
from pydantic import BaseModel
from typing import Optional, List


class LoginIn(BaseModel):
    username: str
    password: str


class ResponderIn(BaseModel):
    respostas: List[dict]  # [{"questao_id": int, "resposta": str, "tempo_seg": int}]
    tempo_total_seg: Optional[int] = None


class BlocoGerado(BaseModel):
    bloco: dict
    concurso_id: int


class GerarBlocoIn(BaseModel):
    concurso_id: int
    bloco: Optional[dict] = None
    n_topicos: Optional[int] = 2
