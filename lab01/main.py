import os
import pyodbc
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, validator
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

# FastAPI app
app = FastAPI(title="Library Management API")

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    server = os.getenv('DB_SERVER', 'localhost')
    database = os.getenv('DB_DATABASE', 'LibraryDB')
    driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    use_windows_auth = os.getenv('DB_USE_WINDOWS_AUTH', 'True').lower() == 'true'
    
    if use_windows_auth:
        # Windows Authentication (Trusted Connection)
        conn_str = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;'
    else:
        # SQL Server Authentication
        username = os.getenv('DB_USERNAME', 'sa')
        password = os.getenv('DB_PASSWORD', '')
        conn_str = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;'
    
    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# Pydantic models
class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., max_length=200)

class Member(MemberCreate):
    id: int

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=120)
    copies: int = Field(..., ge=0)

class Book(BookCreate):
    id: int

class LoanBorrow(BaseModel):
    member_id: int = Field(..., gt=0)
    book_id: int = Field(..., gt=0)
    days: int = Field(..., ge=1, le=365)

class LoanReturn(BaseModel):
    loan_id: int = Field(..., gt=0)

class Loan(BaseModel):
    id: int
    member_id: int
    book_id: int
    loan_date: str
    due_date: str
    return_date: Optional[str] = None

# API Endpoints

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

@app.get("/members")
async def serve_members():
    return FileResponse("static/members.html")

@app.get("/loans")
async def serve_loans():
    return FileResponse("static/loans.html")

# Members API
@app.get("/api/members", response_model=List[Member])
async def get_members():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Id, Name, Email FROM dbo.Members ORDER BY Name")
        rows = cursor.fetchall()
        conn.close()
        
        members = [{"id": row[0], "name": row[1], "email": row[2]} for row in rows]
        return JSONResponse(content=members, headers={"Cache-Control": "no-cache"})
    except Exception as e:
        logger.error(f"Error fetching members: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/members", status_code=status.HTTP_201_CREATED)
async def create_member(member: MemberCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute("SELECT Id FROM dbo.Members WHERE Email = ?", member.email)
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail="Email already exists")
        
        # Insert member
        cursor.execute(
            "INSERT INTO dbo.Members (Name, Email) OUTPUT INSERTED.Id VALUES (?, ?)",
            member.name, member.email
        )
        member_id = cursor.fetchone()[0] # type: ignore
        conn.commit()
        conn.close()
        
        return JSONResponse(
            content={"id": member_id, "name": member.name, "email": member.email},
            status_code=201,
            headers={
                "Location": f"/api/members/{member_id}",
                "Content-Type": "application/json"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating member: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Books API
@app.get("/api/books")
async def get_books(author: Optional[str] = None, page: int = 1, pageSize: int = 20):
    if page < 1 or pageSize < 1 or pageSize > 100:
        raise HTTPException(status_code=400, detail="Invalid pagination parameters")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        offset = (page - 1) * pageSize
        
        if author:
            query = """
                SELECT Id, Title, Author, Copies 
                FROM dbo.Books 
                WHERE Author LIKE ? 
                ORDER BY Title 
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            cursor.execute(query, f"%{author}%", offset, pageSize)
        else:
            query = """
                SELECT Id, Title, Author, Copies 
                FROM dbo.Books 
                ORDER BY Title 
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """
            cursor.execute(query, offset, pageSize)
        
        rows = cursor.fetchall()
        
        # Get available copies for each book
        books = []
        for row in rows:
            book_id = row[0]
            cursor.execute(
                "SELECT COUNT(*) FROM dbo.Loans WHERE BookId = ? AND ReturnDate IS NULL",
                book_id
            )
            borrowed = cursor.fetchone()[0] # type: ignore
            available = row[3] - borrowed
            
            books.append({
                "id": book_id,
                "title": row[1],
                "author": row[2],
                "copies": row[3],
                "available": available
            })
        
        conn.close()
        return JSONResponse(content=books, headers={"Cache-Control": "public, max-age=60"})
    except Exception as e:
        logger.error(f"Error fetching books: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/books", status_code=status.HTTP_201_CREATED)
async def create_book(book: BookCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO dbo.Books (Title, Author, Copies) OUTPUT INSERTED.Id VALUES (?, ?, ?)",
            book.title, book.author, book.copies
        )
        book_id = cursor.fetchone()[0] # type: ignore
        conn.commit()
        conn.close()
        
        return JSONResponse(
            content={"id": book_id, "title": book.title, "author": book.author, "copies": book.copies},
            status_code=201,
            headers={
                "Location": f"/api/books/{book_id}",
                "Content-Type": "application/json"
            }
        )
    except Exception as e:
        logger.error(f"Error creating book: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Loans API
@app.get("/api/loans")
async def get_loans():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                l.Id, l.MemberId, l.BookId, 
                CONVERT(VARCHAR(10), l.LoanDate, 23) as LoanDate,
                CONVERT(VARCHAR(10), l.DueDate, 23) as DueDate,
                CONVERT(VARCHAR(10), l.ReturnDate, 23) as ReturnDate,
                m.Name as MemberName,
                b.Title as BookTitle
            FROM dbo.Loans l
            JOIN dbo.Members m ON l.MemberId = m.Id
            JOIN dbo.Books b ON l.BookId = b.Id
            ORDER BY l.LoanDate DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        loans = []
        for row in rows:
            loans.append({
                "id": row[0],
                "member_id": row[1],
                "book_id": row[2],
                "loan_date": row[3],
                "due_date": row[4],
                "return_date": row[5] if row[5] else None,
                "member_name": row[6],
                "book_title": row[7]
            })
        
        return JSONResponse(content=loans, headers={"Cache-Control": "no-cache"})
    except Exception as e:
        logger.error(f"Error fetching loans: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/loans/borrow", status_code=status.HTTP_201_CREATED)
async def borrow_book(loan: LoanBorrow):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if member exists
        cursor.execute("SELECT Id FROM dbo.Members WHERE Id = ?", loan.member_id)
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Check if book exists
        cursor.execute("SELECT Copies FROM dbo.Books WHERE Id = ?", loan.book_id)
        book_row = cursor.fetchone()
        if not book_row:
            conn.close()
            raise HTTPException(status_code=404, detail="Book not found")
        
        total_copies = book_row[0]
        
        # Check availability
        cursor.execute(
            "SELECT COUNT(*) FROM dbo.Loans WHERE BookId = ? AND ReturnDate IS NULL",
            loan.book_id
        )
        borrowed_count = cursor.fetchone()[0] # type: ignore
        
        if borrowed_count >= total_copies:
            conn.close()
            raise HTTPException(status_code=409, detail="No copies available")
        
        # Create loan
        loan_date = datetime.now()
        due_date = loan_date + timedelta(days=loan.days)
        
        cursor.execute(
            """INSERT INTO dbo.Loans (MemberId, BookId, LoanDate, DueDate) 
               OUTPUT INSERTED.Id 
               VALUES (?, ?, ?, ?)""",
            loan.member_id, loan.book_id, loan_date, due_date
        )
        loan_id = cursor.fetchone()[0] # type: ignore
        conn.commit() 
        conn.close()
        
        return JSONResponse(
            content={
                "id": loan_id,
                "member_id": loan.member_id,
                "book_id": loan.book_id,
                "loan_date": loan_date.strftime("%Y-%m-%d"),
                "due_date": due_date.strftime("%Y-%m-%d")
            },
            status_code=201,
            headers={
                "Location": f"/api/loans/{loan_id}",
                "Content-Type": "application/json"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error borrowing book: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/loans/return")
async def return_book(loan_return: LoanReturn):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if loan exists and is not returned
        cursor.execute(
            "SELECT Id, ReturnDate FROM dbo.Loans WHERE Id = ?",
            loan_return.loan_id
        )
        loan_row = cursor.fetchone()
        
        if not loan_row:
            conn.close()
            raise HTTPException(status_code=404, detail="Loan not found")
        
        if loan_row[1]:
            conn.close()
            raise HTTPException(status_code=409, detail="Book already returned")
        
        # Update return date
        return_date = datetime.now()
        cursor.execute(
            "UPDATE dbo.Loans SET ReturnDate = ? WHERE Id = ?",
            return_date, loan_return.loan_id
        )
        conn.commit()
        conn.close()
        
        return JSONResponse(
            content={
                "id": loan_return.loan_id,
                "return_date": return_date.strftime("%Y-%m-%d"),
                "message": "Book returned successfully"
            },
            headers={"Content-Type": "application/json"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error returning book: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/loans/overdue")
async def get_overdue_loans():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                l.Id, l.MemberId, l.BookId, 
                CONVERT(VARCHAR(10), l.LoanDate, 23) as LoanDate,
                CONVERT(VARCHAR(10), l.DueDate, 23) as DueDate,
                m.Name as MemberName,
                b.Title as BookTitle,
                DATEDIFF(day, l.DueDate, GETDATE()) as DaysOverdue
            FROM dbo.Loans l
            JOIN dbo.Members m ON l.MemberId = m.Id
            JOIN dbo.Books b ON l.BookId = b.Id
            WHERE l.ReturnDate IS NULL AND l.DueDate < GETDATE()
            ORDER BY l.DueDate ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        overdue_loans = []
        for row in rows:
            overdue_loans.append({
                "id": row[0],
                "member_id": row[1],
                "book_id": row[2],
                "loan_date": row[3],
                "due_date": row[4],
                "member_name": row[5],
                "book_title": row[6],
                "days_overdue": row[7]
            })
        
        return JSONResponse(content=overdue_loans, headers={"Cache-Control": "no-cache"})
    except Exception as e:
        logger.error(f"Error fetching overdue loans: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host=host, port=port)
