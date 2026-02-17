import asyncio
import random
from playwright.async_api import async_playwright
from .stealth import stealth_async
from .evasions import clean_popups_and_overlays

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

class MizukiBrowser:
    async def get_page_content(self, url):
        async with async_playwright() as p:
            # Mantive headless=False para você ver acontecendo (debug)
            # Mude para True quando estiver confiante
            browser = await p.chromium.launch(
                headless=False, 
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
            )
            
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1366, 'height': 768},
                locale='pt-BR'
            )
            
            page = await context.new_page()
            await stealth_async(page)

            try:
                print(f"--> Navegando: {url}")
                await page.goto(url, timeout=90000, wait_until='domcontentloaded')
                
                # Scroll lento para ativar Lazy Loading (Imagens e Preços dinâmicos)
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 500)")
                    await asyncio.sleep(1)
                
                # Tenta esperar por SELETORES DE PREÇO comuns em farmácias
                # Isso força o bot a esperar até que o preço apareça na tela
                try:
                    # Lista de seletores genéricos de preço usados em e-commerces
                    await page.wait_for_selector(
                        "div[class*='price'], span[class*='price'], p[class*='price'], .product-price", 
                        timeout=5000, 
                        state='visible'
                    )
                except:
                    print("⚠️ Aviso: Elemento de preço explícito não detectado via CSS (tentando extração bruta)")

                await clean_popups_and_overlays(page)
                
                # Screenshot de Debug (Fundamental para ver o que deu errado)
                await page.screenshot(path=f"debug_{random.randint(100,999)}.png")

                content = await page.content()
                return {"status": "success", "html": content, "url": url}

            except Exception as e:
                print(f"X-- Erro crítico em {url}: {e}")
                return {"status": "error", "html": str(e), "url": url}
            
            finally:
                await browser.close()