import requests
import json

url = "http://localhost:8000/analyze_resume"
data = {
    "job_description": "Ищем Frontend разработчика с опытом React",
    "resume_text": "Иван Петров\nReact Developer\nОпыт: 2 года\nТехнологии: React, TypeScript, Next.js"
}

print(f"🚀 Отправляем запрос на {url}")
print(f"📝 Данные: {json.dumps(data, ensure_ascii=False, indent=2)}")

try:
    response = requests.post(url, json=data, timeout=30)
    
    print(f"📊 Статус код: {response.status_code}")
    print(f"📋 Заголовки ответа: {dict(response.headers)}")
    print(f"📄 Текст ответа: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ Успешный ответ:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"❌ Ошибка {response.status_code}: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Не удалось подключиться к серверу. Убедитесь, что app.py запущен.")
except requests.exceptions.Timeout:
    print("❌ Превышено время ожидания ответа (30 сек)")
except json.JSONDecodeError as e:
    print(f"❌ Ошибка парсинга JSON: {e}")
    print(f"Ответ сервера: {response.text}")
except Exception as e:
    print(f"❌ Неожиданная ошибка: {e}")