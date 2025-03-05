from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles  # Импортируем StaticFiles
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.middleware.cors import CORSMiddleware

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
    "dbname": "User",
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
        CREATE TABLE IF NOT EXISTS User (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            login VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Project (
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
        "INSERT INTO users (name, login, password) VALUES (%s, %s, %s) RETURNING id, name, login;",
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
    cur.execute("SELECT id, name, login FROM users;")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users

# Эндпоинт для получения одного пользователя по ID
@app.get("/users/{user_id}", response_model=UserResponse, tags=["users"])
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
@app.put("/users/{user_id}", response_model=UserResponse, tags=["users"])
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
@app.delete("/users/{user_id}", tags=["users"])
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



@app.post("/projects/", response_model=ProjectResponse, tags=["project"])
def create_project(project: ProjectCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO projects (name) VALUES (%s) RETURNING id, name, voices;",
        (project.name,)
    )
    new_project = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return new_project

@app.get("/projects/", response_model=list[ProjectResponse], tags=["project"])
def get_projects():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, voices FROM projects;")
    projects = cur.fetchall()
    cur.close()
    conn.close()
    return projects

@app.get("/projects/{project_id}", response_model=ProjectResponse, tags=["project"])
def get_project(project_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, voices FROM projects WHERE id = %s;", (project_id,))
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

@app.delete("/projects/{project_id}", tags=["project"])
def delete_project(project_id: int):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM projects WHERE id = %s RETURNING id;", (project_id,))
    deleted_project = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if deleted_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted", "id": deleted_project["id"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)