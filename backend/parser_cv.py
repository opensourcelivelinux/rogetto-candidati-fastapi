import fitz  # PyMuPDF

def estrai_testo_da_pdf(percorso_pdf):
    testo_totale = ""
    try:
        # Apriamo il documento
        doc = fitz.open(percorso_pdf)
        for pagina in doc:
            testo_totale += pagina.get_text()
        doc.close()
        return testo_totale
    except Exception as e:
        return f"Errore durante la lettura del PDF: {e}"

# TEST VELOCE: Proviamo a leggere il tuo CV
if __name__ == "__main__":
    # Sostituisci 'tuo_cv.pdf' con il nome reale del file che hai in static/
    path = "static/cv_1.pdf" 
    risultato = estrai_testo_da_pdf(path)
    
    print("--- TEST DI LETTURA ---")
    print(risultato[:1000]) # Stampiamo i primi 1000 caratteri
    print("-----------------------")
