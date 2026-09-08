from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    # Cria o navegador visível e a página
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Todos os comandos do scraper devem ficar identados dentro do bloco "with"
    page.goto("https://www.dfimoveis.com.br/lancamento/df/todos/imoveis")

    # Espera ao menos um card carregar na tela antes de ler
    page.wait_for_selector(".imovel-info")

    for card in page.locator(".imovel-info").all():
        # Usar 'card.locator' para buscar estritamente dentro deste anúncio
        titulo1_loc = card.locator('h2[itemprop="name"]')
        titulo1 = titulo1_loc.inner_text() if titulo1_loc.count() > 0 else "N/A"
        
        subtitulo_loc = card.locator('h3.web-ellipse-view')
        subtitulo = subtitulo_loc.inner_text() if subtitulo_loc.count() > 0 else "N/A"
        
        preco_loc = card.locator("[itemprop='price']")
        preco = preco_loc.inner_text() if preco_loc.count() > 0 else "N/A"
        
        # Locator direto das especificações
        info = card.locator(".imovel-feature .rounded-pill")
        
        # Validação de existência antes de extrair
        tamanho = info.nth(0).inner_text() if info.count() > 0 else "N/A"
        quartos = info.nth(1).inner_text() if info.count() > 1 else "N/A"
        plantas = info.nth(2).inner_text() if info.count() > 2 else "N/A"
        if tamanho == "0 plantas":
            tamanho = "N/A"
            plantas = "0 plantas"

        print(
            f"Endereço, Bairro e Cidade: {titulo1}\n"
            f"Condominio: {subtitulo}\n"
            f"Preço: {preco}\n"
            f"Tamanho: {tamanho}\n"
            f"Quartos: {quartos}\n"
            f"Plantas: {plantas}\n"
            + "-" * 40
        )
        
    page.wait_for_timeout(5000)
    browser.close()