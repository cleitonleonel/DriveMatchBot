from telethon import events, Button
from smartbot.utils.handler import ClientHandler
from smartbot.config import ADMIN_IDS

client = ClientHandler()


def is_admin(sender_id):
    return sender_id in ADMIN_IDS


@client.on(events.NewMessage(pattern='/admin'))
async def admin_menu(event):
    sender_id = event.sender_id
    if not is_admin(sender_id):
        return

    stats = await event.client.controller.get_admin_stats()
    settings = await event.client.controller.get_system_settings()

    text = (
        "👑 **PAINEL ADMINISTRATIVO**\n\n"
        f"👥 **Usuários:** {stats['users_count']} __({stats['drivers_count']} motoristas)__\n"
        f"🚕 **Viagens Totais:** {stats['travels_count']}\n\n"
        "📊 **FINANCEIRO ACUMULADO**\n"
        f"💰 Total Bruto: **R$ {stats['revenue_total']:.2f}**\n"
        f"💎 Plataforma: **R$ {stats['revenue_platform']:.2f}**\n"
        f"🤝 Motoristas: **R$ {stats['revenue_drivers']:.2f}**\n\n"
        "⚙️ **CONFIGURAÇÃO ATUAL**\n"
        f"📍 Base: `R$ {settings['base_fare']:.2f}` | KM: `R$ {settings['price_per_km']:.2f}`\n"
        f"⏱ Min: `R$ {settings['price_per_min']:.2f}` | Fee: `R$ {settings['service_fee']:.2f}`\n"
        f"📈 Taxa Padrão: **{settings['default_platform_percentage']}%**\n"
    )

    buttons = [
        [Button.inline("📊 Relatórios Detalhados", b"admin_metrics")],
        [Button.inline("💰 Pagamentos Pendentes", b"admin_payouts")],
        [Button.inline("⚙️ Editar Taxas Globais", b"admin_rates")],
        [Button.inline("👥 Gerenciar Usuários", b"admin_users")],
        [Button.inline("🔙 Fechar Painel", b"admin_close")]
    ]
    await event.respond(text, buttons=buttons)


@client.on(events.CallbackQuery(pattern=b'admin_'))
async def admin_callbacks(event):
    sender_id = event.sender_id
    if not is_admin(sender_id):
        return await event.answer("Acesso negado.", alert=True)

    data = event.data
    if data == b'admin_close':
        await event.delete()
    elif data == b'admin_metrics':
        await event.answer("Relatórios estendidos em desenvolvimento...", alert=True)
    elif data == b'admin_rates':
        await event.client.controller.get_system_settings()
        text = (
            "⚙️ **TAXAS GLOBAIS**\n\n"
            "Para alterar os valores do sistema, utilize os comandos abaixo:\n\n"
            "• `/set_base {valor}` - Taxa de partida\n"
            "• `/set_km {valor}` - Valor por quilômetro\n"
            "• `/set_min {valor}` - Valor por minuto de viagem\n"
            "• `/set_fee {valor}` - Taxa de serviço fixa\n"
            "• `/set_split {valor}` - % da plataforma\n"
        )
        await event.edit(text, buttons=[Button.inline("🔙 Voltar", b"admin_back")])
    elif data == b'admin_back':
        await admin_menu(event)
    elif data == b'admin_users':
        users = await event.client.controller.get_all_users(limit=5)
        text = "👥 **Últimos Usuários Cadastrados**\n\n"
        for u in users:
            role = "🚗 Driver" if u.get('type') == 'motorista' else "👤 Pass"
            text += f"• `{u['user_id']}` | {u['first_name']} | {role}\n"
        await event.edit(text, buttons=[Button.inline("🔙 Voltar", b"admin_back")])
    elif data == b'admin_payouts':
        requests = await event.client.controller.list_pending_payouts()
        if not requests:
            return await event.answer("✅ Não há pagamentos pendentes.", alert=True)
        text = "💰 **Solicitações de Saque Pendentes**\n\n"
        buttons = []
        for r in requests:
            text += (f"🆔 Pedido: `{r['id']}`\n👤 Driver ID: `{r['driver_id']}`\n"
                     f"💰 Valor: **R$ {r['amount']:.2f}**\n🔑 PIX: `{r['pix_key']}`\n"
                     f"--------------------------\n")
            buttons.append(
                [Button.inline(
                    f"✅ Confirmar Payout #{r['id']}", f"admin_confirm_payout_{r['id']}"
                )]
            )
        buttons.append([Button.inline("🔙 Voltar", b"admin_back")])
        await event.edit(text, buttons=buttons)
    elif data.startswith(b'admin_confirm_payout_'):
        request_id = int(data.decode().split('_')[-1])
        success, driver_user_id = await event.client.controller.confirm_payout(request_id)
        if success:
            await event.answer("💰 Payout confirmado com sucesso!", alert=True)
            await event.client.send_message(
                driver_user_id,
                "✅ **Seu pedido de saque foi PROCESSADO!**\nO dinheiro já foi enviado via PIX."
            )

            async def reload_payouts():
                requests = await event.client.controller.list_pending_payouts()
                if not requests:
                    return await event.answer("✅ Não há pagamentos pendentes.", alert=True)
                text = "💰 **Solicitações de Saque Pendentes**\n\n"
                buttons = []
                for r in requests:
                    text += (f"🆔 Pedido: `{r['id']}`\n👤 Driver ID: `{r['driver_id']}`\n"
                             f"💰 Valor: **R$ {r['amount']:.2f}**\n🔑 PIX: `{r['pix_key']}`\n"
                             f"--------------------------\n")
                    buttons.append(
                        [Button.inline(
                            f"✅ Confirmar Payout #{r['id']}", f"admin_confirm_payout_{r['id']}"
                        )]
                    )
                buttons.append([Button.inline("🔙 Voltar", b"admin_back")])
                await event.edit(text, buttons=buttons)

            await reload_payouts()
        else:
            await event.answer("❌ Erro ao confirmar payout.", alert=True)


@client.on(events.NewMessage(pattern='/set_(base|km|min|fee|split)'))
async def set_config(event):
    if not is_admin(event.sender_id): return
    cmd = event.pattern_match.group(1)
    try:
        val = float(event.text.split()[1].replace(',', '.'))
    except (IndexError, ValueError):
        return await event.respond(f"❌ Uso correto: `/set_{cmd} 1.50`")
    mapping = {
        'base': 'base_fare',
        'km': 'price_per_km',
        'min': 'price_per_min',
        'fee': 'service_fee',
        'split': 'default_platform_percentage'
    }
    field = mapping.get(cmd)
    await event.client.controller.update_system_settings(**{field: val})
    await event.respond(f"✅ Configuração `{cmd}` atualizada para `{val}`.")
