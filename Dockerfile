# Use a imagem base oficial do Python slim para menor tamanho
FROM python:3.12-slim

# Evita a geração de arquivos .pyc, permite logs em tempo real e configura timeouts estendidos para uv (Raspberry Pi)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_HTTP_TIMEOUT=300
ENV UV_CONCURRENT_BUILDS=2

# Instala dependências do sistema necessárias para PostGIS, CFFI/CairoSVG, compilação C/C++ e outras extensões
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libpq-dev \
    python3-dev \
    libgeos-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf-xlib-2.0-dev \
    shared-mime-info \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instala o uv via pip para compatibilidade total com ARM (Raspberry Pi) e x86_64
RUN pip install --no-cache-dir uv

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos de definição de dependências e README
COPY pyproject.toml uv.lock* README.md ./

# Instala apenas as dependências externas primeiro (cache eficiente de camadas)
RUN uv sync --frozen --no-install-project

# Copia todo o código da aplicação
COPY . .

# Finaliza o sync instalando o pacote local drivematch
RUN uv sync --frozen

# Comando padrão para rodar a aplicação (Bot)
CMD ["uv", "run", "python", "main.py"]
