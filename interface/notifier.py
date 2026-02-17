import aiohttp
import os

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")

async def send_discord_alert(product_name, url, price, target_price, ai_msg, market_ctx):
    """
    (1a) Envia notificação rica para o Discord.
    """
    if not DISCORD_WEBHOOK: return

    # Cor: Verde se estiver abaixo do alvo, Amarelo se for só monitoramento
    color = 0x2ecc71 if (target_price and price <= target_price) else 0xf1c40f
    
    embed = {
        "title": f"Preço Encontrado: {product_name or 'Produto'}",
        "description": f"**R$ {price:.2f}**\n[Ir para loja]({url})",
        "color": color,
        "fields": [
            {"name": "🎯 Preço Alvo", "value": f"R$ {target_price:.2f}" if target_price else "Não definido", "inline": True},
            {"name": "🤖 Previsão IA", "value": ai_msg or "Sem dados", "inline": True},
            {"name": "📅 Mercado", "value": market_ctx, "inline": False}
        ],
        "footer": {"text": "Mizuki Intelligence System"}
    }

    async with aiohttp.ClientSession() as session:
        await session.post(DISCORD_WEBHOOK, json={"embeds": [embed]})