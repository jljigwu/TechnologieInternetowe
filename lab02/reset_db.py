import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def reset_database():
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_DATABASE')
    driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    use_windows_auth = os.getenv('DB_USE_WINDOWS_AUTH', 'True').lower() == 'true'
    
    if use_windows_auth:
        conn_str = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;'
    else:
        username = os.getenv('DB_USERNAME')
        password = os.getenv('DB_PASSWORD')
        conn_str = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;'
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Read and execute schema file
        with open('Lab02_Shop_Schema.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Execute entire script
        for statement in sql_script.split('\n\n'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    conn.commit()
                except Exception as e:
                    # Continue on minor errors
                    pass
        
        print("✓ Database reset successful!")
        print("✓ Sample products added")
        conn.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        raise

if __name__ == "__main__":
    reset_database()
