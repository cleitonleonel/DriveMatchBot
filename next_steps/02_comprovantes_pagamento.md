# Próximos Passos: Comprovantes de Pagamento (Ponto 2)

## Objetivo
Implementar um sistema de envio e validação de comprovantes de pagamento via imagem para aumentar a segurança e confiabilidade das transações entre passageiros e motoristas.

## Funcionalidades Planejadas

### 1. Envio pelo Passageiro 📸
- Ao finalizar a viagem, o passageiro terá a opção de fazer o upload de uma imagem (print do PIX).
- O bot deve capturar o evento de mídia e associá-lo à `travel_id` atual.
- Armazenar o `file_id` do Telegram no banco de dados para referência futura.

### 2. Notificação ao Motorista 🔔
- Assim que o comprovante for enviado, o motorista recebe a imagem e uma mensagem de confirmação.
- Botões interativos: `✅ Pagamento Confirmado` e `❌ Não recebi`.

### 3. Histórico e Disputas ⚖️
- O comprovante deve ficar disponível no histórico de viagens (`/wallet`) para consulta rápida em caso de problemas.
- Em caso de contestação (`❌ Não recebi`), notificar automaticamente a administração via grupo de suporte.

## Arquivos a serem alterados:
- `drivematch/models/travel.py`: Adicionar coluna `receipt_file_id`.
- `plugins/conversation.py`: Adicionar handler para mensagens do tipo imagem/documento durante o estado de finalização.
- `plugins/callback.py`: Adicionar lógica de confirmação de recebimento pelo motorista.
