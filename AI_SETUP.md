# 🤖 Настройка AI интеграции

## 📋 Пошаговая инструкция

### 1. 🔑 Получение AI ключей

1. **Перейдите на [Timeweb Cloud AI](https://cloud.timeweb.com/)**
2. **Зарегистрируйтесь** или войдите в аккаунт
3. **Создайте AI агента** в панели управления
4. **Скопируйте два ключа:**
   - `AI_API_KEY` - API ключ для авторизации (в заголовке Authorization)
   - `AI_AGENT_ID` - ID вашего агента (в URL: `/api/v1/cloud-ai/agents/{agent_access_id}/call`)

### 2. ⚙️ Настройка конфигурации

Откройте файл `app/core/config.py` и вставьте ваши ключи:

```python
# AI Service (Timeweb Cloud AI)
ai_api_key: str = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Ваш API ключ
ai_agent_id: str = "agent_1234567890abcdef"  # Ваш Agent Access ID
```

**Пример из вашего кода:**
```python
headers = {
    'Authorization': "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  # Это AI_API_KEY
    'Content-Type': "application/json"
}
# URL: /api/v1/cloud-ai/agents/agent_1234567890abcdef/call
#                                    ^^^^^^^^^^^^^^^^^^^^
#                                    Это AI_AGENT_ID
```

### 3. 📦 Установка зависимостей

```bash
# Активируйте виртуальное окружение (если есть)
source myenv/bin/activate

# Установите новые зависимости
pip install pdfplumber aiohttp

# Или установите все зависимости
pip install -r requirements.txt
```

### 4. 🗄️ Миграция базы данных

```bash
python migrate_ai_fields.py
```

### 5. 🚀 Запуск сервера

```bash
uvicorn app.main:app --reload
```

## ✅ Проверка настройки

После запуска сервера вы должны увидеть в логах:

```
INFO: AI service initialized successfully
```

Если ключи не настроены:
```
WARNING: AI API key or Agent ID not set in config. AI features will be disabled.
```

## 🔧 Тестирование AI

### 1. Подача заявки с резюме

```bash
curl -X POST "http://localhost:8000/vacancies/1/apply" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "resume_file=@resume.pdf" \
  -F "cover_letter=Заинтересован в позиции"
```

### 2. Пакетный анализ

```bash
curl -X POST "http://localhost:8000/vacancies/applications/batch-analyze" \
  -H "Authorization: Bearer HR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"application_ids": [1, 2, 3]}'
```

## 🐛 Решение проблем

### Ошибка: "AI service not initialized"
- Проверьте правильность API ключа и Agent ID в `config.py`
- Убедитесь, что ключи не пустые

### Ошибка: "Failed to initialize AI service"
- Проверьте доступность Timeweb Cloud AI
- Убедитесь в правильности формата ключей

### Ошибка: "Could not extract text from PDF"
- Убедитесь, что PDF файл не поврежден
- Проверьте, что файл содержит текст (не только изображения)

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи сервера
2. Убедитесь в правильности настройки ключей
3. Проверьте доступность Timeweb Cloud AI
4. Обратитесь к команде разработки
