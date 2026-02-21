from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
import fitz  # PyMuPDF
import re
from datetime import datetime

import models, schemas, database

# --- 🧠 IL CERVELLO: LOGICA DI ANALISI ESPERIENZA ---
def calculate_real_dev_experience(text):
    """
    Analizzatore contestuale: conta gli anni solo se associati a termini tech.
    Evita di contare esperienze lavorative in altri settori (es. metalmeccanico).
    """
    tech_keywords = ["sviluppatore", "developer", "software", "programmatore", "web", "python", "full stack", "backend", "frontend"]
    lines = text.split('\n')
    dev_years = []

    for i, line in enumerate(lines):
        clean_line = line.lower()
        # Controlla la riga attuale e quella precedente per il contesto
        context = clean_line
        if i > 0: 
            context += " " + lines[i-1].lower()
        
        if any(key in context for key in tech_keywords):
            # Estrae anni a 4 cifre (es. 2022)
            years = re.findall(r'20\d{2}', context)
            dev_years.extend([int(y) for y in years])

    # Se non trova nulla di specifico, cerca date degli ultimi 10 anni come fallback
    if not dev_years:
        current_year = datetime.now().year
        recent_years = [int(y) for y in re.findall(r'20\d{2}', text) if int(y) >= (current_year - 10)]
        dev_years = recent_years

    if not dev_years: 
        return 0
    
    unique_years = sorted(list(set(dev_years)))
    if len(unique_years) >= 2:
        diff = unique_years[-1] - unique_years
        return diff if diff > 0 else 1
    return 1

# --- ⚙️ INIZIALIZZAZIONE ---
models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="Gestione Candidati API - AI Powered")

if not os.path.exists("static"):
    os.makedirs("static")

# --- 🛣️ ROTTE API ---

@app.get("/")
def read_root():
    return {"status": "Online", "database": "Connesso", "AI_Parser": "Pronto"}

@app.post("/candidates", response_model=schemas.Candidate, status_code=status.HTTP_201_CREATED)
def create_candidate(candidate: schemas.CandidateCreate, db: Session = Depends(database.get_db)):
    db_candidate = models.Candidate(**candidate.dict())
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

@app.get("/candidates", response_model=List[schemas.Candidate])
def read_candidates(db: Session = Depends(database.get_db)):
    return db.query(models.Candidate).all()

# --- ROTTA ELIMINA CANDIDATO ---

@app.delete("/candidates/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(candidate_id: int, db: Session = Depends(database.get_db)):
    # 1. Cerca il candidato nel DB
    db_candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    
    # 2. Se non esiste, lancia errore 404
    if not db_candidate:
        raise HTTPException(status_code=404, detail="Candidato non trovato")
    
    # 3. Elimina fisicamente il file del CV se esiste (per non intasare il server)
    if db_candidate.cv_path and os.path.exists(db_candidate.cv_path):
        os.remove(db_candidate.cv_path)
    
    # 4. Elimina dal Database
    db.delete(db_candidate)
    db.commit()
    
    return None # Il codice 204 non restituisce contenuto


# --- 🚀 LOGICA DI ANALISI CV ---

@app.post("/candidates/{candidate_id}/upload-cv")
async def upload_cv(candidate_id: int, file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    db_candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not db_candidate:
        raise HTTPException(status_code=404, detail="Candidato non trovato")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Carica solo file PDF")

    file_path = f"static/cv_{candidate_id}.pdf"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        doc = fitz.open(file_path)
        testo_completo = ""
        for pagina in doc:
            testo_completo += pagina.get_text().lower()
        doc.close()

        # 1. Calcolo Anni (Allineato con schemas.py: experience_years)
        anni_calcolati = calculate_real_dev_experience(testo_completo)
        print(f"DEBUG: Anni rilevati per {db_candidate.first_name}: {anni_calcolati}")

        # 2. Classificazione Livello
        keywords_senior = ["senior", "lead", "esperto", "manager", "architect", "responsabile"]
        has_senior_key = any(k in testo_completo for k in keywords_senior)
        
        if anni_calcolati >= 5 or (anni_calcolati >= 3 and has_senior_key):
            livello_rilevato = "Senior"
        elif anni_calcolati >= 2:
            livello_rilevato = "Middle"
        else:
            livello_rilevato = "Junior"
        
        # 3. Estrazione Skills
        skills_target = ["python", "fastapi", "docker", "sql", "linux", "postgresql", "git", "javascript"]
        skills_trovate = [s for s in skills_target if s in testo_completo]

        # 4. SALVATAGGIO NEL DATABASE
        db_candidate.level = livello_rilevato
        db_candidate.experience_years = anni_calcolati  # <--- NOME SINCRONIZZATO
        db_candidate.skills = ", ".join(skills_trovate)
        db_candidate.cv_path = file_path
        
        db.commit()
        db.refresh(db_candidate)

        return {
            "messaggio": "CV analizzato con successo",
            "risultato": {
                "anni_esperienza": anni_calcolati,
                "livello": livello_rilevato,
                "skills": skills_trovate
            },
            "candidato": f"{db_candidate.first_name} {db_candidate.last_name}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore analisi: {str(e)}")
