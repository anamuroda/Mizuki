from database.connection import SessionLocal
from database.models import TargetURL, ScrapingResult
from core.browser import MizukiBrowser
from parsers.extractor import extract_hybrid
from core.intelligence import forecast_price
from core.logger import logger
import asyncio

# Importa a função que criamos acima
from interface.discord_bot import send_discord_notification

async def job_routine():
    logger.info("⏰ Iniciando rotina de verificação...")
    db = SessionLocal()
    targets = db.query(TargetURL).filter(TargetURL.active == True).all()
    db.close()

    if not targets: 
        logger.info("Nenhum alvo ativo.")
        return

    browser = MizukiBrowser()
    
    # REMOVIDO: get_market_context() (Não existe no seu intelligence.py)

    for target in targets:
        try:
            logger.info(f"Escaneando: {target.url}")
            res = await browser.fetch_page(target.url)
            price, available, method = extract_hybrid(res['html'])
            
            if price > 0:
                # Salva histórico
                db = SessionLocal()
                
                # Se for o primeiro scan e o nome for genérico, tenta atualizar (opcional)
                if "Aguardando Scan" in target.product_name:
                    # Aqui você poderia adicionar lógica para pegar o <title>
                    pass 

                db.add(ScrapingResult(target_id=target.id, price=price, available=available, method=method))
                db.commit()
                db.close()
                
                # Inteligência
                ai_msg = forecast_price(target.id)

                # Lógica de Notificação
                should_notify = False
                
                # 1. Se tem meta de preço e atingiu
                if target.target_price and price <= target.target_price:
                    should_notify = True
                # 2. Se não tem meta (apenas monitoramento)
                elif not target.target_price:
                    should_notify = True
                
                # CORREÇÃO: Usar discord_channel_id em vez de discord_user_id
                if should_notify and target.discord_channel_id:
                    # Removemos o market_ctx pois ele não existe no intelligence.py atual
                    await send_discord_notification(target, price, ai_msg)

        except Exception as e:
            logger.error(f"Erro ao processar {target.url}: {e}")