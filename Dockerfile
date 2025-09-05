FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

ENV APP_POSTGRES_HOST=3544d32d1703d6ae1b1d2f22.twc1.net
ENV APP_POSTGRES_DATABASE=default_db
ENV APP_POSTGRES_USER=admin_1
ENV APP_POSTGRES_PASSWORD=hppKD~s@S75;e=
ENV APP_SECRET_KEY=your-secret-key-change-in-production
ENV APP_ACCESS_TOKEN_EXPIRE_MINUTES=1440

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
