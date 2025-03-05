import psycopg2
from psycopg2.extras import RealDictCursor

# Настройки подключения к PostgreSQL
DATABASE_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "12345",
    "host": "db",  # Имя контейнера PostgreSQL
    "port": "5432",
    "client_encoding": "utf8",
}

# Функция для подключения к базе данных
def get_db_connection():
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        raise

# Функция для создания таблиц
def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            login VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()