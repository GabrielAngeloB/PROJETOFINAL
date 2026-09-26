import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "arbitragem_db")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "adminpassword")


def get_connection():
    """Gera uma conexão isolada por requisição ao banco PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )


def init_db():
    """Garante que todas as 15 colunas existam na tabela bronze_dfimoveis."""
    query = """
    CREATE TABLE IF NOT EXISTS bronze_dfimoveis (
        id SERIAL PRIMARY KEY,
        endereco_bruto TEXT,
        nome_empreendimento TEXT,
        preco_bruto TEXT,
        preco_m2_bruto TEXT DEFAULT 'N/A',
        tamanho_bruto TEXT,
        quartos_bruto TEXT,
        suites_bruto TEXT DEFAULT 'N/A',
        vagas_bruto TEXT DEFAULT 'N/A',
        plantas_bruto TEXT DEFAULT 'N/A',
        url_origem TEXT,
        tipo_transacao TEXT DEFAULT 'venda',
        tipo_imovel TEXT DEFAULT 'N/A',
        localidade TEXT DEFAULT 'N/A',
        coletado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        vendido BOOLEAN DEFAULT FALSE
    );
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
        conn.commit()


def salvar_lote_bronze(lista_imoveis: list):
    """Salva a lista completa de uma página no banco em uma única query otimizada."""
    if not lista_imoveis:
        return

    query = """
    INSERT INTO bronze_dfimoveis 
    (endereco_bruto, nome_empreendimento, preco_bruto, preco_m2_bruto, tamanho_bruto, 
     quartos_bruto, suites_bruto, vagas_bruto, plantas_bruto, url_origem, 
     tipo_transacao, tipo_imovel, localidade, vendido)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE);
    """

    # O uso do .get() assegura que se um campo (ex: 'plantas_bruto' no aluguel) não existir, ele salva 'N/A' e não quebra o script.
    dados_insercao = [
        (
            item.get("endereco_bruto", "N/A"),
            item.get("nome_empreendimento", "N/A"),
            item.get("preco_bruto", "N/A"),
            item.get("preco_m2_bruto", "N/A"),
            item.get("tamanho_bruto", "N/A"),
            item.get("quartos_bruto", "N/A"),
            item.get("suites_bruto", "N/A"),
            item.get("vagas_bruto", "N/A"),
            item.get("plantas_bruto", "N/A"),
            item.get("url_origem"),
            item.get("tipo_transacao", "venda"),
            item.get("tipo_imovel", "N/A"),
            item.get("localidade", "N/A"),
        )
        for item in lista_imoveis
    ]

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(query, dados_insercao)
        conn.commit()


def marcar_imoveis_vendido(urls_coletadas: list):
    """Marca como vendido qualquer imóvel do banco cuja URL não foi vista na raspagem de hoje."""
    if not urls_coletadas:
        print("Nenhuma URL foi coletada. Pulando etapa de marcação de vendidos.")
        return

    query = """
    UPDATE bronze_dfimoveis
    SET vendido = TRUE
    WHERE NOT (url_origem = ANY(%s))
      AND vendido = FALSE;
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Psycopg2 exige que a lista seja passada dentro de uma tupla para o comando ANY()
            cursor.execute(query, (urls_coletadas,))
            afetados = cursor.rowcount
        conn.commit()
    
    if afetados > 0:
        print(f"Marcados como VENDIDOS/INATIVOS: {afetados} imóvel(is).")