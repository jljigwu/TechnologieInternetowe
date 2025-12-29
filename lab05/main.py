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

app = FastAPI(title="Kanban Board API")

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
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    col_id: int = Field(..., gt=0)

class TaskMove(BaseModel):
    col_id: int = Field(..., gt=0)
    ord: int = Field(..., ge=1)

# HTML routes
@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

# Board API
@app.get("/api/board")
async def get_board():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get columns
        cursor.execute("SELECT Id, Name, Ord FROM dbo.Columns ORDER BY Ord")
        cols_rows = cursor.fetchall()
        
        cols = [{
            "id": row[0],
            "name": row[1],
            "ord": row[2]
        } for row in cols_rows]
        
        # Get tasks
        cursor.execute("SELECT Id, Title, ColId, Ord FROM dbo.Tasks ORDER BY ColId, Ord")
        tasks_rows = cursor.fetchall()
        
        tasks = [{
            "id": row[0],
            "title": row[1],
            "col_id": row[2],
            "ord": row[3]
        } for row in tasks_rows]
        
        conn.close()
        
        return JSONResponse(
            content={"cols": cols, "tasks": tasks},
            headers={"Cache-Control": "no-cache"}
        )
    except Exception as e:
        logger.error(f"Error fetching board: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Tasks API
@app.post("/api/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify column exists
        cursor.execute("SELECT Id FROM dbo.Columns WHERE Id = ?", task.col_id)
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Column not found")
        
        # Get max ord in column
        cursor.execute("SELECT ISNULL(MAX(Ord), 0) FROM dbo.Tasks WHERE ColId = ?", task.col_id)
        max_ord = cursor.fetchone()[0] # type: ignore
        new_ord = max_ord + 1
        
        cursor.execute(
            "INSERT INTO dbo.Tasks (Title, ColId, Ord) OUTPUT INSERTED.Id VALUES (?, ?, ?)",
            task.title, task.col_id, new_ord
        )
        task_id = cursor.fetchone()[0] # type: ignore
        conn.commit()
        conn.close()
        
        return JSONResponse(
            content={"id": task_id, "title": task.title, "col_id": task.col_id, "ord": new_ord},
            status_code=201,
            headers={
                "Location": f"/api/tasks/{task_id}",
                "Content-Type": "application/json"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/tasks/{task_id}/move")
async def move_task(task_id: int, move: TaskMove):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify task exists
        cursor.execute("SELECT Id, ColId, Ord FROM dbo.Tasks WHERE Id = ?", task_id)
        task_row = cursor.fetchone()
        if not task_row:
            conn.close()
            raise HTTPException(status_code=404, detail="Task not found")
        
        old_col_id = task_row[1]
        old_ord = task_row[2]
        
        # Verify new column exists
        cursor.execute("SELECT Id FROM dbo.Columns WHERE Id = ?", move.col_id)
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Column not found")
        
        # Update task position
        cursor.execute(
            "UPDATE dbo.Tasks SET ColId = ?, Ord = ? WHERE Id = ?",
            move.col_id, move.ord, task_id
        )
        
        # Reorder tasks in old column if needed
        if old_col_id != move.col_id:
            cursor.execute(
                "UPDATE dbo.Tasks SET Ord = Ord - 1 WHERE ColId = ? AND Ord > ?",
                old_col_id, old_ord
            )
        
        # Adjust ord in new column
        cursor.execute(
            "UPDATE dbo.Tasks SET Ord = Ord + 1 WHERE ColId = ? AND Ord >= ? AND Id != ?",
            move.col_id, move.ord, task_id
        )
        
        conn.commit()
        conn.close()
        
        return JSONResponse(
            content={"id": task_id, "col_id": move.col_id, "ord": move.ord}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host=host, port=port)
