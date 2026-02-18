import os
import asyncio
from dotenv import load_dotenv
from interface.discord_bot import bot
from core.scheduler import job_routine
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.logger import logger

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Variável de controle para garantir que o setup rode apenas uma vez
# (evita duplicidade se o bot reconectar ao Discord)
bot_ready_flag = False

@bot.event
async def on_ready():
    global bot_ready_flag
    
    # Se já tiver rodado o setup, ignora (reconexão)
    if bot_ready_flag:
        return
    
    bot_ready_flag = True
    logger.info(f'🤖 Mizuki Bot conectado! ID: {bot.user.id}')
    
    # 1. Configura o Agendador (para rodar periodicamente no futuro)
    scheduler = AsyncIOScheduler()
    # Aumentei para 30 minutos para dar tempo do ciclo anterior terminar, se houver muitos produtos
    scheduler.add_job(job_routine, 'interval', minutes=30)
    scheduler.start()
    logger.info("⏳ Agendador de tarefas iniciado (Ciclo: 30 min).")

    # 2. FUNCIONALIDADE NOVA: Scraping Imediato no Startup
    logger.info("🚀 Detectada inicialização do sistema. Iniciando varredura completa de dados agora...")
    
    # Usamos create_task para rodar em "segundo plano" e não travar o bot de responder comandos
    asyncio.create_task(run_startup_scan())

async def run_startup_scan():
    """Função wrapper para tratar erros durante o scan inicial"""
    try:
        await job_routine()
        logger.info("✅ Varredura inicial de startup concluída com sucesso.")
    except Exception as e:
        logger.error(f"❌ Falha crítica na varredura inicial: {e}")

if __name__ == "__main__":
    if not TOKEN:
        logger.error("❌ Token do Discord não encontrado no arquivo .env")
    else:
        print("=== 🎌 INICIANDO MIZUKI BOT 🎌 ===")
        bot.run(TOKEN)