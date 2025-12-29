import os
import logging
import pyodbc
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Notes API")

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response

# CORS - tylko localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_connection():
    server = os.getenv('DB_SERVER', None)
    database = os.getenv('DB_DATABASE', None)
    driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    use_windows_auth = os.getenv('DB_USE_WINDOWS_AUTH', 'True').lower() == 'true'
    
    if use_windows_auth:
        conn_str = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;TrustServerCertificate=yes;'
    else:
        username = os.getenv('DB_USERNAME', None)
        password = os.getenv('DB_PASSWORD', None)
        conn_str = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;'
    
    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# Pydantic models
class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)

class NoteTagsAssign(BaseModel):
    tags: List[str] = Field(..., min_items=1) # type: ignore

# HTML routes
@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

# Notes API
@app.get("/api/notes")
async def get_notes(q: Optional[str] = Query(None)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if q and q.strip():
            search_term = f"%{q}%"
            cursor.execute("""
                SELECT Id, Title, Body, CreatedAt 
                FROM dbo.Notes 
                WHERE Title LIKE ? OR Body LIKE ?
                ORDER BY CreatedAt DESC
            """, search_term, search_term)
        else:
            cursor.execute("""
                SELECT Id, Title, Body, CreatedAt 
                FROM dbo.Notes 
                ORDER BY CreatedAt DESC
            """)
        
        notes_rows = cursor.fetchall()
        
        notes = []
        for row in notes_rows:
            note_id = row[0]
            
            # Get tags for this note
            cursor.execute("""
                SELECT t.Name 
                FROM dbo.Tags t
                JOIN dbo.NoteTags nt ON t.Id = nt.TagId
                WHERE nt.NoteId = ?
            """, note_id)
            
            tags = [tag_row[0] for tag_row in cursor.fetchall()]
            
            notes.append({
                "id": note_id,
                "title": row[1],
                "body": row[2],
                "created_at": row[3].isoformat() if row[3] else None,
                "tags": tags
            })
        
        conn.close()
        
        return JSONResponse(
            content={"notes": notes},
            headers={"Cache-Control": "no-cache"}
        )
    except Exception as e:
        logger.error(f"Error fetching notes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/notes", status_code=status.HTTP_201_CREATED)
async def create_note(note: NoteCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO dbo.Notes (Title, Body) OUTPUT INSERTED.Id, INSERTED.CreatedAt VALUES (?, ?)",
            note.title, note.body
        )
        result = cursor.fetchone()
        note_id = result[0] # type: ignore
        created_at = result[1] # type: ignore
        
        conn.commit()
        conn.close()
        
        return JSONResponse(
            content={
                "id": note_id,
                "title": note.title,
                "body": note.body,
                "created_at": created_at.isoformat() if created_at else None,
                "tags": []
            },
            status_code=201,
            headers={
                "Location": f"/api/notes/{note_id}",
                "Content-Type": "application/json"
            }
        )
    except Exception as e:
        logger.error(f"Error creating note: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Tags API
@app.get("/api/tags")
async def get_tags():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT Id, Name FROM dbo.Tags ORDER BY Name")
        tags_rows = cursor.fetchall()
        
        tags = [{"id": row[0], "name": row[1]} for row in tags_rows]
        
        conn.close()
        
        return JSONResponse(
            content={"tags": tags},
            headers={"Cache-Control": "no-cache"}
        )
    except Exception as e:
        logger.error(f"Error fetching tags: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/notes/{note_id}/tags")
async def assign_tags(note_id: int, assignment: NoteTagsAssign):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify note exists
        cursor.execute("SELECT Id FROM dbo.Notes WHERE Id = ?", note_id)
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Note not found")
        
        assigned_tags = []
        
        for tag_name in assignment.tags:
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue
            
            # Get or create tag
            cursor.execute("SELECT Id FROM dbo.Tags WHERE Name = ?", tag_name)
            tag_row = cursor.fetchone()
            
            if tag_row:
                tag_id = tag_row[0]
            else:
                cursor.execute("INSERT INTO dbo.Tags (Name) OUTPUT INSERTED.Id VALUES (?)", tag_name)
                tag_id = cursor.fetchone()[0] # type: ignore
            
            # Check if assignment already exists
            cursor.execute(
                "SELECT 1 FROM dbo.NoteTags WHERE NoteId = ? AND TagId = ?",
                note_id, tag_id
            )
            
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO dbo.NoteTags (NoteId, TagId) VALUES (?, ?)",
                    note_id, tag_id
                )
                assigned_tags.append(tag_name)
        
        conn.commit()
        conn.close()
        
        return JSONResponse(
            content={
                "note_id": note_id,
                "assigned_tags": assigned_tags
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning tags: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host=host, port=port)
