from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database.connection import SessionLocal
from database.models import TargetURL, ScrapingResult
from core.browser import MizukiBrowser
from parsers.extractor import extract_hybrid
from core.intelligence import forecast_price, get_market_context
from core.logger import logger

# Importa a função de notificação do Bot
from interface.discord_bot import send_discord_notification

async def job_routine():
    logger.info("⏰ Iniciando rotina de verificação...")
    db = SessionLocal()
    targets = db.query(TargetURL).filter(TargetURL.active == True).all()
    db.close()

    if not targets: return

    browser = MizukiBrowser()
    market_ctx = get_market_context()

    for target in targets:
        try:
            res = await browser.fetch_page(target.url)
            price, available, method = extract_hybrid(res['html'])
            
            # Só processa se tiver preço válido
            if price > 0:
                # Salva histórico
                db = SessionLocal()
                db.add(ScrapingResult(target_id=target.id, price=price, available=available, method=method))
                db.commit()
                db.close()
                
                # Inteligência
                ai_msg = forecast_price(target.id)

                # Lógica de Notificação Personalizada
                should_notify = False
                
                # 1. Se tem meta de preço e atingiu
                if target.target_price and price <= target.target_price:
                    should_notify = True
                # 2. Se não tem meta (usuário quer apenas monitorar tudo)
                elif not target.target_price:
                    should_notify = True
                
                # Se o usuário é do Discord, manda notificação rica
                if should_notify and target.discord_user_id:
                    # Precisamos garantir que isso rode no loop do Bot
                    await send_discord_notification(target, price, ai_msg, market_ctx)

        except Exception as e:
            logger.error(f"Erro ao processar {target.url}: {e}")

