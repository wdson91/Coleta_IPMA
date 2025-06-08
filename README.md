# 🌦️ API de Previsão do Tempo (FastAPI)

API para consultar a previsão do tempo em Portugal com dados do IPMA (Instituto Português do Mar e da Atmosfera), utilizando `requests` ou `Playwright` para raspagem dinâmica. Suporte opcional a Redis para cache.

---

## 🔧 Tecnologias

* [FastAPI](https://fastapi.tiangolo.com/)
* [Playwright](https://playwright.dev/python/)
* [Redis (async)](https://redis.io/)
* [Jinja2](https://jinja.palletsprojects.com/)
* Fonte dos dados: [https://www.ipma.pt/pt/otempo/prev.localidade.hora](https://www.ipma.pt/pt/otempo/prev.localidade.hora)

---

## ■ Como utilizar a API

### Endpoints principais

| Método | Rota                 | Descrição                           | Parâmetros principais                                                                                                              |
| ------ | -------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| GET    | `/`                  | Página inicial                      | -                                                                                                                                  |
| GET    | `/coleta_requests`   | Interface com coleta via requests   | -                                                                                                                                  |
| GET    | `/coleta_playwright` | Interface com coleta via Playwright | -                                                                                                                                  |
| GET    | `/get_distritos`     | Retorna lista de distritos          | -                                                                                                                                  |
| GET    | `/get_locations`     | Retorna lista de localidades        | -                                                                                                                                  |
| GET    | `/api_playwright`    | Retorna previsão do tempo           | `distrito` (obrigatório), `location` (obrigatório), `data` (opcional, formato `YYYY-MM-DD`), `use_cache` (opcional, padrão `true`) |
| GET    | `/api_requests`      | Retorna previsão do tempo via requests com filtro opcional por data | `distrito` (obrigatório), `location` (obrigatório), `data` (opcional, formato `YYYY-MM-DD`)                                         |



### Exemplos de chamadas

* Buscar previsão para um distrito e localidade via Playwright:

```

GET /api_playwright?distrito=Lisboa&location=Lisboa

```

* Buscar previsão para uma data específica via Playwright:

```

GET /api_playwright?distrito=Porto&location=Porto&data=2025-06-08

```

* Ignorar cache via Playwright:

```

GET /api_playwright?distrito=Faro&location=Faro&use_cache=false

```

---

* Buscar previsão para um distrito e localidade via requests:

```

GET /api_requests?distrito=Lisboa&location=Lisboa

```

* Buscar previsão para uma data específica via requests:

```

GET /api_requests?distrito=Porto&location=Porto&data=2025-06-08

```


## 💾 Cache com Redis

* Previsões são armazenadas por **24 horas (86400 segundos)**
* Formato da chave: `"{distrito}:{location}"`
* Use `use_cache=false` para ignorar o cache e buscar dados em tempo real

---

## ■ Instruções de instalação

### Pré-requisitos

* Python 3.10 - 3.12
* (Opcional) Docker e Docker Compose para execução via container

### Instalar dependências

1. Crie e ative um ambiente virtual (recomendado):

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

2. Instale as dependências necessárias:

```bash
pip install -r requirements.txt
pip install playwright
playwright install
```

---

## ■ Como executar a aplicação

### 1. Executar localmente

```bash
uvicorn main:app --reload --loop asyncio
```

Acesse a aplicação em [http://localhost:8000](http://localhost:8000).

> ℹ️ **Importante:** o uso de Redis é **opcional**, mas é **altamente recomendado** para uma interação mais rápida e fluida nas coletas com Playwright, evitando requisições repetidas e pesadas.


### 2. Rodar Redis com Docker

Para rodar um contêiner Redis localmente com o nome `redis` (necessário para `host="redis"` funcionar corretamente), execute:

```bash
docker run -d --name redis -p 6379:6379 redis
```

> Isso inicia um contêiner Redis padrão, disponível na porta `6379`, com o nome exato `redis`.


## 🐳 Executando com Docker Compose

### Pré-requisitos:

* Docker e Docker Compose instalados

### Comando:

```bash
docker-compose up
```

Isso irá:

* Subir a aplicação FastAPI na porta `8000`
* Subir o container Redis
* Tornar a aplicação acessível em: [http://localhost:8000](http://localhost:8000)

---

## 📄 Páginas HTML

### `coleta_requests.html`

Interface web para consultar previsão do tempo via `requests`.

**Funcionalidades:**

* Seleção de **distrito** e **localidade**
* Filtro de data opcional
* Exibição em **cartões** com: temperatura, vento, precipitação, UV e ícones gráficos ☀️ 🌧️
* JavaScript puro (`fetch`) no frontend
* Requisições para `/get_distritos` e `/get_locations`

---

### `coleta_playwright.html`

Interface idêntica à anterior, com a diferença de que os dados são obtidos via backend com Playwright.

---

## 🔍 Detalhes sobre a Coleta e Lista de Localidades

### 📌 Como os distritos e localidades são obtidos

A lista de **distritos** e **localidades** exibida nas interfaces HTML é extraída diretamente da página do IPMA. O backend realiza uma **requisição HTTP à página oficial do IPMA**, analisando o conteúdo HTML para obter os valores dos elementos `<select>`, que são então servidos via endpoints (`/get_distritos` e `/get_locations`).

Isso garante que a interface esteja sempre atualizada com a lista real disponível no site oficial, mesmo sem o uso de uma API estruturada do IPMA para esse fim.

---

### 🔎 Como a coleta de dados meteorológicos funciona

#### 📡 Via `requests`

A coleta com `requests` simula uma requisição feita pelo navegador ao acessar a previsão para uma localidade. A aplicação envia uma **requisição direta à página do IPMA**, obtém o HTML resultante e faz a **extração das informações meteorológicas diretamente do conteúdo da resposta**.

* É uma abordagem leve e rápida.
* Ideal quando os endpoints públicos do IPMA estão disponíveis e funcionando corretamente.

#### 🧭 Via `Playwright`

A coleta com `Playwright` é mais robusta: ela simula a **interação de um usuário real com a página**.

1. A página do IPMA é aberta num navegador automatizado.
2. Os menus suspensos de **distrito** e **localidade** são preenchidos automaticamente.
3. Após a seleção, o navegador aguarda o carregamento dinâmico dos dados.
4. Em seguida, o conteúdo HTML da previsão renderizada é **raspado** e processado.

* Ideal para quando os dados são carregados via JavaScript e não estão disponíveis diretamente por meio de requests.

---

## 💡 Diferenças entre os modos

| Recurso            | `coleta_requests.html`      | `coleta_playwright.html`            |
| ------------------ | --------------------------- | ----------------------------------- |
| Fonte dos dados    | API pública do IPMA         | Scraping automatizado (Playwright)  |
| Backend necessário | Sim (requisições HTTP)      | Sim (execução de navegador)         |
| Interface          | Igual                       | Igual                               |
| Uso recomendado    | Quando a API está funcional | Quando a API falha ou está limitada |

---

## 📂 Estrutura esperada do projeto

```
.
├── main.py
├── coleta.py
├── templates/
│   ├── index.html
│   ├── coleta_requests.html
│   └── coleta_playwright.html
├── docker-compose.yml
├── Dockerfile
```

---

## ✅ Justificativa da Escolha do FastAPI

A escolha pelo **FastAPI** nesta aplicação se deve a diversos fatores técnicos que se alinham diretamente às necessidades do projeto:

### 🌐 Suporte nativo a `async/await`

* O **Playwright** é uma biblioteca assíncrona (async) para automação de navegação web, essencial para coleta de dados dinâmicos do IPMA.
* O FastAPI oferece suporte assíncrono completo, permitindo integração eficiente com Playwright sem bloqueio de I/O.

### 🚀 Desempenho e produtividade

* Validação automática de parâmetros com **Pydantic**
* Geração automática de documentação (Swagger e Redoc)
* Excelente performance comparável a frameworks como Node.js ou Go

### 🔌 Integração fácil com Redis e cache

* Utilização de `aioredis` para cache assíncrono e escalável das previsões
* Permite controle fino sobre tempo de vida do cache e invalidação condicional (`use_cache=false`)

---


## 🛠️ Pontos de Melhoria Planejados

### ✅ Sistema inteligente de normalização de nomes

Um dos desafios identificados é que os nomes dos distritos e localidades utilizados no frontend podem conter **acentos e diferenças de capitalização** (ex: `"Évora"` vs `"evora"`), o que atualmente pode gerar falhas na busca e comparação no backend.

**Planeja-se implementar futuramente um sistema inteligente que:**

* Normalize os nomes removendo acentos e convertendo para minúsculas.
* Garanta que variações como `"Évora"`, `"evora"` e `"évora"` sejam tratadas como equivalentes.
* Evite problemas na geração de URLs, cache e consulta dos dados.

---

### 🔄 Normalização do formato de retorno entre métodos de coleta

Atualmente, embora os dados extraídos via `requests` e `Playwright` sejam semanticamente equivalentes, a **estrutura e organização dos campos pode variar** entre os dois métodos. Isso ocorre porque a fonte de dados (HTML estático vs. renderizado) tem pequenas diferenças de marcação.

**Está planejado um mecanismo de padronização de resposta**, de modo que:

* O formato de retorno seja **consistente**, independentemente do método de coleta utilizado.
* Os nomes dos campos, tipos de dados e estrutura JSON sejam uniformizados.
* Isso facilite o consumo por parte do frontend e potenciais usuários externos da API.

---

### 🌐 Outras melhorias

* Validação e normalização dos nomes também no frontend para melhorar a experiência do usuário.
* Eventual suporte à internacionalização para outras línguas/regiões.
* Melhor tratamento de erros e mensagens amigáveis em caso de falha na raspagem.
* Eventual mudança para um input com autocomplete
