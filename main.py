import requests
from fastapi import FastAPI, Request
import uvicorn
import uuid
import base64
import json

app = FastAPI()

# === ТВОИ НАСТРОЙКИ ===
VK_TOKEN = "vk1.a.r3U_mkBw7HIA0YIjmFhhIEwQ_YZQjswQ1mMcr4IJh9ahiVaI5kVBW67ycphVqpDtK5ZlhccAJmswTR1wYR-1z2NpSDlYtlA0O9VvCAslJz_MWr_vj4goL7FXvj9lA9gIs7m78pvGr1K9NO9zxl8i1HALCQIJhyZcfERaOPWsIH8kXwwFeIkNGTo7XBrvzRbDvhbMYq0lM099Ja8JlsW7NQ"
USER_ID = 691890810  
GIGACHAT_CREDENTIALS = "MDFhMGM5OTgtYjljMy03MjdmLWJmZGEtODA5ODFmYTkzYzRmOmJkMWE5ZDA5LTJkYTktNGI1YS1hYTJmLTU5MjgwNWUwMDBiOQ==01a0c998-b9c3-727f-bfda-80981fa93c4f"
# ======================

def get_gigachat_token():
    url = "https://sberbank.ru"
    headers = {
        'Authorization': f'Bearer {GIGACHAT_CREDENTIALS}',
        'RqUID': str(uuid.uuid4()),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    res = requests.post(url, headers=headers, data={'scope': 'GIGACHAT_API_PERS'}, verify=False).json()
    return res['access_token']

@app.post("/exam")
async def process_photo(request: Request):
    try:
        # Читаем запрос как сырой текст, чтобы обойти любые капризы FastAPI
        raw_body = await request.body()
        data = json.loads(raw_body.decode("utf-8"))
        
        # Декодируем Base64 в байты фото
        photo_bytes = base64.b64decode(data["image"])
        print("[СЕРВЕР] Фото успешно принято и декодировано!")
        
        g_token = get_gigachat_token()

        # Загружаем в Сбер
        upload_url = "https://sberbank.ru"
        file_res = requests.post(upload_url, headers={'Authorization': f'Bearer {g_token}'}, files={'file': ('img.jpg', photo_bytes, 'image/jpeg')}, data={'purpose': 'general'}, verify=False).json()
        file_id = file_res['id']

        # Просим GigaChat решить задачу (используем базовую стабильную модель)
        chat_url = "https://sberbank.ru"
        chat_payload = {
            "model": "GigaChat", 
            "messages": [{
                "role": "user",
                "content": "Реши тест на фото СУПЕР КРАТКО. Выведи только финальные ответы цифрами или буквами.",
                "attachments": [file_id]
            }]
        }
        ai_res = requests.post(chat_url, headers={'Authorization': f'Bearer {g_token}'}, json=chat_payload, verify=False).json()
        ai_solution = ai_res['choices']['message']['content']

        # Отправляем в ВК
        vk_url = "https://vk.com"
        requests.get(vk_url, params={
            "access_token": VK_TOKEN, "user_id": USER_ID, "random_id": 0, "message": f"🤖 ОТВЕТ ИИ:\n{ai_solution}", "v": "5.131"
        })
        return {"status": "success"}
    except Exception as e:
        print(f"[КРИТИЧЕСКАЯ ОШИБКА СЕРВЕРА] {str(e)}")
        # Если упало, шлем ошибку прямо в ВК, чтобы ты сразу понял в чем дело!
        try:
            requests.get("https://vk.com", params={
                "access_token": VK_TOKEN, "user_id": USER_ID, "random_id": 0, "message": f"❌ Ошибка на сервере: {str(e)}", "v": "5.131"
            })
        except:
            pass
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
