from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles  # Импортируем StaticFiles
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.middleware.cors import CORSMiddleware
import datetime

# Настройки подключения к PostgreSQL
# DATABASE_CONFIG = {
#     "dbname": "postgres",
#     "user": "postgres",
#     "password": "12345",
#     "host": "db",  # Имя контейнера PostgreSQL
#     "port": "5432",
#     "client_encoding": "utf8",
# }

DATABASE_CONFIG = {
    "dbname": "users",
    "user": "set",
    "password": "dwordpass",
    "host": "172.30.192.44",  # Имя контейнера PostgreSQL
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

# Модель для создания проекта
class ProjectCreate(BaseModel):
    name: str

# Модель для ответа (с голосами)
class ProjectResponse(BaseModel):
    id: int
    name: str
    voices: int

class SuggestionCreate(BaseModel):
    text: str
    user_id: int
    state: str
    datetime: str  # Формат даты и времени можно адаптировать под требования
    score: int = 0
    title: str

class SuggestionResponse(BaseModel):
    id: int
    text: str
    user_id: int
    state: str
    datetime: str
    score: int
    title: str

# Инициализация FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Подключение статической директории
#app.mount("/static", StaticFiles(directory="public"), name="static")

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
        CREATE TABLE IF NOT EXISTS "User" (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            login VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "Project" (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            voices INT DEFAULT 0
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
    return FileResponse("static/index.html")

# Эндпоинт для создания пользователя
@app.post("/users/", response_model=UserResponse, tags=["users"])
def create_user(user: UserCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO \"User\" (name, login, password) VALUES (%s, %s, %s) RETURNING id, name, login;",
        (user.name, user.login, user.password)
    )
    new_user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return new_user

# Эндпоинт для получения всех пользователей
@app.get("/users/", response_model=list[UserResponse], tags=["users"])
def get_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, login FROM \"User\";")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users

# Эндпоинт для получения одного пользователя по ID
@app.get("/users/{user_id}", response_model=UserResponse, tags=["users"])
def get_user(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, login FROM \"User\" WHERE id = %s;", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Эндпоинт для обновления пользователя
@app.put("/users/{user_id}", response_model=UserResponse, tags=["users"])
def update_user(user_id: int, user: UserCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE \"User\" SET name = %s, login = %s, password = %s WHERE id = %s RETURNING id, name, login;",
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
@app.delete("/users/{user_id}", tags=["users"])
def delete_user(user_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM \"User\" WHERE id = %s RETURNING id;", (user_id,))
    deleted_user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if deleted_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted", "id": deleted_user["id"]}



# Эндпоинт для создания проекта
@app.post("/projects/", response_model=ProjectResponse, tags=["project"])
def create_project(project: ProjectCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO \"Project\" (name) VALUES (%s) RETURNING id, name, voices;",
        (project.name,)
    )
    new_project = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return new_project

# Эндпоинт для получения всех проектов
@app.get("/projects/", response_model=list[ProjectResponse], tags=["project"])
def get_projects():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name, voices FROM "Project";')
    projects = cur.fetchall()
    cur.close()
    conn.close()
    return projects

# Эндпоинт для получения одного проекта по ID
@app.get("/projects/{project_id}", response_model=ProjectResponse, tags=["project"])
def get_project(project_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name, voices FROM "Project" WHERE id = %s;', (project_id,))
    project = cur.fetchone()
    cur.close()
    conn.close()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.put("/projects/{project_id}", response_model=ProjectResponse, tags=["project"])
def update_project(project_id: int, project: ProjectCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE projects SET name = %s WHERE id = %s RETURNING id, name, voices;",
        (project.name, project_id)
    )
    updated_project = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if updated_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated_project

# Эндпоинт для удаления проекта
@app.delete("/projects/{project_id}", tags=["project"])
def delete_project(project_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM \"Project\" WHERE id = %s RETURNING id;", (project_id,))
    deleted_project = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if deleted_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted", "id": deleted_project["id"]}

from datetime import datetime

@app.post("/suggestions/", response_model=SuggestionResponse, tags=["suggestions"])
def create_suggestion(suggestion: SuggestionCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO "Suggestions" (text, user_id, state, datetime, score, title)
        VALUES (%s, %s, %s, NOW(), %s, %s)
        RETURNING id, text, user_id, state, datetime, score, title;
        """,
        (suggestion.text, suggestion.user_id, "New", suggestion.score, suggestion.title)
    )
    new_suggestion = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    # Преобразование datetime в строку
    new_suggestion_dict = dict(new_suggestion)
    new_suggestion_dict['datetime'] = new_suggestion_dict['datetime'].strftime('%Y-%m-%d %H:%M:%S')

    return new_suggestion_dict



# Эндпоинт для получения одного предложения по ID
@app.get("/suggestions/{suggestion_id}", response_model=SuggestionResponse, tags=["suggestions"])
def get_suggestion(suggestion_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, text, user_id, state, datetime, score, title FROM "Suggestions" WHERE id = %s;', (suggestion_id,))
    suggestion = cur.fetchone()
    cur.close()
    conn.close()
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return suggestion

# Эндпоинт для обновления предложения
@app.put("/suggestions/{suggestion_id}", response_model=SuggestionResponse, tags=["suggestions"])
def update_suggestion(suggestion_id: int, suggestion: SuggestionCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE "Suggestions" SET text = %s, user_id = %s, state = %s, datetime = %s, score = %s, title = %s
        WHERE id = %s
        RETURNING id, text, user_id, state, datetime, score, title;
        """,
        (suggestion.text, suggestion.user_id, suggestion.state, suggestion.datetime, suggestion.score, suggestion.title, suggestion_id)
    )
    updated_suggestion = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if updated_suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return updated_suggestion

# Эндпоинт для удаления предложения
@app.delete("/suggestions/{suggestion_id}", tags=["suggestions"])
def delete_suggestion(suggestion_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM "Suggestions" WHERE id = %s RETURNING id;', (suggestion_id,))
    deleted_suggestion = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if deleted_suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"message": "Suggestion deleted", "id": deleted_suggestion["id"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
