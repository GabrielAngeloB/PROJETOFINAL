from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from db import init_db, marcar_imoveis_vendido, salvar_lote_bronze

# Listas ordenadas do maior para o menor para evitar sobreposição (Ex: achar "CASA" dentro de "CASA CONDOMINIO")
TIPOS_IMOVEL = [
    "PONTO COMERCIAL", "CASA CONDOMINIO", "HOTEL-FLAT", "LOTEAMENTO", "APARTAMENTO", 
    "TERRENO", "GALPAO", "GARAGEM", "KITNET", "PREDIO", "RURAL", "AREA", "CASA", 
    "LOJA", "LOTE", "SALA"
]

LOCALIDADES = [
    "SANTO ANTONIO DO DESCOBERTO", "AGUAS LINDAS DE GOIAS", "VALPARAISO DE GOIAS",
    "PLANALTINA DE GOIAS", "SETOR INDUSTRIAL", "NUCLEO BANDEIRANTE", "CIDADE OCIDENTAL",
    "RECANTO DAS EMAS", "VILA ESTRUTURAL", "JARDIM BOTANICO", "CANDANGOLANDIA",
    "SAO SEBASTIAO", "RIACHO FUNDO", "VICENTE PIRES", "AGUAS CLARAS", "SANTA MARIA", 
    "TAGUATINGA", "SOBRADINHO", "PLANALTINA", "BRAZLANDIA", "ALPHAVILLE", "SAMAMBAIA", 
    "CEILANDIA", "BRASILIA", "LUZIANIA", "CRUZEIRO", "FORMOSA", "VARJAO", "GUARA", "GAMA"
]

def classificar_texto(titulo, subtitulo):
    """Verifica se as palavras-chave de Tipo e Localidade estão presentes nos títulos."""
    texto_completo = f"{titulo} {subtitulo}".upper()
    
    tipo_encontrado = "N/A"
    local_encontrado = "N/A"
    
    # Classifica Tipo de Imóvel
    for t in TIPOS_IMOVEL:
        if t in texto_completo:
            if t in ["LOTE", "TERRENO", "AREA"]:
                tipo_encontrado = "LOTE / TERRENO / AREA"
            else:
                tipo_encontrado = t.title()
            break
            
    # Classifica Localidade
    for l in LOCALIDADES:
        if l in texto_completo:
            local_encontrado = l.title()
            break
            
    return tipo_encontrado, local_encontrado


urls_coletadas_hoje = []
init_db()
contagem = 0
contagem2 = 0

print("Atualizar: 'aluguel', 'venda' ou 'ambos'?")
resposta = input().strip().lower()

if resposta not in ['aluguel', 'venda', 'ambos']:
    resposta = 'ambos'

MAX_PAGINAS = 200 

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,mp4,webm}", lambda route: route.abort())
    
    # ==========================
    # BLOCO DE VENDAS
    # ==========================
    if resposta in ['venda', 'ambos']:
        base_venda_url = "https://www.dfimoveis.com.br/venda/df/todos/imoveis"
        
        for pagina in range(1, MAX_PAGINAS + 1):
            url_pagina = f"{base_venda_url}?pagina={pagina}&ordenamento=mais-recente"
            print(f"[*] Coletando VENDAS - Página {pagina}/{MAX_PAGINAS}")
            
            try:
                page.goto(url_pagina, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_selector("article[itemtype='https://schema.org/RealEstateListing']", timeout=10000)
            except Exception:
                break 

            cards = page.locator("article[itemtype='https://schema.org/RealEstateListing']").all()
            if not cards:
                break

            lote_vendas = []
            for card in cards:
                titulo1_loc = card.locator('h2[itemprop="name"]')
                titulo1 = titulo1_loc.inner_text().strip() if titulo1_loc.count() > 0 else "N/A"
                
                subtitulo_loc = card.locator('h3.web-ellipse-view')
                subtitulo = subtitulo_loc.inner_text().strip() if subtitulo_loc.count() > 0 else "N/A"
                
                preco_loc = card.locator("[itemprop='price']")
                preco = preco_loc.inner_text().strip() if preco_loc.count() > 0 else "N/A"
                
                preco_m2_loc = card.locator("p:has-text('Valor m²') strong")
                preco_m2 = preco_m2_loc.inner_text().strip() if preco_m2_loc.count() > 0 else "N/A"
                
                info = card.locator(".imovel-feature .rounded-pill")
                link_loc = card.locator("a").first
                href_relativo = link_loc.get_attribute("href") if link_loc.count() > 0 else ""
                
                url_completa = f"https://www.dfimoveis.com.br{href_relativo}"
                if url_completa not in urls_coletadas_hoje:
                    urls_coletadas_hoje.append(url_completa)
                
                tamanho = info.nth(0).inner_text().strip() if info.count() > 0 else "N/A"
                quartos = info.nth(1).inner_text().strip() if info.count() > 1 else "N/A"
                plantas = info.nth(2).inner_text().strip() if info.count() > 2 else "N/A"
                
                if tamanho == "0 plantas":
                    tamanho = "N/A"
                    plantas = "0 plantas"
                
                # Executa a nova classificação
                tipo_imovel, localidade = classificar_texto(titulo1, subtitulo)

                lote_vendas.append({
                    "endereco_bruto": titulo1,
                    "nome_empreendimento": subtitulo,
                    "preco_bruto": preco,
                    "preco_m2_bruto": preco_m2,
                    "tamanho_bruto": tamanho,
                    "quartos_bruto": quartos,
                    "plantas_bruto": plantas,
                    "url_origem": url_completa,
                    "tipo_transacao": "venda",
                    "tipo_imovel": tipo_imovel,
                    "localidade": localidade
                })
                contagem += 1
                
            salvar_lote_bronze(lote_vendas)

    # ==========================
    # BLOCO DE ALUGUEL
    # ==========================
    if resposta in ['aluguel', 'ambos']:
        base_aluguel_url = "https://www.dfimoveis.com.br/aluguel/df/todos/imoveis"
        
        for pagina in range(1, MAX_PAGINAS + 1):
            url_pagina = f"{base_aluguel_url}?pagina={pagina}&ordenamento=mais-recente"
            print(f"[*] Coletando ALUGUÉIS - Página {pagina}/{MAX_PAGINAS}")
            
            try:
                page.goto(url_pagina, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_selector("article[itemtype='https://schema.org/RealEstateListing']", timeout=10000)
            except Exception:
                break

            cards = page.locator("article[itemtype='https://schema.org/RealEstateListing']").all()
            if not cards:
                break
                
            lote_alugueis = []
            for card in cards:
                titulo1_loc = card.locator('h2[itemprop="name"]')
                titulo1 = titulo1_loc.inner_text().strip() if titulo1_loc.count() > 0 else "N/A"
                
                subtitulo_loc = card.locator('h3.web-ellipse-view')
                subtitulo = subtitulo_loc.inner_text().strip() if subtitulo_loc.count() > 0 else "N/A"
                
                preco_loc = card.locator("[itemprop='price']")
                preco = preco_loc.inner_text().strip() if preco_loc.count() > 0 else "N/A"

                preco_m2_loc = card.locator("p:has-text('Valor m²') strong")
                preco_m2 = preco_m2_loc.inner_text().strip() if preco_m2_loc.count() > 0 else "N/A"
                
                link_loc = card.locator("a").first
                href_relativo = link_loc.get_attribute("href") if link_loc.count() > 0 else ""
                url_completa = f"https://www.dfimoveis.com.br{href_relativo}"
                
                if url_completa not in urls_coletadas_hoje:
                    urls_coletadas_hoje.append(url_completa) 

                info = card.locator(".imovel-feature .rounded-pill")
                valores_brutos = [info.nth(i).inner_text().strip() for i in range(info.count())]

                dados = {"tamanho": "N/A", "quartos": "N/A", "suites": "N/A", "vagas": "N/A"}
                for item in valores_brutos:
                    texto = item.lower()
                    if "m²" in texto or "m2" in texto:
                        dados["tamanho"] = item
                    elif "suít" in texto:
                        dados["suites"] = item
                    elif "quarto" in texto:
                        dados["quartos"] = item
                    elif "vaga" in texto:
                        dados["vagas"] = item
                        
                # Executa a nova classificação
                tipo_imovel, localidade = classificar_texto(titulo1, subtitulo)

                lote_alugueis.append({
                    "endereco_bruto": titulo1,
                    "nome_empreendimento": subtitulo,
                    "preco_bruto": preco,
                    "preco_m2_bruto": preco_m2,
                    "tamanho_bruto": dados["tamanho"],
                    "quartos_bruto": dados["quartos"],
                    "suites_bruto": dados["suites"],
                    "vagas_bruto": dados["vagas"],
                    "url_origem": url_completa,
                    "tipo_transacao": "aluguel",
                    "tipo_imovel": tipo_imovel,
                    "localidade": localidade
                })
                contagem2 += 1
                
            salvar_lote_bronze(lote_alugueis)
                
    browser.close()

print(f"Quantidade de Venda coletados: {contagem}")
print(f"Quantidade de Aluguel coletados: {contagem2}")
marcar_imoveis_vendido(urls_coletadas_hoje)