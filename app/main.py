from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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

# Модель для создания пользователя
class UserCreate(BaseModel):
    name: str
    login: str
    password: str

# Модель для ответа (без пароля)
class UserResponse(BaseModel):
    id: int
    name: str
    login: str

# Инициализация FastAPI
app = FastAPI()

# Подключение к базе данных
def get_db_connection():
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        raise

# Создание таблицы users (если её нет)
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

# Инициализация таблиц при старте приложения
@app.on_event("startup")
def startup():
    create_tables()  # Создаем таблицу users

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# Эндпоинт для создания пользователя
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, login, password) VALUES (%s, %s, %s) RETURNING id, name, login;",
        (user.name, user.login, user.password)
    )
    new_user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return new_user

# Эндпоинт для получения всех пользователей
@app.get("/users/", response_model=list[UserResponse])
def get_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, login FROM users;")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users

# Эндпоинт для получения одного пользователя по ID
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, login FROM users WHERE id = %s;", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Эндпоинт для обновления пользователя
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET name = %s, login = %s, password = %s WHERE id = %s RETURNING id, name, login;",
        (user.name, user.login, user.password, user_id)
    )
    updated_user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

# Эндпоинт для удаления пользователя
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s RETURNING id;", (user_id,))
    deleted_user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if deleted_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted", "id": deleted_user["id"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)