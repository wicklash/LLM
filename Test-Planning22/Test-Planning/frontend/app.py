import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.title("Test Planning Document Generator")

# Dosya yükleme bileşeni
uploaded_file = st.file_uploader("Test planning için gerekli dosyayı yükleyin", type=["txt", "pdf", "docx"])

if uploaded_file is not None:
    try:
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
                response = requests.post("http://localhost:8000/generate_test_plan", json=payload)
                if response.status_code == 200:
                    result = response.json()  # {"json_data": ..., "download_url": ...} bekleniyor.
                    st.success("Test planı başarıyla oluşturuldu.")
                    st.markdown(f"[Test Planını İndir]({result['download_url']})")
                    
                    st.subheader("Oluşturulan Test Planı (JSON Formatında)")
                    st.json(result["json_data"])
                    
                    # Gantt chart oluşturmak için:
                    df = pd.DataFrame(result["json_data"])
                    # Tarih sütunlarını datetime formatına çeviriyoruz
                    df["Start Date"] = pd.to_datetime(df["Start Date"])
                    df["End Date"] = pd.to_datetime(df["End Date"])
                    
                    # Plotly Express timeline kullanarak gantt chart oluşturma
                    fig = px.timeline(
                        df,
                        x_start="Start Date",
                        x_end="End Date",
                        y="Task Name",
                        title="Test Planı Gantt Chart",
                        labels={"Task Name": "Görevler"}
                    )
                    # Görevlerin üst üste binmemesi için y eksenini ters çeviriyoruz.
                    fig.update_yaxes(autorange="reversed")
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                else:
                    st.error("Test planı oluşturulurken hata: " + response.text)
            except requests.exceptions.RequestException as e:
                st.error("Sunucuya bağlanırken hata oluştu: " + str(e))
            except ValueError as e:
                st.error("Geçersiz JSON formatı: " + str(e))
