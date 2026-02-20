from pydantic import BaseModel
from typing import Optional

class CandidateBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    role: str
    experience_years: int
    # Fondamentale: usa Optional per permettere a FastAPI di leggere i dati
    level: Optional[str] = None 
    skills: Optional[str] = None
    cv_path: Optional[str] = None

class CandidateCreate(CandidateBase):
    pass

class Candidate(CandidateBase):
    id: int # L'ID deve esserci per vederlo nella lista

    class Config:
        from_attributes = True # <--- Questa riga dice a Pydantic di leggere i dati dal DB
