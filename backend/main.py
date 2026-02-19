from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Backend Funzionante!", "messaggio": "Vai su /docs per testare le API"}

@app.get("/docs")
def fake_docs():
    # Questo serve solo come test, FastAPI genera /docs automaticamente
    return {"messaggio": "Se vedi questo, la rotta /docs risponde"}
