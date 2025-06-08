from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from coleta import buscar_previsao
import redis.asyncio as redis
import json
import httpx
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


## ROTA PARA BUSCAR PREVISÃO DO TEMPO COM PLAYWRIGHT
@app.get("/api_playwright")
async def api_playwright(
    distrito: str,
    location: str,
    data: str = Query(None, description="Data no formato YYYY-MM-DD (opcional)"),
    use_cache: bool = Query(
        True, description="Se false, ignora cache e coleta de novo"
    ),
):
    try:
        chave = f"{distrito}:{location}"

        cache = None
        if use_cache:
            try:
                cache = await redis_client.get(chave)
            except Exception:
                # Ignora erro no Redis e segue sem cache
                cache = None

        if cache:
            previsao = json.loads(cache)
        else:
            previsao = await buscar_previsao(distrito, location)
            if previsao is not None and use_cache:
                try:
                    await redis_client.set(chave, json.dumps(previsao), ex=86400)
                except Exception:
                    # Ignora erro ao salvar cache
                    pass

        # Filtra por data se necessário
        if data:
            try:
                datetime.strptime(data, "%Y-%m-%d")
                previsao = [p for p in previsao if p.get("data") == data]
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"erro": "Formato de data inválido. Use YYYY-MM-DD."},
                )

        return {
            "previsao": previsao,
        }

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"erro": e.detail})

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"erro": f"Erro ao buscar previsão: {str(e)}"},
        )


## ROTA PARA BUSCAR PREVISÃO DO TEMPO COM REQUESTS
@app.get("/api_requests")
def api_requests(
    distrito: str,
    location: str,
    data: str = Query(None, description="Data no formato YYYY-MM-DD (opcional)"),
):

    lista_distritos = requests.get(
        "https://api.ipma.pt/public-data/districts.json"
    ).json()
    lista_locations = requests.get(
        "https://api.ipma.pt/public-data/forecast/locations.json"
    ).json()

    # Filtra os nomes dos distritos e locations das listas
    nomes_distritos = [d["nome"] for d in lista_distritos]
    nomes_locations = [l["local"] for l in lista_locations]

    # Verifica se os nomes existem em suas respectivas listas
    if distrito not in nomes_distritos or location not in nomes_locations:
        return JSONResponse(
            status_code=404,
            content={"erro": "Distrito ou localização não encontrados."},
        )

    # Encontra o ID do Location
    location_id = next(
        (loc["globalIdLocal"] for loc in lista_locations if loc["local"] == location),
        None,
    )

    if not location_id:
        return JSONResponse(
            status_code=404,
            content={"erro": "ID da localização não encontrado."},
        )

    try:
        previsao = requests.get(
            f"https://api.ipma.pt/public-data/forecast/aggregate/{location_id}.json"
        ).json()

        # Filtra por data se fornecida
        if data:

            try:
                datetime.strptime(data, "%Y-%m-%d")

                previsao = [
                    p for p in previsao if p.get("dataPrev").split("T")[0] == data
                ]
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"erro": "Formato de data inválido. Use YYYY-MM-DD."},
                )

        return {
            "previsao": previsao,
        }

    except requests.RequestException as e:
        return JSONResponse(
            status_code=500,
            content={"erro": f"Erro ao buscar previsão: {str(e)}"},
        )
