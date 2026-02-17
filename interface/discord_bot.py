# Arquivo: interface/discord_bot.py
import discord
from discord import app_commands
from discord.ext import commands
from database.connection import SessionLocal
from database.models import TargetURL
from sqlalchemy.exc import IntegrityError

# Configuração de Permissões (Intents)
intents = discord.Intents.default()
intents.message_content = True

# Criamos o Bot
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Mizuki Bot Online! Logada como {bot.user}')
    try:
        # Sincroniza os comandos Slash (/) com o Discord
        synced = await bot.tree.sync()
        print(f"🌲 Comandos sincronizados: {len(synced)}")
    except Exception as e:
        print(f"❌ Erro ao sincronizar comandos: {e}")

# --- COMANDO: MONITORAR ---
@bot.tree.command(name="monitorar", description="Adiciona um produto à lista de vigilância")
@app_commands.describe(url="Link do produto", preco_alvo="Preço máximo que você quer pagar (0 para qualquer preço)")
async def monitorar(interaction: discord.Interaction, url: str, preco_alvo: float = 0.0):
    # Defer responde ao Discord "estou processando" para evitar timeout
    await interaction.response.defer()

    db = SessionLocal()
    try:
        # Cria o registro no banco
        target = TargetURL(
            url=url,
            product_name="Produto (Aguardando Scan...)", # Será atualizado no primeiro scrape
            target_price=preco_alvo,
            discord_channel_id=interaction.channel_id # Salva o ID do canal atual
        )
        db.add(target)
        db.commit()

        # Cria um Embed bonito de confirmação
        embed = discord.Embed(
            title="🔭 Monitoramento Iniciado",
            description=f"A Mizuki está de olho neste link para você.",
            color=discord.Color.from_rgb(255, 105, 180) # Rosa Mizuki
        )
        embed.add_field(name="Alvo de Preço", value=f"R$ {preco_alvo:.2f}" if preco_alvo > 0 else "Qualquer valor", inline=True)
        embed.add_field(name="Canal de Alerta", value=f"<#{interaction.channel_id}>", inline=True)
        
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"❌ Ocorreu um erro ao salvar: {str(e)}")
    finally:
        db.close()

# --- COMANDO: LISTA ---
@bot.tree.command(name="lista", description="Mostra o que está sendo monitorado neste canal")
async def lista(interaction: discord.Interaction):
    db = SessionLocal()
    # Busca apenas produtos cadastrados NESTE canal específico
    targets = db.query(TargetURL).filter(TargetURL.discord_channel_id == interaction.channel_id).all()
    db.close()

    if not targets:
        await interaction.response.send_message("📭 Não estou monitorando nada neste canal.", ephemeral=True)
        return

    embed = discord.Embed(title=f"📋 Lista de Vigilância ({len(targets)})", color=discord.Color.purple())
    
    description_text = ""
    for t in targets:
        price_txt = f"R$ {t.target_price:.2f}" if t.target_price else "Qualquer"
        description_text += f"**[{t.product_name}]({t.url})**\n🎯 Meta: {price_txt}\n\n"
    
    # Discord tem limite de 4096 caracteres na descrição, cuidado com listas gigantes
    if len(description_text) > 4000:
        description_text = description_text[:4000] + "..."
        
    embed.description = description_text
    await interaction.response.send_message(embed=embed)