import streamlit as st
import requests
from datetime import datetime

# FastAPI backend URL
API_URL = "http://127.0.0.1:8000"

st.title("LLM Destekli Not Defteri")

# Sidebar - Yeni not ekleme
st.sidebar.header("Yeni Not Ekle")
title = st.sidebar.text_input("Başlık")
content = st.sidebar.text_area("İçerik")

if st.sidebar.button("Notu Kaydet"):
    new_note = {"title": title, "content": content, "timestamp": datetime.now().isoformat()}
    response = requests.post(f"{API_URL}/notes", json=new_note)
    if response.status_code == 200:
        st.sidebar.success("Not başarıyla kaydedildi!")
    else:
        st.sidebar.error("Not kaydedilemedi!")

# Ana ekran - Not listesi
st.header("Not Listesi")
response = requests.get(f"{API_URL}/notes")
if response.status_code == 200:
    notes = response.json()
    if notes:
        for note in notes:
            st.subheader(note['title'])
            st.write(note['content'])
            timestamp = note.get('timestamp', 'Tarih bilgisi yok')
            if timestamp != 'Tarih bilgisi yok':
                timestamp = datetime.fromisoformat(timestamp).strftime('%Y-%m-%d %H:%M')
            st.write(f"Tarih: {timestamp}")
            
            # Özetleme Butonu
            if st.button(f"Özetle: {note['title']}", key=f"summarize_{note['id']}"):
                summary_response = requests.post(f"{API_URL}/notes/{note['id']}/summarize")
                if summary_response.status_code == 200:
                    st.write("Özet:", summary_response.json()["summary"])
                else:
                    st.error("Özetleme hatası!")
            
            # Çeviri Butonu
            target_language = st.selectbox(
                "Çevrilecek Dil Seçin",
                ["İngilizce", "İspanyolca", "Japonca"],
                key=f"lang_{note['id']}"
            )
            if st.button(f"Çevir ➡️ {target_language}", key=f"translate_{note['id']}"):
                translate_response = requests.post(
                    f"{API_URL}/translate",
                    json={"text": note['content'], "target_language": target_language}
                )
                if translate_response.status_code == 200:
                    st.success("Çeviri:")
                    st.write(translate_response.json()["translated_text"])
                else:
                    st.error("Çeviri hatası!")
            
# ★ Yeni: Quiz Oluşturma Butonu ★
            if st.button(f"Quiz Oluştur: {note['title']}", key=f"quiz_{note['id']}"):
                quiz_response = requests.post(f"{API_URL}/notes/{note['id']}/quiz")
                if quiz_response.status_code == 200:
                    quiz_data = quiz_response.json()
                    st.subheader("Oluşturulan Quiz")
                    # Burada LLM'den gelen quiz metnini gösteriyoruz.
                    st.write(quiz_data.get("quiz", "Quiz verisi boş."))
                else:
                    st.error("Quiz oluşturulurken hata!")

            # Silme Butonu
            if st.button(f"Sil: {note['title']}", key=f"delete_{note['id']}"):
                delete_response = requests.delete(f"{API_URL}/notes/{note['id']}")
                if delete_response.status_code == 200:
                    st.success("Not silindi!")
                    st.experimental_rerun()  # Sayfayı yenile
                else:
                    st.error("Silme hatası!")
            
            st.markdown("---")
    else:
        st.write("Henüz not eklenmedi.")
else:
    st.error("Notlar yüklenemedi!")

st.markdown(
    """
    <style>
    .fixed-bottom-right {
      position: fixed;
      right: 10px;
      bottom: 10px;
      background-color: #f1f1f1;
      padding: 10px;
      border-radius: 5px;
      box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
      z-index: 1000;
      font-size: 14px;
    }
    .fixed-bottom-right a {
      color: #0e76a8;
      text-decoration: none;
      margin-right: 10px;
    }
    .fixed-bottom-right a:hover {
      text-decoration: underline;
    }
    </style>
    <div class="fixed-bottom-right">
      <a href="https://www.linkedin.com/in/doğukan-kıyıklık-561945288" target="_blank">Benim LinkedIn</a>
      <a href="https://www.linkedin.com/in/salih-enes-unal-20b763351?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app" target="_blank">Arkadaşımın LinkedIn</a>
    </div>
    """,
    unsafe_allow_html=True
)
