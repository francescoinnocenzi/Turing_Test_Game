import uvicorn

def main():
    """
    Funzione principale che avvia il server Uvicorn per eseguire il frontend.

    Esegue l'app FastAPI sull'indirizzo '0.0.0.0' 
    (accessibile da qualsiasi host) e sulla porta 8001.
    """
    
    uvicorn.run("frontend:app", host="0.0.0.0", port=8001, reload=True)

if __name__ == '__main__':
    main()