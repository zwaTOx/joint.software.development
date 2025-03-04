from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

#docker run --name my_postgres -p 5438:5432 -e POSTGRES_PASSWORD=12345 --network my-network -d postgres
#uvicorn app.main:app --reload

DATABASE_CONFIG = {
    "dbname": "postgres",  
    "user": "postgres",    
    "password": "12345",   
    "host": "db",  # Имя контейнера PostgreSQL
    "port": "5432",         # Пробросил (5438 -> 5432)
    "client_encoding": "utf8",
}

# Модель для создания записи
class ItemCreate(BaseModel):
    name: str
    description: str

# Модель для ответа
class ItemResponse(BaseModel):
    id: int
    name: str
    description: str

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

# Создание таблицы (если её нет)
def create_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# Инициализация таблицы при старте приложения
@app.on_event("startup")
def startup():
    create_table()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

# Эндпоинт для создания записи
@app.post("/items/", response_model=ItemResponse)
def create_item(item: ItemCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO items (name, description) VALUES (%s, %s) RETURNING id;",
        (item.name, item.description)
    )
    new_item = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {**new_item, **item.dict()}

# Эндпоинт для получения всех записей
@app.get("/items/", response_model=list[ItemResponse])
def get_items():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items;")
    items = cur.fetchall()
    cur.close()
    conn.close()
    return items

# Эндпоинт для получения одной записи по ID
@app.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items WHERE id = %s;", (item_id,))
    item = cur.fetchone()
    cur.close()
    conn.close()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# Эндпоинт для обновления записи
@app.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE items SET name = %s, description = %s WHERE id = %s RETURNING id;",
        (item.name, item.description, item_id)
    )
    updated_item = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {**updated_item, **item.dict()}

# Эндпоинт для удаления записи
@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE id = %s RETURNING id;", (item_id,))
    deleted_item = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if deleted_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted", "id": deleted_item["id"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)