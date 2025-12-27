import os
import logging
import pyodbc
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Blog API")

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
class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)

class CommentCreate(BaseModel):
    author: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=1000)

# HTML routes
@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

@app.get("/post/{post_id}")
async def serve_post():
    return FileResponse("static/post.html")

@app.get("/moderate")
async def serve_moderate():
    return FileResponse("static/moderate.html")

# Posts API
@app.get("/api/posts")
async def get_posts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Id, Title, Body, CreatedAt FROM dbo.Posts ORDER BY CreatedAt DESC")
        rows = cursor.fetchall()
        conn.close()
        
        posts = [{
            "id": row[0],
            "title": row[1],
            "body": row[2],
            "created_at": row[3].isoformat() if row[3] else None
        } for row in rows]
        
        return JSONResponse(content=posts, headers={"Cache-Control": "public, max-age=60"})
    except Exception as e:
        logger.error(f"Error fetching posts: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/posts", status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO dbo.Posts (Title, Body) OUTPUT INSERTED.Id VALUES (?, ?)",
            post.title, post.body
        )
        post_id = cursor.fetchone()[0] # type: ignore
        conn.commit()
        conn.close()
        
        return JSONResponse(
            content={"id": post_id, "title": post.title, "body": post.body},
            status_code=201,
            headers={
                "Location": f"/api/posts/{post_id}",
                "Content-Type": "application/json"
            }
        )
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Comments API
@app.get("/api/posts/{post_id}/comments")
async def get_comments(post_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify post exists
        cursor.execute("SELECT Id FROM dbo.Posts WHERE Id = ?", post_id)
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Get approved comments
        cursor.execute(
            """SELECT Id, PostId, Author, Body, CreatedAt, Approved 
               FROM dbo.Comments 
               WHERE PostId = ? AND Approved = 1 
               ORDER BY CreatedAt DESC""",
            post_id
        )
        rows = cursor.fetchall()
        conn.close()
        
        comments = [{
            "id": row[0],
            "post_id": row[1],
            "author": row[2],
            "body": row[3],
            "created_at": row[4].isoformat() if row[4] else None,
            "approved": bool(row[5])
        } for row in rows]
        
        return JSONResponse(content=comments, headers={"Cache-Control": "no-cache"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching comments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_comment(post_id: int, comment: CommentCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify post exists
        cursor.execute("SELECT Id FROM dbo.Posts WHERE Id = ?", post_id)
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Post not found")
        
        cursor.execute(
            "INSERT INTO dbo.Comments (PostId, Author, Body) OUTPUT INSERTED.Id VALUES (?, ?, ?)",
            post_id, comment.author, comment.body
        )
        comment_id = cursor.fetchone()[0]  # type: ignore
        conn.commit() 
        conn.close()
        
        return JSONResponse(
            content={
                "id": comment_id,
                "post_id": post_id,
                "author": comment.author,
                "body": comment.body,
                "approved": False
            },
            status_code=201,
            headers={
                "Location": f"/api/comments/{comment_id}",
                "Content-Type": "application/json"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Moderation API
@app.get("/api/comments/pending")
async def get_pending_comments():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT c.Id, c.PostId, p.Title, c.Author, c.Body, c.CreatedAt 
               FROM dbo.Comments c
               JOIN dbo.Posts p ON c.PostId = p.Id
               WHERE c.Approved = 0 
               ORDER BY c.CreatedAt DESC"""
        )
        rows = cursor.fetchall()
        conn.close()
        
        comments = [{
            "id": row[0],
            "post_id": row[1],
            "post_title": row[2],
            "author": row[3],
            "body": row[4],
            "created_at": row[5].isoformat() if row[5] else None
        } for row in rows]
        
        return JSONResponse(content=comments, headers={"Cache-Control": "no-cache"})
    except Exception as e:
        logger.error(f"Error fetching pending comments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/comments/{comment_id}/approve")
async def approve_comment(comment_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT Id FROM dbo.Comments WHERE Id = ?", comment_id)
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Comment not found")
        
        cursor.execute("UPDATE dbo.Comments SET Approved = 1 WHERE Id = ?", comment_id)
        conn.commit()
        conn.close()
        
        return JSONResponse(content={"message": "Comment approved", "id": comment_id})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving comment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host=host, port=port)
