import os
import pyodbc
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    server = os.getenv('DB_SERVER', None)
    database = os.getenv('DB_DATABASE', None)
    driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    use_windows_auth = os.getenv('DB_USE_WINDOWS_AUTH', 'True').lower() == 'true'
    
    if use_windows_auth:
        # Windows Authentication (Trusted Connection)
        conn_str = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;'
    else:
        # SQL Server Authentication
        username = os.getenv('DB_USERNAME', None)
        password = os.getenv('DB_PASSWORD', None)
        conn_str = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;'
    
    return pyodbc.connect(conn_str)

def create_schema():
    """Create database schema"""
    logger.info("Creating database schema...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Drop tables if exist (in reverse order due to foreign keys)
    logger.info("Dropping existing tables...")
    cursor.execute("IF OBJECT_ID('dbo.Loans', 'U') IS NOT NULL DROP TABLE dbo.Loans")
    cursor.execute("IF OBJECT_ID('dbo.Books', 'U') IS NOT NULL DROP TABLE dbo.Books")
    cursor.execute("IF OBJECT_ID('dbo.Members', 'U') IS NOT NULL DROP TABLE dbo.Members")
    conn.commit()
    
    # Create Members table
    logger.info("Creating Members table...")
    cursor.execute("""
        CREATE TABLE dbo.Members (
            Id       INT IDENTITY(1,1) PRIMARY KEY,
            Name     NVARCHAR(100) NOT NULL,
            Email    NVARCHAR(200) NOT NULL UNIQUE
        )
    """)
    conn.commit()
    
    # Create Books table
    logger.info("Creating Books table...")
    cursor.execute("""
        CREATE TABLE dbo.Books (
            Id       INT IDENTITY(1,1) PRIMARY KEY,
            Title    NVARCHAR(200) NOT NULL,
            Author   NVARCHAR(120) NOT NULL,
            Copies   INT NOT NULL CONSTRAINT CK_Books_Copies CHECK (Copies >= 0)
        )
    """)
    conn.commit()
    
    # Create Loans table
    logger.info("Creating Loans table...")
    cursor.execute("""
        CREATE TABLE dbo.Loans (
            Id         INT IDENTITY(1,1) PRIMARY KEY,
            MemberId   INT NOT NULL CONSTRAINT FK_Loans_Members FOREIGN KEY REFERENCES dbo.Members(Id) ON DELETE CASCADE,
            BookId     INT NOT NULL CONSTRAINT FK_Loans_Books   FOREIGN KEY REFERENCES dbo.Books(Id)   ON DELETE CASCADE,
            LoanDate   DATETIME2(0) NOT NULL CONSTRAINT DF_Loans_LoanDate DEFAULT (SYSUTCDATETIME()),
            DueDate    DATETIME2(0) NOT NULL,
            ReturnDate DATETIME2(0) NULL
        )
    """)
    conn.commit()
    
    # Create indexes
    logger.info("Creating indexes...")
    cursor.execute("CREATE INDEX IX_Loans_Member ON dbo.Loans(MemberId)")
    cursor.execute("CREATE INDEX IX_Loans_Book ON dbo.Loans(BookId) INCLUDE(ReturnDate)")
    conn.commit()
    
    conn.close()
    logger.info("Schema created successfully!")

def seed_data():
    """Seed initial data"""
    logger.info("Seeding initial data...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Seed members
    logger.info("Seeding members...")
    members = [
        ("Jan Kowalski", "jan.kowalski@example.com"),
        ("Anna Nowak", "anna.nowak@example.com"),
        ("Piotr Wiśniewski", "piotr.wisniewski@example.com"),
        ("Maria Wójcik", "maria.wojcik@example.com"),
        ("Tomasz Kamiński", "tomasz.kaminski@example.com")
    ]
    
    for name, email in members:
        cursor.execute("INSERT INTO dbo.Members (Name, Email) VALUES (?, ?)", name, email)
    conn.commit()
    
    # Seed books
    logger.info("Seeding books...")
    books = [
        ("Pan Tadeusz", "Adam Mickiewicz", 3),
        ("Quo Vadis", "Henryk Sienkiewicz", 2),
        ("Lalka", "Bolesław Prus", 2),
        ("Wesele", "Stanisław Wyspiański", 1),
        ("Ferdydurke", "Witold Gombrowicz", 2),
        ("Solaris", "Stanisław Lem", 4),
        ("Zbrodnia i kara", "Fiodor Dostojewski", 2),
        ("1984", "George Orwell", 3),
        ("Władca Pierścieni", "J.R.R. Tolkien", 2),
        ("Harry Potter i Kamień Filozoficzny", "J.K. Rowling", 3)
    ]
    
    for title, author, copies in books:
        cursor.execute("INSERT INTO dbo.Books (Title, Author, Copies) VALUES (?, ?, ?)", 
                      title, author, copies)
    conn.commit()
    
    # Seed some loans
    logger.info("Seeding sample loans...")
    cursor.execute("""
        INSERT INTO dbo.Loans (MemberId, BookId, LoanDate, DueDate, ReturnDate) 
        VALUES (1, 1, DATEADD(day, -20, GETDATE()), DATEADD(day, -6, GETDATE()), DATEADD(day, -5, GETDATE()))
    """)
    cursor.execute("""
        INSERT INTO dbo.Loans (MemberId, BookId, LoanDate, DueDate) 
        VALUES (2, 6, DATEADD(day, -10, GETDATE()), DATEADD(day, 4, GETDATE()))
    """)
    cursor.execute("""
        INSERT INTO dbo.Loans (MemberId, BookId, LoanDate, DueDate) 
        VALUES (3, 8, DATEADD(day, -5, GETDATE()), DATEADD(day, 9, GETDATE()))
    """)
    conn.commit()
    
    conn.close()
    logger.info("Data seeded successfully!")

def reset_database():
    """Reset database: drop, create, and seed"""
    try:
        logger.info("=" * 50)
        logger.info("Starting database reset...")
        logger.info("=" * 50)
        
        create_schema()
        seed_data()
        
        logger.info("=" * 50)
        logger.info("Database reset completed successfully!")
        logger.info("=" * 50)
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        raise

if __name__ == "__main__":
    reset_database()
