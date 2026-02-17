import asyncio
import os
from interface.discord_bot import bot, run_discord_bot
from core.scheduler import job_routine
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from core.logger import logger
from dotenv import load_dotenv

load_dotenv()

# --- INTEGRAÇÃO BOT + SCHEDULER ---

@bot.event
async def on_ready():
    logger.info(f'🤖 Mizuki Bot conectado como {bot.user} (ID: {bot.user.id})')
    
    # Inicia o Agendador dentro do loop do Discord
    scheduler = AsyncIOScheduler()
    
    # Configura para rodar às 10:00 AM
    scheduler.add_job(job_routine, CronTrigger(hour=10, minute=0))
    
    # DICA: Descomente a linha abaixo para testar AGORA (roda a cada 2 minutos)
    # scheduler.add_job(job_routine, 'interval', minutes=2)
    
    scheduler.start()
    logger.info("⏳ Agendador sincronizado com o loop do Discord.")

if __name__ == "__main__":
    print("=== 🎌 INICIANDO MIZUKI BOT 🎌 ===")
    run_discord_bot()