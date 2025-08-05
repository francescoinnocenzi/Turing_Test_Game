import uvicorn

def main():
    """
    Funzione principale che avvia il server Uvicorn per il backend.

    Configura il server per eseguire l'app sull'host "0.0.0.0" 
    (accessibile da qualsiasi dispositivo) e sulla porta 8003.
    """
    
    uvicorn.run("backend:app", host="0.0.0.0", port=8003, reload=True)

if __name__ == '__main__':
    main()
