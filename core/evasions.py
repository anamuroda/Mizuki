async def clean_popups_and_overlays(page):
    """
    Injeta js para remover elementos obstrutivos baseados em Z-Index
    """
    await page.evaluate("""() => {
        const elements = document.querySelectorAll('*');
        for (let el of elements) {
            const style = window.getComputedStyle(el);
            const zIndex = parseInt(style.zIndex);
            
            // remove elementos com z-index absurdo (geralmente modais)
            if (!isNaN(zIndex) && zIndex > 999) {
                // Tenta ser cauteloso: só remove se parecer de popup
                if (el.innerHTML.includes('newsletter') || 
                    el.innerHTML.includes('assine') || 
                    el.innerHTML.includes('cupom') ||
                    el.className.includes('modal') ||
                    el.className.includes('popup')) {
                    
                    el.remove();
                    console.log('Mizuki: Popup removido.');
                }
            }
        }
    }""")