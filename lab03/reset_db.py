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
        
        with open('Blog_Schema.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Split by GO (SQL Server batch separator)
        statements = []
        for batch in sql_script.split('GO'):
            batch = batch.strip()
            if batch and batch.upper() != 'GO':
                # Remove ONLY standalone comment lines, keep comments that are before SQL
                lines = []
                has_sql = False
                for line in batch.split('\n'):
                    stripped = line.strip()
                    # Keep the line if it's not a standalone comment OR if we already have SQL
                    if not stripped.startswith('--') or has_sql:
                        lines.append(line)
                        if stripped and not stripped.startswith('--'):
                            has_sql = True
                    elif stripped.startswith('--') and not has_sql:
                        # This is a leading comment, skip it but check next lines
                        continue
                
                clean_batch = '\n'.join(lines).strip()
                if clean_batch:
                    statements.append(clean_batch)
        
        print(f"Found {len(statements)} statements to execute")
        
        for i, statement in enumerate(statements, 1):
            if not statement or statement.startswith('--'):
                continue
            try:
                # Show what we're executing
                preview = statement[:150].replace('\n', ' ')
                print(f"Executing statement {i}: {preview}...")
                cursor.execute(statement)
                conn.commit()
                print(f"  ✓ Statement {i} executed successfully")
            except Exception as e:
                print(f"  ✗ Error in statement {i}: {e}")
                print(f"  Full statement: {statement}")
        
        print("✓ Database reset successful!")
        print("✓ Sample posts and comments added")
        
        # Verify data was inserted
        print("\n--- Verifying data in database ---")
        cursor.execute("SELECT COUNT(*) FROM dbo.Posts")
        posts_count = cursor.fetchone()[0]  # type: ignore
        print(f"Posts in database: {posts_count}")
        
        cursor.execute("SELECT COUNT(*) FROM dbo.Comments")
        comments_count = cursor.fetchone()[0] # type: ignore
        print(f"Comments in database: {comments_count}")
        
        if posts_count > 0:
            cursor.execute("SELECT Id, Title FROM dbo.Posts")
            print("\nPosts:")
            for row in cursor.fetchall():
                print(f"  - [{row[0]}] {row[1]}")
        
        if comments_count > 0:
            cursor.execute("SELECT Id, PostId, Author, Approved FROM dbo.Comments")
            print("\nComments:")
            for row in cursor.fetchall():
                print(f"  - [{row[0]}] Post {row[1]} by {row[2]} (Approved: {row[3]})")
        
        conn.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        raise

if __name__ == "__main__":
    reset_database()
