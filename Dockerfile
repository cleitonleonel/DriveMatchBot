# Use a imagem base oficial do Python slim para menor tamanho
FROM python:3.12-slim

# Evita a geração de arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependências do sistema necessárias para PostGIS e outras extensões
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    libgeos-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instala o uv via pip para compatibilidade total com ARM (Raspberry Pi) e x86_64
RUN pip install --no-cache-dir uv

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos de definição de dependências
COPY pyproject.toml uv.lock* ./

# Instala as dependências usando o uv
RUN uv sync --frozen

# Copia o restante do código da aplicação
COPY . .

# Comando padrão para rodar a aplicação (Bot)
CMD ["uv", "run", "python", "main.py"]
