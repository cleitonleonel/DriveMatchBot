from telethon import events, Button
from smartbot.utils.handler import ClientHandler
from smartbot.config import ADMIN_IDS

client = ClientHandler()


def is_admin(sender_id):
    return sender_id in ADMIN_IDS


async def safe_edit_or_respond(event, text, buttons=None):
    try:
        if isinstance(event, events.CallbackQuery.Event) or (hasattr(event, 'data') and event.data):
            await event.edit(text, buttons=buttons)
        else:
            await event.respond(text, buttons=buttons)
    except Exception:
        try:
            await event.respond(text, buttons=buttons)
        except Exception:
            pass


async def render_admin_menu(event):
    sender_id = event.sender_id
    if not is_admin(sender_id):
        return

    stats = await event.client.controller.get_admin_stats()
    settings = await event.client.controller.get_system_settings()

    text = (
        "👑 **PAINEL ADMINISTRATIVO - DRIVEMATCH**\n\n"
        f"👥 **Usuários Registrados:** {stats['users_count']} __({stats['drivers_count']} motoristas)__\n"
        f"🚕 **Viagens Totais:** {stats['travels_count']}\n\n"
        "📊 **FINANCEIRO ACUMULADO**\n"
        f"💰 Total Bruto: **R$ {stats['revenue_total']:.2f}**\n"
        f"💎 Plataforma: **R$ {stats['revenue_platform']:.2f}**\n"
        f"🤝 Motoristas: **R$ {stats['revenue_drivers']:.2f}**\n\n"
        "⚙️ **TAXAS DO SISTEMA**\n"
        f"📍 Base: `R$ {settings['base_fare']:.2f}` | KM: `R$ {settings['price_per_km']:.2f}`\n"
        f"⏱ Min: `R$ {settings['price_per_min']:.2f}` | Fee: `R$ {settings['service_fee']:.2f}`\n"
        f"📈 Taxa Padrão: **{settings['default_platform_percentage']}%**\n"
    )

    buttons = [
        [Button.inline("📊 Relatórios Detalhados", b"admin_metrics")],
        [Button.inline("💰 Pagamentos Pendentes", b"admin_payouts")],
        [Button.inline("⚙️ Editar Taxas Globais", b"admin_rates")],
        [Button.inline("👥 Gerenciar Usuários", b"admin_users_page_0")],
        [Button.inline("🔙 Fechar Painel", b"admin_close")]
    ]

    await safe_edit_or_respond(event, text, buttons)


async def render_user_detail(event, target_id, from_page=0):
    user = await event.client.controller.check_user_exists(target_id)
    if not user:
        text = f"❌ Usuário `{target_id}` não encontrado."
        buttons = [[Button.inline("🔙 Voltar aos Usuários", f"admin_users_page_{from_page}".encode())]]
        return await safe_edit_or_respond(event, text, buttons)

    role = "🚗 Motorista" if user.get('type') == 'motorista' else "👤 Passageiro"
    status_icon = "🟢 Ativo" if user.get('is_active') else "🔴 Inativo"
    text = (
        f"👤 **DETALHES DO USUÁRIO**\n\n"
        f"• **ID Telegram:** `{user['user_id']}`\n"
        f"• **Nome:** {user.get('first_name', '')} {user.get('last_name', '') or ''}\n"
        f"• **Username:** @{user.get('username') or 'N/A'}\n"
        f"• **Tipo:** {role}\n"
        f"• **Status:** {status_icon}\n"
        f"• **Avaliação:** ⭐ `{user.get('average_rating', 0.0):.1f}` ({user.get('num_ratings', 0)} avaliações)\n"
        f"• **Saldo:** R$ {user.get('balance', 0.0):.2f}\n"
        f"• **Total de Viagens:** {user.get('qtd_travels', 0)}\n"
    )
    toggle_label = "🔴 Desativar Usuário" if user.get('is_active') else "🟢 Ativar Usuário"
    buttons = [
        [Button.inline(toggle_label, f"admin_toggle_detail_{user['user_id']}_{from_page}")],
        [Button.inline("🔙 Voltar aos Usuários", f"admin_users_page_{from_page}".encode()), Button.inline("🏠 Menu Principal", b"admin_back")]
    ]
    await safe_edit_or_respond(event, text, buttons)


@client.on(events.NewMessage(pattern='/admin'))
async def admin_menu(event):
    await render_admin_menu(event)


@client.on(events.CallbackQuery(pattern=b'admin_'))
async def admin_callbacks(event):
    sender_id = event.sender_id
    if not is_admin(sender_id):
        return await event.answer("Acesso negado.", alert=True)

    data = event.data

    if data == b'admin_close':
        try:
            await event.delete()
        except Exception:
            pass

    elif data == b'admin_metrics':
        metrics = await event.client.controller.get_financial_metrics()
        stats = await event.client.controller.get_admin_stats()
        text = (
            "📊 **RELATÓRIO FINANCEIRO E MÉTRICAS**\n\n"
            f"📈 Total Geral Bruto: **R$ {stats['revenue_total']:.2f}**\n"
            f"💎 Lucro da Plataforma: **R$ {stats['revenue_platform']:.2f}**\n"
            f"🤝 Repasse aos Motoristas: **R$ {stats['revenue_drivers']:.2f}**\n"
            f"🚕 Total de Viagens: **{stats['travels_count']}**\n\n"
            "🗓 **Desempenho nos últimos 7 dias:**\n"
        )
        if not metrics:
            text += "_Nenhuma viagem concluída nos últimos 7 dias._\n"
        else:
            for m in metrics:
                text += f"• `{m['date']}` | Bruto: **R$ {m['total']:.2f}** | Plataforma: **R$ {m['platform']:.2f}**\n"

        buttons = [[Button.inline("🔙 Voltar", b"admin_back")]]
        await safe_edit_or_respond(event, text, buttons)

    elif data == b'admin_rates':
        settings = await event.client.controller.get_system_settings()
        text = (
            "⚙️ **CONFIGURAÇÃO DE TAXAS GLOBAIS**\n\n"
            f"📍 **Taxa Base (Partida):** `R$ {settings['base_fare']:.2f}`\n"
            f"🚗 **Valor por KM:** `R$ {settings['price_per_km']:.2f}`\n"
            f"⏱ **Valor por Minuto:** `R$ {settings['price_per_min']:.2f}`\n"
            f"🛡 **Taxa de Serviço Fixa:** `R$ {settings['service_fee']:.2f}`\n"
            f"📈 **Porcentagem da Plataforma:** `{settings['default_platform_percentage']}%`\n\n"
            "Para alterar qualquer valor, envie o comando no chat:\n"
            "• `/set_base 5.00` - Altera taxa base\n"
            "• `/set_km 2.00` - Altera valor/km\n"
            "• `/set_min 0.50` - Altera valor/minuto\n"
            "• `/set_fee 1.00` - Altera taxa fixa\n"
            "• `/set_split 20` - Altera % da plataforma\n"
        )
        buttons = [[Button.inline("🔙 Voltar", b"admin_back")]]
        await safe_edit_or_respond(event, text, buttons)

    elif data == b'admin_back':
        await render_admin_menu(event)

    elif data.startswith(b'admin_users_page_') or data == b'admin_users':
        try:
            page = int(data.decode().split('_')[-1])
        except (ValueError, IndexError):
            page = 0

        limit = 5
        offset = page * limit

        stats = await event.client.controller.get_admin_stats()
        total_users = stats.get('users_count', 0)

        users = await event.client.controller.get_all_users(limit=limit, offset=offset)

        text = f"👥 **GERENCIAMENTO DE USUÁRIOS (Página {page + 1})**\n"
        text += f"Total de usuários cadastrados: **{total_users}**\n\n"

        buttons = []
        if not users:
            text += "_Nenhum usuário cadastrado nesta página._\n"
        else:
            for u in users:
                role = "🚗 Motorista" if u.get('type') == 'motorista' else "👤 Passageiro"
                status_icon = "🟢 Ativo" if u.get('is_active') else "🔴 Inativo"
                name = u.get('first_name') or u.get('username') or f"User {u['user_id']}"
                text += (
                    f"🆔 `{u['user_id']}` | **{name}**\n"
                    f"   Tipo: {role} | Status: {status_icon}\n"
                    f"   Viagens: {u.get('qtd_travels', 0)} | Saldo: R$ {u.get('balance', 0.0):.2f}\n"
                    "-----------------------------------\n"
                )
                toggle_label = "🔴 Desativar" if u.get('is_active') else "🟢 Ativar"
                buttons.append([
                    Button.inline(f"🔍 {name[:12]}", f"admin_user_detail_{u['user_id']}_{page}"),
                    Button.inline(f"{toggle_label}", f"admin_toggle_{u['user_id']}_{page}")
                ])

        nav_buttons = []
        if page > 0:
            nav_buttons.append(Button.inline("◀️ Anterior", f"admin_users_page_{page - 1}"))
        if (page + 1) * limit < total_users:
            nav_buttons.append(Button.inline("Próximo ▶️", f"admin_users_page_{page + 1}"))

        if nav_buttons:
            buttons.append(nav_buttons)

        buttons.append([Button.inline("🔙 Voltar ao Painel", b"admin_back")])
        await safe_edit_or_respond(event, text, buttons)

    elif data.startswith(b'admin_user_detail_'):
        parts = data.decode().split('_')
        user_id = int(parts[3])
        page = int(parts[4]) if len(parts) > 4 else 0
        await render_user_detail(event, user_id, from_page=page)

    elif data.startswith(b'admin_toggle_'):
        is_detail_view = data.startswith(b'admin_toggle_detail_')
        parts = data.decode().split('_')
        idx = 3 if is_detail_view else 2
        user_id = int(parts[idx])
        page = int(parts[idx + 1]) if len(parts) > idx + 1 else 0

        success, new_state = await event.client.controller.toggle_user_active(user_id)
        if success:
            state_label = "ATIVADO" if new_state else "DESATIVADO"
            try:
                await event.answer(f"✅ Usuário {user_id} {state_label} com sucesso!", alert=False)
            except Exception:
                pass
        else:
            try:
                await event.answer("❌ Erro ao alterar status do usuário.", alert=True)
            except Exception:
                pass

        if is_detail_view:
            await render_user_detail(event, user_id, from_page=page)
        else:
            event.data = f"admin_users_page_{page}".encode()
            await admin_callbacks(event)

    elif data == b'admin_payouts':
        requests = await event.client.controller.list_pending_payouts()
        text = "💰 **SOLICITAÇÕES DE SAQUE PENDENTES**\n\n"
        buttons = []
        if not requests:
            text += "✅ _Não há solicitações de saque pendentes no momento._\n"
        else:
            for r in requests:
                text += (f"🆔 Pedido #{r['id']}\n"
                         f"👤 Driver UserID: `{r['driver_id']}`\n"
                         f"💰 Valor: **R$ {r['amount']:.2f}**\n"
                         f"🔑 Chave PIX: `{r['pix_key']}`\n"
                         f"--------------------------\n")
                buttons.append(
                    [Button.inline(
                        f"✅ Confirmar Payout #{r['id']}", f"admin_confirm_payout_{r['id']}"
                    )]
                )
        buttons.append([Button.inline("🔙 Voltar ao Painel", b"admin_back")])
        await safe_edit_or_respond(event, text, buttons)

    elif data.startswith(b'admin_confirm_payout_'):
        request_id = int(data.decode().split('_')[-1])
        success, driver_user_id = await event.client.controller.confirm_payout(request_id)
        if success:
            try:
                await event.answer("💰 Payout confirmado com sucesso!", alert=False)
            except Exception:
                pass

            if driver_user_id:
                try:
                    await event.client.send_message(
                        driver_user_id,
                        "✅ **Seu pedido de saque foi PROCESSADO!**\nO valor foi transferido via PIX."
                    )
                except Exception:
                    pass

            event.data = b'admin_payouts'
            await admin_callbacks(event)
        else:
            try:
                await event.answer("❌ Erro ao confirmar payout.", alert=True)
            except Exception:
                pass


@client.on(events.NewMessage(pattern='/set_(base|km|min|fee|split)'))
async def set_config(event):
    if not is_admin(event.sender_id):
        return
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


@client.on(events.NewMessage(pattern='/admin_user'))
async def inspect_user(event):
    if not is_admin(event.sender_id):
        return
    try:
        target_id = int(event.text.split()[1])
    except (IndexError, ValueError):
        return await event.respond("❌ Uso correto: `/admin_user 123456789`")

    await render_user_detail(event, target_id, from_page=0)
