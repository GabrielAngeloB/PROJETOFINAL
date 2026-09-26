import requests
from bs4 import BeautifulSoup
from db import init_db, marcar_imoveis_vendido, salvar_lote_bronze

# Listas ordenadas do maior para o menor para evitar sobreposição
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

localidades_link = ["santo-antonio-do-descoberto", "aguas-lindas-de-goias", "valparaiso-de-goias", "planaltina-de-goias", 
                   "setor-industrial", "nucleo-bandeirante", "cidade-ocidental", 
                   "recanto-das-emas", "vila-estrutural", "jardim-botanico", 
                   "candangolandia", "sao-sebastiao", "riacho-fundo", 
                   "vicente-pires", "aguas-claras", "santa-maria", 
                   "taguatinga", "sobradinho", "planaltina", "brazlandia", 
                   "alphaville", "samambaia", "ceilandia", "brasilia", 
                   "luziania", "cruzeiro", "formosa", "varjao", 
                   "guara", "gama"]

def classificar_texto(titulo, subtitulo):
    """Varre rigorosamente o título e o subtítulo para encontrar o tipo de imóvel e a localidade correta."""
    texto_completo = f"{titulo} {subtitulo}".upper()
    tipo_encontrado = "N/A"
    local_encontrado = "N/A"
    
    for t in TIPOS_IMOVEL:
        if t in texto_completo:
            if t in ["LOTE", "TERRENO", "AREA"]:
                tipo_encontrado = "LOTE / TERRENO / AREA"
            else:
                tipo_encontrado = t.title()
            break
            
    for l in LOCALIDADES:
        if l in texto_completo:
            local_encontrado = l.title()
            break
            
    return tipo_encontrado, local_encontrado

def extrair_preco_m2(card):
    """Busca com segurança o valor do metro quadrado dentro do card."""
    for p in card.find_all('p'):
        if 'Valor m²' in p.get_text():
            strong = p.find('strong')
            if strong:
                return strong.get_text(strip=True)
    return "N/A"

def parsear_features(card):
    """Extrai dinamicamente tamanho, quartos, suítes, vagas e plantas."""
    features = [pill.get_text(strip=True) for pill in card.select('.imovel-feature .rounded-pill')]
    
    dados = {
        "tamanho": "N/A",
        "quartos": "N/A",
        "suites": "N/A",
        "vagas": "N/A",
        "plantas": "N/A"
    }
    
    for item in features:
        texto = item.lower()
        if "m²" in texto or "m2" in texto:
            dados["tamanho"] = item
        elif "suít" in texto:
            dados["suites"] = item
        elif "quarto" in texto:
            dados["quartos"] = item
        elif "vaga" in texto:
            dados["vagas"] = item
        elif "planta" in texto:
            dados["plantas"] = item
            
    if dados["tamanho"] == "0 plantas":
        dados["tamanho"] = "N/A"
        dados["plantas"] = "0 plantas"
        
    return dados


# --- EXECUÇÃO PRINCIPAL ---
urls_coletadas_hoje = []
init_db()
contagem_venda = 0
contagem_aluguel = 0

print("Atualizar: 'aluguel', 'venda' ou 'ambos'?")
resposta = input().strip().lower()
if resposta not in ['aluguel', 'venda', 'ambos']:
    resposta = 'ambos'

MAX_PAGINAS = 200

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
})

# ==========================================
# BLOCO DE VENDAS
# ==========================================
if resposta in ['venda', 'ambos']:
    base_venda_url = "https://www.dfimoveis.com.br/venda/df/todos/imoveis"
    for locais in localidades_link:
        for pagina in range(1, MAX_PAGINAS + 1):
            url_pagina = f"{base_venda_url}?pagina={pagina}&ordenamento=mais-recente"
            print(f"[*] Coletando VENDAS - Página {pagina}/{MAX_PAGINAS}")
            
            try:
                resp = session.get(url_pagina, timeout=15)
                if resp.status_code != 200:
                    print(f"[!] Erro {resp.status_code} na página {pagina}. Encerrando Vendas.")
                    break
            except Exception as e:
                print(f"[!] Falha na requisição da página {pagina}: {e}")
                break

            soup = BeautifulSoup(resp.text, 'html.parser')
            cards = soup.find_all('article', attrs={'itemtype': 'https://schema.org/RealEstateListing'})
            
            if not cards:
                print(f"[!] Fim dos resultados na página {pagina} (Vendas).")
                break

            lote_vendas = []
            for card in cards:
                h2_tag = card.find('h2', attrs={'itemprop': 'name'})
                titulo1 = h2_tag.get_text(strip=True) if h2_tag else "N/A"
                
                h3_tag = card.find('h3', class_='web-ellipse-view')
                subtitulo = h3_tag.get_text(strip=True) if h3_tag else "N/A"
                
                preco_tag = card.find(attrs={'itemprop': 'price'})
                preco = preco_tag.get_text(strip=True) if preco_tag else "N/A"
                
                preco_m2 = extrair_preco_m2(card)

                a_tag = card.find('a', href=True)
                href_relativo = a_tag['href'] if a_tag else ""
                url_completa = f"https://www.dfimoveis.com.br{href_relativo}"
                
                if url_completa not in urls_coletadas_hoje:
                    urls_coletadas_hoje.append(url_completa)
                
                dados = parsear_features(card)
                tipo_imovel, localidade = classificar_texto(titulo1, subtitulo)

                lote_vendas.append({
                    "endereco_bruto": titulo1,
                    "nome_empreendimento": subtitulo,
                    "preco_bruto": preco,
                    "preco_m2_bruto": preco_m2, # <--- Preço por m2 incluído corretamente
                    "tamanho_bruto": dados["tamanho"],
                    "quartos_bruto": dados["quartos"],
                    "suites_bruto": dados["suites"],
                    "vagas_bruto": dados["vagas"],
                    "plantas_bruto": dados["plantas"],
                    "url_origem": url_completa,
                    "tipo_transacao": "venda",
                    "tipo_imovel": tipo_imovel,
                    "localidade": localidade
                })
                contagem_venda += 1
                
            salvar_lote_bronze(lote_vendas)

# ==========================================
# BLOCO DE ALUGUEL
# ==========================================
if resposta in ['aluguel', 'ambos']:
    base_aluguel_url = "https://www.dfimoveis.com.br/aluguel/df/todos/imoveis"
    
    for pagina in range(1, MAX_PAGINAS + 1):
        url_pagina = f"{base_aluguel_url}?pagina={pagina}&ordenamento=mais-recente"
        print(f"[*] Coletando ALUGUÉIS - Página {pagina}/{MAX_PAGINAS}")
        
        try:
            resp = session.get(url_pagina, timeout=15)
            if resp.status_code != 200:
                print(f"[!] Erro {resp.status_code} na página {pagina}. Encerrando Aluguéis.")
                break
        except Exception as e:
            print(f"[!] Falha na requisição da página {pagina}: {e}")
            break

        soup = BeautifulSoup(resp.text, 'html.parser')
        cards = soup.find_all('article', attrs={'itemtype': 'https://schema.org/RealEstateListing'})
        
        if not cards:
            print(f"[!] Fim dos resultados na página {pagina} (Aluguel).")
            break
            
        lote_alugueis = []
        for card in cards:
            h2_tag = card.find('h2', attrs={'itemprop': 'name'})
            titulo1 = h2_tag.get_text(strip=True) if h2_tag else "N/A"
            
            h3_tag = card.find('h3', class_='web-ellipse-view')
            subtitulo = h3_tag.get_text(strip=True) if h3_tag else "N/A"
            
            preco_tag = card.find(attrs={'itemprop': 'price'})
            preco = preco_tag.get_text(strip=True) if preco_tag else "N/A"

            preco_m2 = extrair_preco_m2(card)
            
            a_tag = card.find('a', href=True)
            href_relativo = a_tag['href'] if a_tag else ""
            url_completa = f"https://www.dfimoveis.com.br{href_relativo}"
            
            if url_completa not in urls_coletadas_hoje:
                urls_coletadas_hoje.append(url_completa) 

            dados = parsear_features(card)
            tipo_imovel, localidade = classificar_texto(titulo1, subtitulo)

            lote_alugueis.append({
                "endereco_bruto": titulo1,
                "nome_empreendimento": subtitulo,
                "preco_bruto": preco,
                "preco_m2_bruto": preco_m2, # <--- Preço por m2 incluído corretamente
                "tamanho_bruto": dados["tamanho"],
                "quartos_bruto": dados["quartos"],
                "suites_bruto": dados["suites"],
                "vagas_bruto": dados["vagas"],
                "plantas_bruto": dados["plantas"],
                "url_origem": url_completa,
                "tipo_transacao": "aluguel",
                "tipo_imovel": tipo_imovel,
                "localidade": localidade
            })
            contagem_aluguel += 1
            
        salvar_lote_bronze(lote_alugueis)

print("-" * 40)
print(f"Quantidade de Venda coletados: {contagem_venda}")
print(f"Quantidade de Aluguel coletados: {contagem_aluguel}")
print("-" * 40)

marcar_imoveis_vendido(urls_coletadas_hoje)
print("Processo concluído com sucesso!")