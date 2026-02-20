from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="projects")

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String)
    experience_years = Column(Integer)
    
    # --- NUOVI CAMPI PER IL PARSER ---
    level = Column(String, default="Da analizzare") # Esempio: Junior, Mid, Senior
    skills = Column(Text) # Salveremo una stringa tipo "Python, SQL, Linux"
    cv_path = Column(String, nullable=True) # Il percorso del file in /static
