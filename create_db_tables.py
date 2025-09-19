import os
import sys
from sqlalchemy import create_engine
from app.models import Base

# Добавляем корневую директорию проекта в sys.path, чтобы Python мог найти app.models
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"))

# Используем предоставленный DATABASE_URL
DATABASE_URL = "postgresql://u8pabi5s6v7nnp:p799258912088002fb9684b5afe72def72326c7b545aab369b533159a18f1487c@c18qegamsgjut6.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dfsb5dl3s8q27s"

# Создаем движок базы данных
engine = create_engine(DATABASE_URL)

def create_tables():
    print("Попытка создания таблиц в базе данных...")
    Base.metadata.create_all(engine)
    print("Таблицы созданы успешно или уже существуют.")

if __name__ == "__main__":
    # Убедитесь, что установлен драйвер PostgreSQL: pip install psycopg2-binary
    create_tables()
