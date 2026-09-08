import os
import psycopg2
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "arbitragem_db")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "adminpassword")


def get_connection():
    """Retorna uma conexão ativa com o PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )


def init_db():
    """Cria as tabelas necessárias no banco de dados se não existirem."""
    query = """
    CREATE TABLE IF NOT EXISTS bronze_dfimoveis (
        id SERIAL PRIMARY KEY,
        endereco_bruto TEXT,
        nome_empreendimento TEXT,
        preco_bruto TEXT,
        tamanho_bruto TEXT,
        quartos_bruto TEXT,
        plantas_bruto TEXT,
        url_origem TEXT,
        coletado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
        conn.commit()
    print(" Tabela 'bronze_dfimoveis' verificada/criada com sucesso.")


def salvar_imovel_bronze(dados: dict):
    """Insere um imóvel raspado na camada Bronze."""
    query = """
    INSERT INTO bronze_dfimoveis 
    (endereco_bruto, nome_empreendimento, preco_bruto, tamanho_bruto, quartos_bruto, plantas_bruto, url_origem)
    VALUES (%s, %s, %s, %s, %s, %s, %s);
    """
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                query,
                (
                    dados.get("endereco_bruto"),
                    dados.get("nome_empreendimento"),
                    dados.get("preco_bruto"),
                    dados.get("tamanho_bruto"),
                    dados.get("quartos_bruto"),
                    dados.get("plantas_bruto"),
                    dados.get("url_origem"),
                ),
            )
        conn.commit()