#import psycopg2
from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn
#from config import host, user, password, db_name, port

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0")



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