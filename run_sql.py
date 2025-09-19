import psycopg2
import os

# URL базы данных
DATABASE_URL = "postgresql://u8pabi5s6v7nnp:p799258912088002fb9684b5afe72def72326c7b545aab369b533159a18f1487c@c18qegamsgjut6.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dfsb5dl3s8q27s"

def run_sql_script():
    try:
        # Подключение к БД
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Чтение SQL файла
        with open('clean_and_create.sql', 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # Выполнение SQL
        cursor.execute(sql_script)
        conn.commit()
        
        print("✅ Таблицы успешно созданы!")
        
        # Проверка созданных таблиц
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print("\n📋 Созданные таблицы:")
        for table in tables:
            print(f"  - {table[0]}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    run_sql_script()
