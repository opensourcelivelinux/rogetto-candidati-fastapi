from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
import fitz  # Libreria PyMuPDF per leggere i PDF
import models, schemas, database

# 1. Inizializzazione Database
models.Base.metadata.create_all(bind=database.engine)

# 2. Configurazione App
app = FastAPI(title="Gestione Candidati API - AI Powered")

# Assicuriamoci che la cartella static esista per i PDF
if not os.path.exists("static"):
    os.makedirs("static")

# 3. ROTTE API

@app.get("/")
def read_root():
    return {"status": "Online", "database": "Connesso", "AI_Parser": "Pronto"}

# --- CRUD CANDIDATI ---

@app.post("/candidates", response_model=schemas.Candidate, status_code=status.HTTP_201_CREATED)
def create_candidate(candidate: schemas.CandidateCreate, db: Session = Depends(database.get_db)):
    db_candidate = models.Candidate(**candidate.dict())
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

@app.get("/candidates", response_model=List[schemas.Candidate])
def read_candidates(role: str = None, min_exp: int = 0, db: Session = Depends(database.get_db)):
    query = db.query(models.Candidate)
    if role:
        query = query.filter(models.Candidate.role.ilike(f"%{role}%"))
    if min_exp > 0:
        query = query.filter(models.Candidate.experience_years >= min_exp)
    return query.all()

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
        raise HTTPException(status_code=404, detail="Candidato inesistente")
    db_query.update(updated_data.dict(), synchronize_session=False)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

@app.delete("/candidates/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(candidate_id: int, db: Session = Depends(database.get_db)):
    db_candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not db_candidate:
        raise HTTPException(status_code=404, detail="Candidato non trovato")
    db.delete(db_candidate)
    db.commit()
    return None

# --- LOGICA DI ANALISI CV (AI PARSER) ---

@app.post("/candidates/{candidate_id}/upload-cv")
async def upload_cv(candidate_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    # 1. Verifica esistenza candidato
    db_candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not db_candidate:
        raise HTTPException(status_code=404, detail="Candidato non trovato")

    # 2. Controllo formato
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Carica solo file PDF")

    # 3. Salvataggio fisico del file
    file_path = f"static/cv_{candidate_id}.pdf"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 4. ANALISI INTELLIGENTE CON PYMUPDF
    try:
        doc = fitz.open(file_path)
        testo_completo = ""
        for pagina in doc:
            testo_completo += pagina.get_text().lower()
        doc.close()

        # Logica di classificazione (Keywords)
        keywords_senior = ["senior", "lead", "esperto", "manager", "architect", "responsabile"]
        livello_rilevato = "Senior" if any(k in testo_completo for k in keywords_senior) else "Junior"
        
        skills_target = ["python", "fastapi", "docker", "sql", "linux", "postgresql", "git"]
        skills_trovate = [s for s in skills_target if s in testo_completo]

        # 5. AGGIORNAMENTO DATABASE CON I RISULTATI DELL'ANALISI
        db_candidate.level = livello_rilevato
        db_candidate.skills = ", ".join(skills_trovate)
        db_candidate.cv_path = file_path
        
        db.commit()
        db.refresh(db_candidate)

        return {
            "messaggio": "CV caricato e analizzato con successo",
            "risultato_analisi": {
                "livello_stimato": livello_rilevato,
                "competenze_rilevate": skills_trovate
            },
            "candidato": f"{db_candidate.first_name} {db_candidate.last_name}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante l'analisi: {str(e)}")
