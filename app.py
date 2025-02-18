import streamlit as st
import requests

# API URL'si
API_URL = "http://127.0.0.1:8000"

# Başlık
st.title("📚 Öğrenci Yönetim Sistemi")

# Sayfa Seçimi
page = st.sidebar.selectbox("Sayfa Seçin", ["Öğrencileri Listele", "Yeni Öğrenci Ekle"])

# 📋 Öğrencileri Listele Sayfası
if page == "Öğrencileri Listele":
    st.header("Öğrenciler Listesi")
    
    if st.button("📋 Öğrencileri Listele"):
        response = requests.get(f"{API_URL}/students")
        if response.status_code == 200:
            students = response.json()["students"]
            if students:
                for student in students:
                    st.write(f"📌 {student['first_name']} {student['last_name']} - {student['age']} yaşında")
                    st.write("📚 Dersler:")
                    for course in student["courses"]:
                        st.write(f"- {course['course_name']} : {course['grade']}")
                    st.write("----")
            else:
                st.warning("📭 Sistemde kayıtlı öğrenci bulunmamaktadır.")
        else:
            st.error("🚨 Öğrenciler yüklenirken bir hata oluştu.")

# 🆕 Yeni Öğrenci Ekle Sayfası
elif page == "Yeni Öğrenci Ekle":
    st.header("Yeni Öğrenci Ekle")

    # Öğrenci bilgilerini al
    student_id = st.text_input("📌 Öğrenci ID:")
    first_name = st.text_input("📌 Öğrenci Adı:")
    last_name = st.text_input("📌 Soyadı:")
    age = st.number_input("📅 Yaş", min_value=0, max_value=100, step=1)

    # Ders ekleme
    if "courses" not in st.session_state:
        st.session_state["courses"] = []

    course_name = st.text_input("📚 Ders Adı:")
    grade = st.text_input("📈 Notu:")

    if st.button("Ders Ekle"):
        if course_name and grade:
            st.session_state["courses"].append({"course_name": course_name, "grade": grade})
            st.success(f"{course_name} dersi eklendi!")
        else:
            st.warning("⚠️ Ders adı ve notu boş olamaz!")

    # Eklenen dersleri göster
    if st.session_state["courses"]:
        st.subheader("Eklemiş Olduğunuz Dersler:")
        for i, course in enumerate(st.session_state["courses"], start=1):
            st.write(f"{i}. {course['course_name']} - {course['grade']}")

    # Öğrenciyi ekleme
    if st.button("✅ Öğrenci Ekle"):
        # Öğrencinin tüm bilgileri ve dersler kontrol ediliyor
        if student_id and first_name and last_name and age and len(st.session_state["courses"]) > 0:
            student = {
                "student_id": student_id,
                "first_name": first_name,
                "last_name": last_name,
                "age": age,
                "courses": st.session_state["courses"]
            }
            response = requests.post(f"{API_URL}/add_student", json=student)
            if response.status_code == 200:
                st.success(response.json()["message"])
                # Öğrenci başarıyla eklendikten sonra ders listesi temizleniyor
                st.session_state["courses"] = []  
            else:
                st.error("⚠️ Öğrenci eklenirken bir hata oluştu!")
        else:
            if len(st.session_state["courses"]) == 0:
                st.warning("⚠️ Lütfen en az bir ders ekleyin!")
            else:
                st.warning("⚠️ Lütfen tüm öğrenci bilgilerini doldurun!")

# ❌ Öğrenci Silme
elif page == "Öğrenci Sil":
    st.header("Öğrenci Sil")

    delete_student_id = st.text_input("📌 Silmek istediğiniz öğrencinin ID'si:")

    if st.button("🚫 Öğrenci Sil"):
        if delete_student_id:
            response = requests.delete(f"{API_URL}/delete_student/{delete_student_id}")
            if response.status_code == 200:
                st.success(response.json()["message"])
            else:
                st.error("⚠️ Öğrenci silinemedi! Öğrencinin ID'si yanlış olabilir.")
        else:
            st.warning("⚠️ Lütfen bir ID girin!")
