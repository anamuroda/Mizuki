# core/scheduler.py
from database.connection import SessionLocal
from database.models import Product, PriceHistory, Category, AvailabilityStatus
from core.browser import MizukiBrowser
from parsers.extractor import extract_hybrid
from core.normalization import classify_product
from core.intelligence import forecast_price
from core.logger import logger
from interface.discord_bot import send_discord_notification
import asyncio

async def job_routine():
    logger.info("⏰ Iniciando rotina de inteligência...")
    db = SessionLocal()
    
    # Busca produtos ativos
    products = db.query(Product).filter(Product.active == True).all()
    
    if not products: 
        logger.info("Nenhum produto para monitorar.")
        db.close()
        return

    browser = MizukiBrowser()

    for product in products:
        try:
            logger.info(f"Analisando: {product.url}")
            res = await browser.fetch_page(product.url)
            
            # Extração
            price, available, method = extract_hybrid(res['html'])
            
            # Atualiza dados em tempo real no Produto
            product.price_current = price
            product.availability_status = AvailabilityStatus.IN_STOCK if available else AvailabilityStatus.OUT_OF_STOCK
            
            # (Ponto 3) Auto-Correção Semântica
            # Se o nome ainda for o placeholder, tenta extrair do HTML (ex: Title) e classificar
            if product.product_name == "Aguardando Scan...":
                # Lógica simples para extrair título (pode melhorar no extractor.py)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(res['html'], 'html.parser')
                title = soup.title.string.strip() if soup.title else "Produto Desconhecido"
                product.product_name = title
                
                # Classifica Categoria automaticamente
                cat_name = classify_product(title)
                category = db.query(Category).filter_by(name=cat_name).first()
                if category:
                    product.category_id = category.id
                    logger.info(f"🧬 Classificado como: {cat_name}")

            # (Ponto 6) Grava Histórico (Série Temporal)
            history_entry = PriceHistory(
                product_id=product.id,
                price=price,
                availability=available
            )
            db.add(history_entry)
            
            # Notificação (Mantendo compatibilidade)
            should_notify = False
            if product.target_price and price > 0 and price <= product.target_price:
                should_notify = True
            
            if should_notify and product.discord_channel_id:
                ai_msg = forecast_price(product.id) # Nota: forecast_price precisará de ajuste leve para ler PriceHistory
                await send_discord_notification(product, price, ai_msg)

            db.commit()

        except Exception as e:
            logger.error(f"Erro ao processar {product.url}: {e}")
            db.rollback()
    
    db.close()