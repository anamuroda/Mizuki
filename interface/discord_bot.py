import discord
from discord import app_commands
from discord.ext import commands
from database.connection import SessionLocal
from database.models import TargetURL
import logging

# Configuração de Logs
logger = logging.getLogger("Mizuki")

# Configuração de Permissões (Intents)
intents = discord.Intents.default()
intents.message_content = True

# Criamos o Bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f'✅ Mizuki Bot Online! Logada como {bot.user}')
    # NOTA: Removemos o sync automático do on_ready para evitar rate-limit
    # Vamos usar o comando !sincronizar manualmente na primeira vez.
    print("🤖 Bot pronto! Digite '!sincronizar' no chat do Discord para atualizar o menu.")

# --- COMANDO SECRETO PARA LIMPAR O MENU ---
@bot.command()
async def sincronizar(ctx):
    """Digitar !sincronizar no chat força a atualização do menu /"""
    await ctx.send("🔄 Sincronizando comandos... isso pode levar alguns segundos.")
    try:
        # Limpa tudo e envia os novos
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Sucesso! {len(synced)} comandos sincronizados: {', '.join([c.name for c in synced])}.\n\n⚠️ Se o menu antigo ainda aparecer, feche e abra o Discord (Ctrl+R).")
    except Exception as e:
        await ctx.send(f"❌ Erro ao sincronizar: {e}")

# --- FUNÇÃO DE NOTIFICAÇÃO ---
async def send_discord_notification(target, price, ai_msg):
    """Envia o Embed rico para o canal configurado."""
    try:
        if not target.discord_channel_id: return

        channel = bot.get_channel(int(target.discord_channel_id))
        if not channel: return

        is_deal = target.target_price and price <= target.target_price
        color = discord.Color.green() if is_deal else discord.Color.gold()
        title = "🚨 Preço Atingido!" if is_deal else "🔔 Atualização de Preço"

        embed = discord.Embed(title=title, description=f"**[{target.product_name}]({target.url})**", color=color)
        embed.add_field(name="💰 Preço Atual", value=f"**R$ {price:.2f}**", inline=True)
        if target.target_price:
            embed.add_field(name="🎯 Seu Alvo", value=f"R$ {target.target_price:.2f}", inline=True)
        embed.add_field(name="🧠 IA Mizuki", value=f"_{ai_msg}_", inline=False)
        embed.set_footer(text=f"Mizuki Intelligence System")
        
        await channel.send(embed=embed)
    except Exception as e:
        logger.error(f"Erro ao enviar msg Discord: {e}")

# --- COMANDOS SLASH (NOVOS) ---
@bot.tree.command(name="monitorar", description="Começa a vigiar um produto")
@app_commands.describe(url="Cole o link aqui", preco_alvo="Preço máximo (opcional)")
async def monitorar(interaction: discord.Interaction, url: str, preco_alvo: float = 0.0):
    await interaction.response.defer()
    
    # Validação simples de URL
    if "http" not in url:
        await interaction.followup.send("❌ Isso não parece um link válido.")
        return

    db = SessionLocal()
    try:
        target = TargetURL(
            url=url,
            product_name="Produto (Aguardando Scan...)", 
            target_price=preco_alvo,
            discord_channel_id=interaction.channel_id
        )
        db.add(target)
        db.commit()

        embed = discord.Embed(
            title="🔭 Monitoramento Iniciado",
            description="Vou te avisar aqui quando o preço mudar.",
            color=discord.Color.from_rgb(255, 105, 180)
        )
        embed.add_field(name="Alvo", value=f"R$ {preco_alvo:.2f}" if preco_alvo > 0 else "Qualquer", inline=True)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Erro: {str(e)}")
    finally:
        db.close()

@bot.tree.command(name="lista", description="Ver produtos monitorados neste canal")
async def lista(interaction: discord.Interaction):
    db = SessionLocal()
    targets = db.query(TargetURL).filter(TargetURL.discord_channel_id == interaction.channel_id).all()
    db.close()

    if not targets:
        await interaction.response.send_message("📭 Nada sendo monitorado aqui.", ephemeral=True)
        return

    desc = ""
    for t in targets:
        p_txt = f"R$ {t.target_price:.2f}" if t.target_price else "Qualquer"
        desc += f"• **{t.product_name}** (Meta: {p_txt})\n[Link]({t.url})\n\n"
    
    embed = discord.Embed(title=f"📋 Lista ({len(targets)})", description=desc[:4000], color=discord.Color.purple())
    await interaction.response.send_message(embed=embed)