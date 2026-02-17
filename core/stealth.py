from playwright.async_api import Page

async def stealth_async(page: Page):
    """
    Aplica patches de evasão manualmente, sem depender da biblioteca antiga.
    """
    await page.add_init_script("""
        // 1. mascarar o eebdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });

        // 2. mascarar o chrome/headless
        window.chrome = {
            runtime: {},
            // adicione mais propriedades se necessário
        };

        // 3. mascarar permissões
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );

        // 4. mascarar pplugins (simula que tem plugins instalados)
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });

        // 5. mascarar linguagens
        Object.defineProperty(navigator, 'languages', {
            get: () => ['pt-BR', 'pt', 'en-US', 'en'],
        });
    """)