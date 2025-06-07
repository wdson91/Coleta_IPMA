from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from coleta import buscar_previsao
import redis.asyncio as redis
import json

from datetime import datetime


redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)
app = FastAPI()

templates = Jinja2Templates(directory="templates")


## ROTAS PARA RENDERIZAR PÁGINAS HTML
@app.get("/coleta_requests", response_class=HTMLResponse)
def coleta_requests(request: Request):
    return templates.TemplateResponse("coleta_requests.html", {"request": request})


@app.get("/coleta_playwright", response_class=HTMLResponse)
def coleta_playwright(request: Request):
    return templates.TemplateResponse("coleta_playwright.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


## ROTAS PARA BUSCAR DADOS DA API IPMA
@app.get("/get_locations")
def get_locations():
    try:
        locations = requests.get(
            "https://api.ipma.pt/public-data/forecast/locations.json"
        ).json()
        return JSONResponse(
            content=locations, media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})


@app.get("/get_distritos")
def get_distritos():
    try:
        distritos = requests.get(
            "https://api.ipma.pt/public-data/districts.json"
        ).json()
        return JSONResponse(
            content=distritos, media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"erro": str(e)})


## ROTAS PARA BUSCAR PREVISÃO DO TEMPO COM PLAYWRIGHT
@app.get("/api_playwright")
async def forecast_route(
    distrito: str,
    location: str,
    data: str = Query(None, description="Data no formato YYYY-MM-DD (opcional)"),
    use_cache: bool = Query(
        True, description="Se false, ignora cache e coleta de novo"
    ),
):

    try:
        chave = f"{distrito}:{location}"

        # Verifica se a chave já existe no cache se use_cache for True
        cache = await redis_client.get(chave) if use_cache else None

        # Se a chave não existe ou use_cache é False, busca a previsão
        previsao = (
            json.loads(cache) if cache else await buscar_previsao(distrito, location)
        )

        # Se não tiver cache, armazena a previsão no Redis
        if not cache:
            await redis_client.set(chave, json.dumps(previsao), ex=86400)

        # Filtra por data se necessário
        if data:
            try:
                # Valida formato da data
                datetime.strptime(data, "%Y-%m-%d")
                previsao = [p for p in previsao if p.get("data") == data]
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"erro": "Formato de data inválido. Use YYYY-MM-DD."},
                )

        return {
            "distrito": distrito,
            "location": location,
            "data_filtrada": data if data else None,
            "previsao": previsao,
        }

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"erro": e.detail})

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"erro": f"Erro ao buscar previsão: {str(e)}"},
        )
