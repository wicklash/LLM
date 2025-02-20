import datetime
import json
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import uvicorn
import pandas as pd
from fastapi.responses import FileResponse
import os

# Ollama'nın çalıştığı URL (varsayılan olarak localhost:11434)
OLLAMA_URL = "http://localhost:11434"

# MongoDB bağlantısı (URI, veritabanı ve collection adlarını ihtiyacınıza göre güncelleyin)
client = MongoClient("mongodb://localhost:27017/")
db = client["test_planning_db"]
collection = db["test_plans"]

app = FastAPI()

# İstek veri modeli
class TestPlanRequest(BaseModel):
    content: str  # Kullanıcının yüklediği dosya içeriği

@app.post("/generate_test_plan")
async def generate_test_plan(request: TestPlanRequest):
    # Güncel tarihi alıyoruz
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    # Test planı oluşturma prompt'unu hazırlıyoruz
    prompt_template = f"""
Analyze the following document as an ISTQB expert and use the information provided to generate a comprehensive test planning schedule that adheres strictly to ISTQB standards. Your objective is to produce a detailed test planning document, optimized for creating a Gantt chart. Your analysis should cover all aspects of test planning, including test strategy, resource estimation, scheduling, risk management, and environment/tool requirements. You must focus solely on constructing the test planning schedule, without incorporating the content of the input document verbatim.

When generating dates in your output, use the current date "{today}" as the starting point for scheduling. All planned dates should be calculated relative to today's date.

Your output must be a valid JSON array where each object represents a task in the test planning process. Each object must contain exactly the following keys:
- "Task Name": A concise title for the task.
- "Description": A detailed explanation of the task, including all necessary ISTQB-standard test planning elements.
- "Start Date": The planned start date for the task in the format YYYY-MM-DD.
- "End Date": The planned end date for the task in the format YYYY-MM-DD.
- "Duration (days)": The total number of days allocated for the task.

Below is an example JSON structure to follow:

[
    {{
        "Task Name": "Test Strategy Definition",
        "Description": "Define the overall testing strategy, including objectives, scope (in-scope and out-of-scope items), success criteria, and exit conditions, based on ISTQB standards.",
        "Start Date": "{today}",
        "End Date": "2025-03-05",
        "Duration (days)": 5
    }},
    {{
        "Task Name": "Resource Estimation and Scheduling",
        "Description": "Estimate the required testing resources and develop a realistic schedule that aligns with project deadlines following ISTQB best practices.",
        "Start Date": "2025-03-06",
        "End Date": "2025-03-10",
        "Duration (days)": 5
    }},
    {{
        "Task Name": "Risk Assessment and Mitigation Planning",
        "Description": "Identify potential risks related to security, performance, and usability. Develop mitigation strategies and contingency plans in line with ISTQB standards.",
        "Start Date": "2025-03-11",
        "End Date": "2025-03-15",
        "Duration (days)": 5
    }},
    {{
        "Task Name": "Test Environment and Tool Setup",
        "Description": "Define and set up the test environment, including hardware, software, network configurations, and necessary test tools, ensuring full compliance with ISTQB guidelines.",
        "Start Date": "2025-03-16",
        "End Date": "2025-03-20",
        "Duration (days)": 5
    }}
]

*Additional Instructions:*
- Ensure that the output JSON array is directly convertible into an XLSX spreadsheet, where each key represents a column header.
- Do not include any extra keys or unstructured text outside of the JSON array.
- Your analysis must reflect the expertise of an ISTQB expert and provide a comprehensive test planning schedule that aligns with ISTQB standards.
- Instead of processing a test planning document, use the content provided (which may be from other types of documents) to generate a test planning schedule.
- The output should be detailed and cover all essential aspects of the test planning process without including any feedback or recommendations.
- Use the current date "{today}" as a reference point for all scheduled dates in the generated output.
    """
    
    # Tam prompt, dosya içeriği ile birleştiriliyor.
    full_prompt = prompt_template + "\n\nDocument Content:\n" + request.content

    # Ollama üzerinden llama3:8b modelini çağırıyoruz.
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3:8b",
                "prompt": full_prompt,
                "stream": False
            }
        )
        if response.status_code == 200:
            generated_output = response.json().get("response", "").strip()
        else:
            raise HTTPException(status_code=500, detail=f"Ollama API hatası: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Ollama'ya bağlanılamadı: {e}")

    # Üretilen veriyi MongoDB'ye kaydediyoruz.
    record = {
        "input_content": request.content,
        "generated_output": generated_output,
        "timestamp": datetime.datetime.now(datetime.timezone.utc)
    }
    collection.insert_one(record)

    # API yanıtını logluyoruz
    print("Ollama API yanıtı:", generated_output)

    # JSON dizisini çıkartmak için yanıtı işliyoruz
    try:
        json_start = generated_output.index('[')
        json_end = generated_output.rindex(']') + 1
        json_content = generated_output[json_start:json_end]
        json_data = json.loads(json_content)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=500, detail=f"Geçersiz JSON formatı: Ollama API'den dönen yanıt geçerli bir JSON içermiyor. Yanıt: {generated_output}")

    # JSON verisini XLSX dosyasına dönüştürüyoruz
    output_dir = "./tmp"
    os.makedirs(output_dir, exist_ok=True)
    xlsx_file = os.path.join(output_dir, "test_plan.xlsx")
    df = pd.DataFrame(json_data)
    df.to_excel(xlsx_file, index=False)

    # JSON veri ve indirme linkini içeren yanıtı döndürüyoruz
    return {
        "json_data": json_data,
        "download_url": "http://localhost:8000/download/test_plan.xlsx"
    }

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join("./tmp", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dosya bulunamadı")
    return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=filename)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
