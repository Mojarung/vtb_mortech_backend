FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

ENV APP_DATABASE_URL=sqlite+aiosqlite:///./app.db
ENV APP_SECRET_KEY=your-secret-key-change-in-production
ENV APP_ACCESS_TOKEN_EXPIRE_MINUTES=1440

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
