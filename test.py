# Проверить подключение простым скриптом
python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        host='94.228.113.42',
        database='mortech', 
        user='admin_1',
        password=r'hppKD~s@S75;e='
    )
    print('Подключение успешно!')
    conn.close()
except Exception as e:
    print(f'Ошибка: {e}')
"

# Создать миграцию
alembic revision --autogenerate -m "Initial migration"

# Применить миграцию
alembic upgrade head