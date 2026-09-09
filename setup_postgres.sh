#!/bin/bash

set -e

echo "🔄 Atualizando sistema..."
sudo apt update

echo "📦 Instalando PostgreSQL + dependências..."
sudo apt install -y postgresql postgresql-contrib postgresql-common

echo "🧩 Instalando PostGIS..."
# Detecta versão automaticamente
PG_VERSION=$(psql --version | awk '{print $3}' | cut -d '.' -f1)

sudo apt install -y postgis postgresql-$PG_VERSION-postgis-3

echo "🔓 Garantindo que o serviço não está mascarado..."
sudo systemctl unmask postgresql || true

echo "🚀 Iniciando PostgreSQL..."
sudo systemctl restart postgresql

echo "👤 Configurando usuário postgres..."
sudo -u postgres psql <<EOF
ALTER USER postgres WITH PASSWORD '123456';
EOF

echo "🔐 Configurando autenticação (md5)..."
PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"

sudo sed -i "s/local\s\+all\s\+postgres\s\+peer/local all postgres md5/" $PG_HBA

echo "🔄 Reiniciando PostgreSQL..."
sudo systemctl restart postgresql

echo "🗄️ Criando banco drivematch (se não existir)..."
sudo -u postgres psql <<EOF
DO \$\$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_database WHERE datname = 'drivematch'
   ) THEN
      CREATE DATABASE drivematch;
   END IF;
END
\$\$;
EOF

echo "🧩 Ativando extensão PostGIS..."
sudo -u postgres psql -d drivematch <<EOF
CREATE EXTENSION IF NOT EXISTS postgis;
EOF

echo "✅ Setup concluído com sucesso!"
echo ""
echo "🔗 String de conexão:"
echo "postgresql://postgres:123456@localhost:5432/drivematch"
