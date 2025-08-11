from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
from pydantic import BaseModel

app = FastAPI()

# Monta la directory "static" per servire file statici (CSS, JS, immagini, ecc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configura il motore di template Jinja2, che si aspetta file HTML nella cartella "templates"
templates = Jinja2Templates(directory="templates")

API_URL = "http://backend:8003"

class AskRequest(BaseModel):
    question: str

# Endpoint GET per servire la pagina HTML iniziale
@app.get("/")
async def get(request: Request):
    # Restituisce il template HTML (index.html) con la variabile "request"
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/judge")
async def get_judge(request: Request):
    # Restituisce il template HTML (judge.html) con la variabile "request"
    return templates.TemplateResponse("judge.html", {"request": request})

@app.get("/player")
async def get_player(request: Request):
    # Restituisce il template HTML (player.html) con la variabile "request"
    return templates.TemplateResponse("player.html", {"request": request})


    