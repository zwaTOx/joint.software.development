import psycopg2
from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn
from config import host, user, password, db_name, port

app = FastAPI()

def get_db_connection():
    try:
        connection = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=db_name
        )
        return connection
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        return None

@app.get("/")
def read_root():
    return {"message": "Hello World"}

#http://127.0.0.1:8000/add-user
@app.post("/add-user")
def add_user(name: str, login: str, password: str):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO User (name, login, password) VALUES (%s, %s, %s) RETURNING id;",
                (name, login, password)
            )
            user_id = cursor.fetchone()[0]
            connection.commit()
            return {"status": "User added", "user_id": user_id}
        except Exception as e:
            connection.rollback()
            return {"status": "Error", "detail": str(e)}
        finally:
            cursor.close()
            connection.close()
    else:
        return {"status": "Not Connected"}

#http://127.0.0.1:8000/db-info
@app.get("/db-info")
def get_db_info():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        cursor.close()
        connection.close()
        return {"database_version": db_version[0], "status": "Connected"}
    else:
        return {"status": "Not Connected"}

if __name__ == '__main__':
    config = uvicorn.Config("main:app", port=8000, log_level="info", reload=True)
    server = uvicorn.Server(config)
    server.run()



#http://127.0.0.1:8000/students
# @app.get("/students")
# def get_all_students():
#     return json_to_dict_list(path_to_json)

#http://127.0.0.1:8000/students/4
#http://127.0.0.1:8000/students/1?enrollment_year=2019&major=Психология
# @app.get("/students/{course}")
# def get_filtered_students(course: int | None = None, major: str = None, enrollment_year: int = None):
#     #students = json_to_dict_list(path_to_json)
#     filtered_students = []
#     for student in students:
#         if student["course"] == course:
#             filtered_students.append(student)

    # if major:
    #     filtered_students = [student for student in filtered_students if student['major'].lower() == major.lower()]

    # if enrollment_year:
    #     filtered_students = [student for student in filtered_students if student['enrollment_year'] == enrollment_year]

    # return filtered_students