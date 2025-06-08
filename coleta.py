from datetime import datetime
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)
from fastapi import HTTPException


async def buscar_previsao(distrito: str, location: str):
    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://www.ipma.pt/pt/otempo/prev.localidade.hora/")

            try:
                # Aguarda carregamento do seletor de distrito
                await page.wait_for_selector("#district", timeout=5000)

                # Verifica se o distrito existe

                # Seleciona o distrito
                await page.select_option("#district", value=distrito)

                # Aguarda carregamento das localizações
                await page.wait_for_selector("#locations", timeout=5000)

                await page.select_option("#locations", value=location)
            except PlaywrightTimeoutError:
                raise HTTPException(
                    status_code=404,
                    detail=f"Distrito '{distrito}' ou localidade '{location}' não encontrados.",
                )
            # Aguarda os dados de previsão
            await page.wait_for_selector("#weekly .weekly-column", timeout=10000)

            # Extrai a data base
            last_update_text = await page.text_content("#last_update > i")
            base_date_str = last_update_text.split(" ")[0]
            base_date = datetime.strptime(base_date_str, "%Y-%m-%d")
            mes = base_date.month
            ano = base_date.year

            # Extrai a previsão para a semana
            dias = await page.query_selector_all("#weekly .weekly-column")
            previsao_semana = []

            for dia in dias:
                try:
                    date_text = await dia.query_selector(".date")
                    date_raw = await date_text.text_content() if date_text else None
                    numero_dia = (
                        int(date_raw.strip().split(",")[1].strip())
                        if date_raw
                        else None
                    )

                    data_real = (
                        datetime(ano, mes, numero_dia).strftime("%Y-%m-%d")
                        if numero_dia
                        else None
                    )

                    previsao_dia = {
                        "data": data_real,
                        "tempo": await (
                            await dia.query_selector(".weatherImg")
                        ).get_attribute("title"),
                        "temp_min": await (
                            await dia.query_selector(".tempMin")
                        ).text_content(),
                        "temp_max": await (
                            await dia.query_selector(".tempMax")
                        ).text_content(),
                        "vento": await (
                            await dia.query_selector(".windImg")
                        ).get_attribute("title"),
                        "direcao_vento": await (
                            await dia.query_selector(".windDir")
                        ).text_content(),
                        "imagem": await (
                            await dia.query_selector(".weatherImg")
                        ).get_attribute("src"),
                        "precipitacao": await (
                            await dia.query_selector(".precProb")
                        ).text_content(),
                        "iuv": (
                            await (await dia.query_selector(".iuvImg")).get_attribute(
                                "title"
                            )
                            if await dia.query_selector(".iuvImg")
                            else "N/A"
                        ),
                    }

                    previsao_semana.append(previsao_dia)

                except Exception as e:
                    previsao_semana.append(
                        {"erro": f"Falha ao processar um dia: {str(e)}"}
                    )

            return previsao_semana

        except HTTPException:
            raise  # repropaga erro HTTP definido
        except PlaywrightTimeoutError:
            raise HTTPException(
                status_code=504,
                detail="Tempo limite excedido ao buscar dados de previsão.",
            )
        finally:
            if browser:
                await browser.close()
