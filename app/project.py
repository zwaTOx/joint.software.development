from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

# Модель для создания проекта
class ProjectCreate(BaseModel):
    name: str

# Модель для ответа (с голосами)
class ProjectResponse(BaseModel):
    id: int
    name: str
    voices: int

# Настройки подключения к PostgreSQL
DATABASE_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "12345",
    "host": "db",  # Имя контейнера PostgreSQL
    "port": "5432",
    "client_encoding": "utf8",
}

# Роутер для проектов
router = APIRouter(prefix="/projects", tags=["projects"])

# Функция для подключения к базе данных
def get_db_connection():
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        raise

# Эндпоинт для создания проекта
@router.post("/", response_model=ProjectResponse)
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

# Эндпоинт для получения всех проектов
@router.get("/", response_model=list[ProjectResponse])
def get_projects():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, voices FROM projects;")
    projects = cur.fetchall()
    cur.close()
    conn.close()
    return projects

# Эндпоинт для получения одного проекта по ID
@router.get("/{project_id}", response_model=ProjectResponse)
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

# Эндпоинт для обновления проекта
@router.put("/{project_id}", response_model=ProjectResponse)
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
@router.delete("/{project_id}")
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