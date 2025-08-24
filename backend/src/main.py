import uvicorn
from backend import app


def main():
    """
    Funzione principale che avvia il server Uvicorn per il backend.

    Configura il server per eseguire l'app sull'host "0.0.0.0" 
    (accessibile da qualsiasi dispositivo) e sulla porta 8003.
    """
    
    uvicorn.run(app, host="0.0.0.0", port=8003)

if __name__ == '__main__':
    main()
