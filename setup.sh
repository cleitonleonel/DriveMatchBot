#!/bin/bash

set -e  # para se der erro

echo "🚀 Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

echo "🐍 Instalando Python e dependências básicas..."
sudo apt install -y python3 python3-venv python3-pip build-essential libpq-dev

echo "🧠 Instalando PostgreSQL + PostGIS..."
sudo apt install -y postgresql postgresql-contrib postgis postgresql-15-postgis-3

echo "🔴 Instalando Redis..."
sudo apt install -y redis-server

echo "⚡ Instalando uv..."
curl -Ls https://astral.sh/uv/install.sh | sh

# garante que uv está no PATH
export PATH="$HOME/.cargo/bin:$PATH"

echo "📦 Criando ambiente virtual..."
cd /home/usuario/Desktop/DriveMatchBot

uv venv

echo "📚 Instalando dependências do projeto..."
uv pip install -r requirements.txt

echo "🗄️ Iniciando serviços..."

sudo systemctl enable postgresql
sudo systemctl start postgresql

sudo systemctl enable redis
sudo systemctl start redis

echo "🔧 Criando extensão PostGIS..."

sudo -u postgres psql <<EOF
CREATE EXTENSION IF NOT EXISTS postgis;
EOF

echo "📊 Rodando migrations..."
source .venv/bin/activate
alembic upgrade head

echo "✅ Setup finalizado com sucesso!"
