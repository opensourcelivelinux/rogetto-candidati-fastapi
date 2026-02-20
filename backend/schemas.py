from pydantic import BaseModel
from typing import Optional

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

        # --- Aggiungi questo per i Candidati ---

class CandidateBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    role: str
    experience_years: int

class CandidateCreate(CandidateBase):
    pass

class Candidate(CandidateBase):
    id: int

    class Config:
        from_attributes = True


