#!/bin/bash

set -e

# Script de Deploy Automatizado - DriveMatchBot
# Este script reconstrói os containers para garantir que a versão mais recente do código seja aplicada.

echo "🚀 Iniciando Deploy do DriveMatchBot..."

# Suporte tanto para 'docker compose' (V2) quanto 'docker-compose' (V1)
DOCKER_COMPOSE="docker compose"
if ! $DOCKER_COMPOSE version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
fi

# 1. Parar containers antigos (mantendo volumes)
echo "🛑 Parando serviços existentes..."
$DOCKER_COMPOSE down

# 2. Reconstruir a imagem do Bot
echo "🏗️  Reconstruindo imagem do bot..."
$DOCKER_COMPOSE build bot

# 3. Subir infraestrutura em background
echo "🆙 Subindo containers (db, redis, bot)..."
$DOCKER_COMPOSE up -d

# 4. Verificar status
echo "📊 Status dos containers:"
$DOCKER_COMPOSE ps

echo "✅ Deploy concluído com sucesso!"
echo "💡 Use '$DOCKER_COMPOSE logs -f bot' para acompanhar os logs em tempo real."
