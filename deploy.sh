#!/bin/bash

# Script de Deploy Automatizado - DriveMatchBot
# Este script reconstrói os containers para garantir que a versão mais recente do código seja aplicada.

echo "🚀 Iniciando Deploy do DriveMatchBot..."

# 1. Parar containers antigos (mantendo volumes)
echo "🛑 Parando serviços existentes..."
docker-compose down

# 2. Reconstruir a imagem do Bot
echo "🏗️  Reconstruindo imagem do bot..."
docker-compose build bot

# 3. Subir infraestrutura em background
echo "🆙 Subindo containers (db, redis, bot)..."
docker-compose up -d

# 4. Verificar status
echo "📊 Status dos containers:"
docker-compose ps

echo "✅ Deploy concluído com sucesso!"
echo "💡 Use 'docker-compose logs -f bot' para acompanhar os logs em tempo real."
