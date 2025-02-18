from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List

app = FastAPI()

# MongoDB Bağlantısı
client = MongoClient("mongodb://localhost:27017/")
db = client["School"]
students_collection = db["Students"]

# Veri Modeli (Pydantic Kullanımı)
class Course(BaseModel):
    course_name: str
    grade: str

class Student(BaseModel):
    student_id: str
    first_name: str
    last_name: str
    age: int
    courses: List[Course]

@app.get("/students")
def get_students():
    students = list(students_collection.find({}, {"_id": 0}))  # MongoDB'den gelen verileri liste olarak al
    return {"students": students}  # Liste olarak döndür

@app.post("/add_student")
def add_student(student: Student):
    student_dict = student.dict()  # Pydantic nesnesini dict() ile MongoDB'ye ekle
    students_collection.insert_one(student_dict)
    return {"message": f"Öğrenci '{student.first_name} {student.last_name}' başarıyla eklendi!"}

@app.delete("/delete_student/{student_id}")
def delete_student(student_id: str):
    result = students_collection.delete_one({"student_id": student_id})
    if result.deleted_count == 1:
        return {"message": f"Öğrenci '{student_id}' başarıyla silindi!"}
    raise HTTPException(status_code=404, detail="Öğrenci bulunamadı!")
