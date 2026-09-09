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

echo "🔐 Configurando autenticação e acesso da rede Docker..."
PG_CONF="/etc/postgresql/$PG_VERSION/main/postgresql.conf"
PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"

# Garante que conexões locais via socket continuem usando peer (sem pedir senha no sudo)
sudo sed -i "s/local\s\+all\s\+postgres\s\+md5/local all postgres peer/" $PG_HBA || true

# Garante escuta em todas as interfaces no postgresql.conf
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" $PG_CONF || true
sudo sed -i "s/listen_addresses = 'localhost'/listen_addresses = '*'/" $PG_CONF || true

# Permite conexões TCP com senha (md5) para a rede do Docker (172.17.0.0/16 e host.docker.internal)
if ! grep -q "172.17.0.0/16" $PG_HBA; then
    echo "host    all             all             172.17.0.0/16           md5" | sudo tee -a $PG_HBA
fi
if ! grep -q "0.0.0.0/0" $PG_HBA; then
    echo "host    all             all             0.0.0.0/0               md5" | sudo tee -a $PG_HBA
fi

# Regra de Firewall se UFW estiver ativo
if command -v ufw >/dev/null 2>&1; then
    sudo ufw allow 5432/tcp || true
fi

echo "🔄 Reiniciando PostgreSQL para aplicar listen_addresses = '*'..."
sudo systemctl restart postgresql

echo "👤 Configurando usuário postgres..."
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '123456';"

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
