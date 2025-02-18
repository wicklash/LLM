from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
import requests
from datetime import datetime

# FastAPI uygulamasını başlat
app = FastAPI(title="LLM Destekli Not Defteri API")

# MongoDB bağlantısı
client = MongoClient("mongodb://localhost:27017")
db = client['llm_notes']  # Veritabanı
notes_collection = db['notes']  # Koleksiyon

# Not modeli
class Note(BaseModel):
    title: str
    content: str
    timestamp: str = None

# Çeviri isteği için Pydantic modeli
class TranslationRequest(BaseModel):
    text: str
    target_language: str

# Ollama'nın çalıştığı URL (varsayılan olarak localhost:11434)
OLLAMA_URL = "http://localhost:11434"

# --- Not CRUD Endpoint'leri ---

# Yeni not oluşturma
@app.post("/notes")
async def create_note(note: Note):
    try:
        note_dict = note.dict()
        note_dict["timestamp"] = datetime.now().isoformat()
        result = notes_collection.insert_one(note_dict)
        # MongoDB tarafından oluşturulan _id'yi string'e çevirip "id" olarak ekle
        note_dict["id"] = str(result.inserted_id)
        note_dict.pop("_id", None)
        return note_dict
    except Exception as e:
        print("Not kaydedilirken hata oluştu:", e)
        raise HTTPException(status_code=500, detail="Not kaydedilemedi")

# Tüm notları getirme
@app.get("/notes")
async def get_notes():
    notes = []
    for note in notes_collection.find():
        note["id"] = str(note["_id"])
        note.pop("_id", None)
        notes.append(note)
    return notes

# Belirli bir notu getirme
@app.get("/notes/{note_id}")
async def get_note(note_id: str):
    note = notes_collection.find_one({"_id": ObjectId(note_id)})
    if note:
        note["id"] = str(note["_id"])
        note.pop("_id", None)
        return note
    else:
        raise HTTPException(status_code=404, detail="Not bulunamadı")

# Not güncelleme
@app.put("/notes/{note_id}")
async def update_note(note_id: str, updated_note: Note):
    update_result = notes_collection.update_one(
        {"_id": ObjectId(note_id)},
        {"$set": updated_note.dict()}
    )
    if update_result.modified_count == 1:
        return {"message": "Not güncellendi"}
    else:
        raise HTTPException(status_code=404, detail="Not bulunamadı veya güncellenemedi")

# Not silme
@app.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    delete_result = notes_collection.delete_one({"_id": ObjectId(note_id)})
    if delete_result.deleted_count == 1:
        return {"message": "Not silindi"}
    else:
        raise HTTPException(status_code=404, detail="Not bulunamadı")

# --- LLM Entegrasyonu Endpoint'leri ---

# Notu özetleme
@app.post("/notes/{note_id}/summarize")
async def summarize_note(note_id: str):
    note = notes_collection.find_one({"_id": ObjectId(note_id)})
    if not note:
        raise HTTPException(status_code=404, detail="Not bulunamadı")
    
    content = note.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="Not içeriği boş.")
    
    prompt = f"Bu metni çok kısa Türkçe özetle: {content}"
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3:8b",
                "prompt": prompt,
                "stream": False
            }
        )
        if response.status_code == 200:
            summary = response.json().get("response", "").strip()
            return {"summary": summary}
        else:
            print(f"Ollama API hatası: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Özetleme sırasında hata oluştu")
    except requests.exceptions.RequestException as e:
        print(f"Ollama'ya bağlanılamadı: {e}")
        raise HTTPException(status_code=500, detail="Ollama'ya bağlanılamadı")

# Çeviri endpoint'i
@app.post("/translate")
async def translate_text(request: TranslationRequest):
    prompt = f"Bu metni {request.target_language} diline çevir: {request.text}"
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3:8b",
                "prompt": prompt,
                "stream": False
            }
        )
        if response.status_code == 200:
            translated_text = response.json().get("response", "").strip()
            return {"translated_text": translated_text}
        else:
            print(f"Ollama API hatası: {response.text}")
            raise HTTPException(status_code=500, detail="Çeviri başarısız oldu")
    except requests.exceptions.RequestException as e:
        print(f"Ollama'ya bağlanılamadı: {e}")
        raise HTTPException(status_code=500, detail="Ollama'ya bağlantı hatası")
    
    # ★ Yeni: Otomatik Quiz Oluşturma Endpoint'i ★
@app.post("/notes/{note_id}/quiz")
async def generate_quiz(note_id: str):
    # İlgili notu MongoDB'den çekiyoruz.
    note = notes_collection.find_one({"_id": ObjectId(note_id)})
    if not note:
        raise HTTPException(status_code=404, detail="Not bulunamadı")
    
    content = note.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="Not içeriği boş.")
    
    # LLM'ye gönderilecek prompt'u oluşturuyoruz.
    prompt = (
        "Aşağıdaki ders notu içeriğine dayalı olarak bir quiz oluştur. "
        "Oluşturduğun Quiz 'Türkçe' olsun.\n"
        "Oluşturduğun Quiz 5 soru olsun."
        "Her soru için 4 seçenek ve doğru cevabı belirt.\n"
        "Lütfen quiz çıktısını markdown formatında oluştur; her soruyu 'Soru {n}: Aşağıdakilerden hangisi doğrudur? veya xxx nedir?' şeklinde başlat, seçenekleri alt alta sıralı (her biri yeni satırda olacak şekilde) listele ve en altta 'Doğru Cevap:' kısmında doğru seçeneği belirt. Seçenekleri A), B), C), D) şeklinde yaz.\n"
        f"Ders Notu: {content}"
    )
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3:8b",
                "prompt": prompt,
                "stream": False
            }
        )
        if response.status_code == 200:
            # LLM'nin ürettiği quiz yanıtını alıyoruz.
            quiz_response = response.json().get("response", "").strip()
            return {"quiz": quiz_response}
        else:
            raise HTTPException(status_code=500, detail=f"Quiz oluşturulurken hata oluştu: {response.text}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Ollama'ya bağlanılamadı: {e}")
