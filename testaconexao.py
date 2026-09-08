import psycopg2

DB_HOST = "127.0.0.1"
DB_PORT = "5433"  # Porta liberada para o seu Windows
DB_NAME = "arbitragem_db"
DB_USER = "admin"
DB_PASS = "adminpassword"

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        connect_timeout=5,
    )
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    versao = cursor.fetchone()[0]

    print(" Conexão estabelecida com sucesso!")
    print(f" Versão do PostgreSQL: {versao}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n Erro ao conectar: {e}")