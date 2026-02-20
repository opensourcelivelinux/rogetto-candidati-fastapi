from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# Importiamo i nostri moduli locali
import models, schemas, database

# Crea le tabelle nel database (se non esistono)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Funzione per ottenere la sessione del DB
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "Backend Online", "database": "Connesso"}

# Rotta per CREARE un candidato (POST)
@app.post("/candidates", response_model=schemas.Candidate, status_code=201)
def create_candidate(candidate: schemas.CandidateCreate, db: Session = Depends(get_db)):
    db_candidate = models.Candidate(**candidate.dict())
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

# Rotta per VEDERE tutti i candidati (GET)
@app.get("/candidates", response_model=List[schemas.Candidate])
def read_candidates(db: Session = Depends(get_db)):
    return db.query(models.Candidate).all()

# --- Rotta per CANCELLARE un candidato (DELETE) ---
@app.post("/candidates/{candidate_id}/delete") # Usiamo POST o DELETE, qui usiamo il metodo DELETE standard
@app.delete("/candidates/{candidate_id}", status_code=204)
def delete_candidate(candidate_id: int, db: Session = Depends(database.get_db)):
    db_candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not db_candidate:
        raise HTTPException(status_code=404, detail="Candidato non trovato")
    
    db.delete(db_candidate)
    db.commit()
    return None # Il codice 204 non restituisce contenuto

# --- Rotta per MODIFICARE un candidato (PUT) ---
@app.put("/candidates/{candidate_id}", response_model=schemas.Candidate)
def update_candidate(candidate_id: int, updated_data: schemas.CandidateCreate, db: Session = Depends(database.get_db)):
    db_query = db.query(models.Candidate).filter(models.Candidate.id == candidate_id)
    db_candidate = db_query.first()
    
    if not db_candidate:
        raise HTTPException(status_code=404, detail="Candidato non trovato")
    
    # Aggiorna i campi con i nuovi dati
    db_query.update(updated_data.dict(), synchronize_session=False)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

