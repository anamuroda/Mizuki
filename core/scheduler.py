from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database.connection import SessionLocal
from database.models import TargetURL, ScrapingResult
from core.browser import MizukiBrowser
from parsers.extractor import extract_hybrid
from core.intelligence import forecast_price
from interface.notifier import send_discord_alert
from core.logger import logger

async def job_routine():
    logger.info("⏰ Iniciando rotina das 10:00...")
    db = SessionLocal()
    targets = db.query(TargetURL).filter(TargetURL.active == True).all()
    db.close()

    browser = MizukiBrowser()

    for target in targets:
        try:
            res = await browser.fetch_page(target.url)
            price, available, method = extract_hybrid(res['html'])
            ai_msg = forecast_price(target.id)

            # Salva
            db = SessionLocal()
            db.add(ScrapingResult(target_id=target.id, price=price, available=available, method=method))
            db.commit()
            db.close()

            # (Pilar 3) Alertas Condicionais
            if available and price > 0:
                is_deal = False
                if not target.target_price: is_deal = True
                elif price <= target.target_price: is_deal = True
                
                if is_deal:
                    await send_discord_alert(target.product_name, target.url, price, ai_msg)
                    logger.info(f"✅ Notificação enviada para {target.product_name}")
        
        except Exception as e:
            logger.error(f"Erro no job: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # (Pilar 4) Roda todo dia às 10:00 da manhã
    scheduler.add_job(job_routine, CronTrigger(hour=10, minute=0))
    scheduler.start()
    return scheduler