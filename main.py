import os
import asyncio
from dotenv import load_dotenv
from interface.discord_bot import bot
from core.scheduler import job_routine
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from core.logger import logger

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

@bot.event
async def on_ready():
    # Isso roda assim que o bot conecta no Discord
    logger.info(f'🤖 Mizuki Bot conectado! ID: {bot.user.id}')
    
    scheduler = AsyncIOScheduler()
    
    # Roda a cada 10 minutos (ajuste conforme necessário)
    scheduler.add_job(job_routine, 'interval', minutes=10)
    # Ou use CronTrigger(hour=10) para rodar todo dia as 10h
    
    scheduler.start()
    logger.info("⏳ Agendador iniciado.")

if __name__ == "__main__":
    if not TOKEN:
        logger.error("❌ Token do Discord não encontrado no .env")
    else:
        print("=== 🎌 INICIANDO MIZUKI BOT 🎌 ===")
        bot.run(TOKEN)