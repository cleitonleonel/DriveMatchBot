# Script de Deploy Automatizado - DriveMatchBot (Windows PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "🚀 Iniciando Deploy do DriveMatchBot..."

# Testa suporte ao 'docker compose' (V2) ou 'docker-compose' (V1)
$cmd = "docker"
$args = "compose"
try {
    & docker compose version | Out-Null
    $useV2 = $true
} catch {
    $useV2 = $false
}

Write-Host "🛑 Parando serviços existentes..."
if ($useV2) { docker compose down } else { docker-compose down }

Write-Host "🏗️  Reconstruindo imagem do bot..."
if ($useV2) { docker compose build bot } else { docker-compose build bot }

Write-Host "🆙 Subindo containers (db, redis, bot)..."
if ($useV2) { docker compose up -d } else { docker-compose up -d }

Write-Host "📊 Status dos containers:"
if ($useV2) { docker compose ps } else { docker-compose ps }

Write-Host "✅ Deploy concluído com sucesso!"
Write-Host "💡 Use 'docker compose logs -f bot' para acompanhar os logs em tempo real."
