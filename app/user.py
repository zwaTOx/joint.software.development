from pydantic import BaseModel
from fastapi import HTTPException
from .connection import get_db_connection

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

# Функция для создания пользователя
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

# Функция для получения всех пользователей
def get_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, login FROM users;")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users

# Функция для получения пользователя по ID
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

# Функция для обновления пользователя
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

# Функция для удаления пользователя
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