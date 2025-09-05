# Production конфигурация

Приложение настроено для production режима с HTTPS и безопасными настройками.

## Production настройки:

- **Cookies**: `secure=True`, `samesite="none"` (требует HTTPS)
- **CORS**: Только разрешенные домены
- **Токены**: 60 минут жизни
- **HTTPS**: Обязательно для работы

## Создайте файл `.env` в корне папки `vtb_mortech_backend/`:

```env
# Database configuration
DATABASE_HOST=94.228.113.42
DATABASE_NAME=mortech
DATABASE_USER=admin_1
DATABASE_PASSWORD=jopabobra

# JWT configuration (ОБЯЗАТЕЛЬНО ИЗМЕНИТЕ В PRODUCTION!)
SECRET_KEY=your-very-secure-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Resume Analysis Service Configuration
AGENT_ID=
API_KEY=
BASE_URL=https://agent.timeweb.cloud
```

## Запуск в production:

### Backend:
```bash
cd vtb_mortech_backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend:
```bash
cd vtb_mortech_frontend
npm run build
npm start
```

## Важные требования для production:

1. **HTTPS обязателен** - приложение не будет работать без HTTPS
2. **Измените SECRET_KEY** - используйте криптографически стойкий ключ
3. **Настройте домены** - обновите CORS origins в `main.py` если нужно
4. **SSL сертификаты** - убедитесь, что у вас есть валидные SSL сертификаты

## Docker для production:

```bash
# Backend
cd vtb_mortech_backend
docker build -t vtb-backend .
docker run -p 8000:8000 --env-file .env vtb-backend

# Frontend
cd vtb_mortech_frontend
docker build -t vtb-frontend .
docker run -p 3000:3000 vtb-frontend
```
