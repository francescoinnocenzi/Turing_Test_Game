from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Monta la directory "static" per servire file statici (CSS, JS, immagini, ecc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configura il motore di template Jinja2, che si aspetta file HTML nella cartella "templates"
templates = Jinja2Templates(directory="templates")

API_URL = "http://backend:8003"

# Endpoint GET per servire la pagina HTML iniziale
@app.get("/", response_class=HTMLResponse)
async def get(request: Request) -> HTMLResponse:
    # Restituisce il template HTML (index.html) con la variabile "request"
    return templates.TemplateResponse("login.html", {"request": request})

# Pagina di login (default)
@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


# Index
@app.get("/index", response_class=HTMLResponse)
async def get_index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


# Login
@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


# Register
@app.get("/register", response_class=HTMLResponse)
async def get_register(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("register.html", {"request": request})


# Modalità singleplayer
@app.get("/singleplayer", response_class=HTMLResponse)
async def get_singleplayer(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("singleplayer.html", {"request": request})


# Modalità multiplayer
@app.get("/multiplayer", response_class=HTMLResponse)
async def get_multiplayer(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("multiplayer.html", {"request": request})


# Modalità singleplayer - Judge
@app.get("/single/judge", response_class=HTMLResponse)
async def get_single_judge(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("judge.html", {"request": request, "mode": "single"})


# Modalità singleplayer - Human
@app.get("/single/human", response_class=HTMLResponse)
async def get_single_human(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("player.html", {"request": request, "mode": "single_human"})


# Judge multiplayer
@app.get("/judge", response_class=HTMLResponse)
async def get_judge(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("judge.html", {"request": request, "mode": "multi"})


# Player multiplayer
@app.get("/player", response_class=HTMLResponse)
async def get_player(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("player.html", {"request": request, "mode": "multi"})


# Ranking
@app.get("/ranking", response_class=HTMLResponse)
async def get_ranking(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("ranking.html", {"request": request})


# Judge multi UI
@app.get("/judge_multi", response_class=HTMLResponse)
async def get_judge_multi(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("judge_multi.html", {"request": request})


# Player multi UI
@app.get("/player_multi", response_class=HTMLResponse)
async def get_player_multi(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("player_multi.html", {"request": request})