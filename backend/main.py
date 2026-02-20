from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import shutil  # <-- AGGIUNGI QUESTA RIGA QUI!
import os      # Utile anche questo per gestire i percorsi
import models, schemas, database

# 1. Crea le tabelle nel DB
models.Base.metadata.create_all(bind=database.engine)

# 2. DEFINISCI L'APP (Deve stare qui, prima delle rotte!)
app = FastAPI(title="Gestione Candidati API")

# 3. LE ROTTE (Usano 'app', quindi devono venire dopo)

@app.get("/")
def read_root():
    return {"status": "Online", "database": "Connesso con successo"}

@app.post("/candidates", response_model=schemas.Candidate, status_code=status.HTTP_201_CREATED)
def create_candidate(candidate: schemas.CandidateCreate, db: Session = Depends(database.get_db)):
    db_candidate = models.Candidate(**candidate.dict())
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

# 1. LEGGI TUTTI (Sostituisci quella vecchia con questa)
@app.get("/candidates", response_model=List[schemas.Candidate])
def read_candidates(
    role: str = None, 
    min_exp: int = 0, 
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Candidate)
    if role:
        query = query.filter(models.Candidate.role.ilike(f"%{role}%"))
    if min_exp > 0:
        query = query.filter(models.Candidate.experience_years >= min_exp)
    return query.all()

# 2. LEGGI SINGOLO (Questa rimane invariata, serve per l'ID specifico)
@app.get("/candidates/{candidate_id}", response_model=schemas.Candidate)
def read_candidate(candidate_id: int, db: Session = Depends(database.get_db)):
    db_candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not db_candidate:
        raise HTTPException(status_code=404, detail="Candidato non trovato")
    return db_candidate

@app.put("/candidates/{candidate_id}", response_model=schemas.Candidate)
def update_candidate(candidate_id: int, updated_data: schemas.CandidateCreate, db: Session = Depends(database.get_db)):
    db_query = db.query(models.Candidate).filter(models.Candidate.id == candidate_id)
    db_candidate = db_query.first()
    if not db_candidate:
        raise HTTPException(status_code=404, detail="Impossibile aggiornare: Candidato inesistente")
    db_query.update(updated_data.dict(), synchronize_session=False)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

@app.delete("/candidates/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(candidate_id: int, db: Session = Depends(database.get_db)):
    db_candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not db_candidate:
        raise HTTPException(status_code=404, detail=f"Candidato con ID {candidate_id} non trovato")
    db.delete(db_candidate)
    db.commit()
    return None

    import shutil
import os
from fastapi import UploadFile, File

# --- ROTTA PER CARICARE IL CV (PDF) ---
@app.post("/candidates/{candidate_id}/upload-cv")
async def upload_cv(candidate_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    # 1. Verifichiamo che il candidato esista nel DB
    db_candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not db_candidate:
        raise HTTPException(status_code=404, detail="Candidato non trovato, impossibile caricare il CV")

    # 2. Controlliamo che il file sia un PDF
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Formato non supportato. Carica solo file PDF.")

    # 3. Creiamo il percorso (es: static/cv_1.pdf)
    file_path = f"static/cv_{candidate_id}.pdf"
    
    # 4. Salviamo il file sul disco
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {
        "messaggio": "CV salvato correttamente",
        "file_name": f"cv_{candidate_id}.pdf",
        "percorso": file_path
    }

