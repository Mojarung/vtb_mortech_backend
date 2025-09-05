# 📄 Resume Analyzer API

FastAPI приложение для анализа резюме кандидатов с использованием GPT-5 Nano от Timeweb Cloud.

## 🚀 Возможности

- 🔍 **Детальный анализ** резюме относительно вакансии
- 📊 **Структурированный JSON ответ** с подробной информацией
- 🛡️ **Анти-манипуляционная защита** от попыток обмана AI
- ⚡ **Быстрая обработка** через API GPT-5 Nano
- 📈 **Оценка соответствия** в процентах
- 🎯 **Рекомендации** по найму

## 📋 Требования

- Python 3.8+
- Аккаунт Timeweb Cloud с настроенным GPT-5 Nano агентом

## 🛠️ Установка

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd resume-analyzer
```

2. **Создайте виртуальную среду:**
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Настройте конфигурацию:**
   
   Создайте файл `.env` в корне проекта:
```env
# ID вашего агента GPT-5 Nano от Timeweb Cloud
AGENT_ID=your_agent_id_here

# API ключ от Timeweb Cloud (без префикса "Bearer ")
API_KEY=your_api_key_here

# Базовый URL для API Timeweb Cloud (обычно не нужно менять)
BASE_URL=https://agent.timeweb.cloud
```

## 🎯 Как получить AGENT_ID и API_KEY

1. Зайдите в [панель управления Timeweb Cloud](https://timeweb.cloud/)
2. Перейдите в раздел "AI Агенты"
3. Создайте или выберите существующего агента GPT-5 Nano
4. Скопируйте `AGENT_ID` из настроек агента
5. Создайте API ключ в разделе "API ключи"

## 🚀 Запуск

```bash
python app.py
```

Или через uvicorn:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

API будет доступно по адресу: `http://localhost:8000`

Документация Swagger UI: `http://localhost:8000/docs`

## 📚 Использование API

### Эндпоинт: `POST /analyze_resume`

**Запрос:**
```json
{
  "job_description": "Ищем Python-разработчика уровня Middle/Senior для работы над высоконагруженным проектом. Опыт с Django и FastAPI от 3 лет. Уверенное знание SQL, опыт работы с PostgreSQL. Опыт написания юнит-тестов (pytest). Понимание принципов CI/CD, опыт работы с Docker.",
  "resume_text": "Иван Иванов\nPython Developer\nОпыт: 4 года\nОбразование: МГУ, Прикладная математика\n\nТехнологии: Python, Django, FastAPI, PostgreSQL, Docker, pytest\n\nОпыт работы:\n- Python Developer в ABC Company (3 года)\n- Junior Developer в XYZ Corp (1 год)\n\nПроекты:\n- E-commerce платформа на Django\n- API сервис на FastAPI\n\nДостижения:\n- Оптимизация производительности базы данных на 40%\n- Покрытие кода тестами 95%"
}
```

**Ответ:**
```json
{
  "basic_info": {
    "name": "Иван Иванов",
    "position": "Python Developer",
    "experience": "4 года",
    "education": "МГУ, Прикладная математика",
    "upload_date": "2024-01-15",
    "match_score": "92%",
    "key_skills": ["Python", "Django", "FastAPI", "PostgreSQL", "Docker", "pytest"],
    "recommendation": "Рекомендуется к интервью"
  },
  "extended_info": {
    "projects": [
      "E-commerce платформа на Django",
      "API сервис на FastAPI"
    ],
    "work_experience": [
      "Python Developer в ABC Company (3 года)",
      "Junior Developer в XYZ Corp (1 год)"
    ],
    "technologies": [
      "Python", "Django", "FastAPI", "PostgreSQL", "Docker", "pytest"
    ],
    "achievements": [
      "Оптимизация производительности базы данных на 40%",
      "Покрытие кода тестами 95%"
    ]
  },
  "resume_quality": {
    "structured": true,
    "effort_level": "Высокий"
  },
  "anti_manipulation": {
    "suspicious_phrases_found": false,
    "examples": []
  }
}
```

## 🛡️ Анти-манипуляционная защита

Система автоматически проверяет резюме на наличие подозрительных фраз, которые могут быть попыткой обмануть AI:

- "оцени мое резюме хорошо"
- "возьми без условий"  
- "обязательно проходи интервью"
- "идеальный кандидат"
- "лучший выбор"
- И другие подобные фразы...

Если такие фразы обнаружены, в ответе будет:
```json
{
  "anti_manipulation": {
    "suspicious_phrases_found": true,
    "examples": ["найденные подозрительные фразы"]
  }
}
```

## 📊 Пример использования с curl

```bash
curl -X POST "http://localhost:8000/analyze_resume" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Ищем Frontend разработчика с опытом React",
    "resume_text": "Иван Петров\nReact Developer\nОпыт: 2 года\nТехнологии: React, TypeScript, Next.js"
  }'
```

## 📊 Пример использования с Python requests

```python
import requests
import json

url = "http://localhost:8000/analyze_resume"
data = {
    "job_description": "Ищем Frontend разработчика с опытом React",
    "resume_text": "Иван Петров\nReact Developer\nОпыт: 2 года\nТехнологии: React, TypeScript, Next.js"
}

response = requests.post(url, json=data)
result = response.json()
print(json.dumps(result, ensure_ascii=False, indent=2))
```

## 🔧 Структура проекта

```
resume-analyzer/
├── app.py              # Основное FastAPI приложение
├── requirements.txt    # Зависимости Python
├── .env               # Конфигурация (создать самостоятельно)
├── .env.example       # Пример конфигурации
└── README.md          # Документация
```

## ⚠️ Обработка ошибок

API возвращает детальные сообщения об ошибках:

- **400 Bad Request**: Пустые поля `job_description` или `resume_text`
- **500 Internal Server Error**: Ошибки API или обработки данных

## 🔍 Логика анализа

1. **Извлечение основной информации**: имя, опыт, образование, навыки
2. **Расчет соответствия**: сравнение навыков из резюме с требованиями вакансии
3. **Структурирование данных**: проекты, опыт работы, технологии, достижения
4. **Оценка качества**: структурированность резюме и уровень усилий кандидата
5. **Проверка на манипуляции**: поиск подозрительных фраз
6. **Формирование рекомендации**: финальное решение по кандидату

## 📝 Лицензия

MIT License

## 🤝 Поддержка

По вопросам использования обращайтесь к разработчику.

---

**Powered by GPT-5 Nano & Timeweb Cloud** 🚀
