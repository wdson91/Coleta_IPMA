# Dockerfile

FROM python
# Diretório da aplicação
WORKDIR /app

RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libasound2 \
    wget \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# Copia os arquivos
COPY requirements.txt .

RUN pip install --upgrade pip

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt


# Copia o resto do projeto
COPY . .

RUN pip install playwright && playwright install --with-deps
# Expõe a porta padrão do Uvicorn
EXPOSE 8000

# Comando para iniciar o FastAPI com Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
