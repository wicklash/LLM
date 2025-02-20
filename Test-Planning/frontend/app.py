import streamlit as st
import requests

st.title("Test Planning Document Generator")

# Dosya yükleme bileşeni: TXT, PDF veya DOCX dosya türlerini destekleyebilirsiniz.
uploaded_file = st.file_uploader("Test planning için gerekli dosyayı yükleyin", type=["txt", "pdf", "docx"])

if uploaded_file is not None:
    try:
        # Örneğin, TXT dosyası için içerik okuma:
        content = uploaded_file.read().decode("utf-8")
    except Exception as e:
        st.error("Dosya okunurken hata oluştu: " + str(e))
        content = ""
    
    st.subheader("Yüklenen Dosya İçeriği")
    st.text_area("Dosya İçeriği", content, height=300)

    if st.button("Test Planı Oluştur"):
        if content.strip() == "":
            st.error("Lütfen geçerli bir dosya yükleyin.")
        else:
            payload = {"content": content}
            try:
                # FastAPI sunucusunun çalıştığı adresi kontrol edin.
                response = requests.post("http://localhost:8000/generate_test_plan", json=payload)
                if response.status_code == 200:
                    result = response.json()
                    st.subheader("Oluşturulan Test Planı (JSON Formatında)")
                    st.json(result)
                else:
                    st.error("Test planı oluşturulurken hata: " + response.text)
            except Exception as e:
                st.error("Sunucuya bağlanırken hata oluştu: " + str(e))
