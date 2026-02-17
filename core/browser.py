import asyncio
import random
import os
from playwright.async_api import async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from fake_useragent import UserAgent
from .stealth import stealth_async
from .logger import logger
import logging

# (Pilar 1) Proxy Rotation: Configure no .env
PROXY_SERVER = os.getenv("PROXY_SERVER", None) 

class MizukiBrowser:
    def __init__(self):
        self.ua = UserAgent()

    async def human_behavior(self, page):
        """(Pilar 1) Simulação de Comportamento Humano"""
        # Movimento de mouse (Curvas de Bézier simuladas)
        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
        
        # Delay aleatório (nunca exato)
        await asyncio.sleep(random.uniform(0.8, 1.5))
        
        # Scroll "Preguiçoso"
        for _ in range(random.randint(2, 5)):
            await page.mouse.wheel(0, random.randint(300, 700))
            await asyncio.sleep(random.uniform(1.0, 3.0))
            # Sobe um pouco (comportamento de leitura)
            if random.random() < 0.3:
                await page.mouse.wheel(0, -random.randint(50, 200))

    # (Pilar 4) Retry Logic: Tenta 3 vezes com espera exponencial
    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def fetch_page(self, url):
        async with async_playwright() as p:
            launch_args = {
                "headless": False,  # Mude para True se não quiser ver a janela
                "args": [
                    "--disable-blink-features=AutomationControlled", 
                    "--no-sandbox", 
                    "--disable-infobars",
                    "--window-size=1920,1080"
                ]
            }
            
            if PROXY_SERVER:
                launch_args["proxy"] = {"server": PROXY_SERVER}

            browser = await p.chromium.launch(**launch_args)
            
            # (Pilar 1) Rotação de Fingerprint (UA, Timezone, Locale)
            random_ua = self.ua.random
            context = await browser.new_context(
                user_agent=random_ua,
                viewport={'width': 1920, 'height': 1080},
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
                permissions=['geolocation']
            )
            
            page = await context.new_page()
            
            # (Pilar 1) Stealth Manual (WebGL, Canvas, etc)
            await stealth_async(page)

            try:
                logger.info(f"Navegando para: {url}...")
                await page.goto(url, timeout=60000, wait_until='domcontentloaded')
                
                await self.human_behavior(page)
                
                # (Pilar 1) Lógica de Captcha (Placeholder)
                if "captcha" in page.url or await page.locator("iframe[src*='captcha']").count() > 0:
                    logger.warning("Captcha detectado! Tentando resolver...")
                    # Aqui entraria a integração com 2Captcha/CapSolver
                    # await solve_captcha(page)
                    await asyncio.sleep(5) 

                content = await page.content()
                return {"status": "success", "html": content}

            except Exception as e:
                # (Pilar 4) Screenshot de Erro
                filename = f"screenshots/error_{random.randint(1000,9999)}.png"
                await page.screenshot(path=filename)
                logger.error(f"Erro ao acessar {url}. Screenshot salvo em {filename}. Erro: {e}")
                raise e 
            
            finally:
                await browser.close()