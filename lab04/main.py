import os
import logging
import pyodbc
from fastapi import FastAPI, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Movie Ratings API")

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
    allow_origins=["http://localhost:3000"],
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
class MovieCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    year: int = Field(..., ge=1888, le=2100)

class RatingCreate(BaseModel):
    movie_id: int = Field(..., gt=0)
    score: int = Field(..., ge=1, le=5)

# HTML routes
@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

# Movies API
@app.get("/api/movies")
async def get_movies():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, Title, [Year], 
                   ISNULL(AvgScore, 0.00) as AvgScore, 
                   ISNULL(Votes, 0) as Votes
            FROM dbo.vMoviesRanking 
            ORDER BY AvgScore DESC, Votes DESC, Title
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        movies = [{
            "id": row[0],
            "title": row[1],
            "year": row[2],
            "avg_score": float(row[3]) if row[3] else 0.0,
            "votes": row[4] if row[4] else 0
        } for row in rows]
        
        return JSONResponse(content=movies, headers={"Cache-Control": "public, max-age=10"})
    except Exception as e:
        logger.error(f"Error fetching movies: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/movies", status_code=status.HTTP_201_CREATED)
async def create_movie(movie: MovieCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO dbo.Movies (Title, [Year]) OUTPUT INSERTED.Id VALUES (?, ?)",
            movie.title, movie.year
        )
        movie_id = cursor.fetchone()[0] # type: ignore
        conn.commit()
        conn.close()
        
        return JSONResponse(
            content={"id": movie_id, "title": movie.title, "year": movie.year},
            status_code=201,
            headers={
                "Location": f"/api/movies/{movie_id}",
                "Content-Type": "application/json"
            }
        )
    except Exception as e:
        logger.error(f"Error creating movie: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Ratings API
@app.post("/api/ratings", status_code=status.HTTP_201_CREATED)
async def create_rating(rating: RatingCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify movie exists
        cursor.execute("SELECT Id FROM dbo.Movies WHERE Id = ?", rating.movie_id)
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Movie not found")
        
        cursor.execute(
            "INSERT INTO dbo.Ratings (MovieId, Score) OUTPUT INSERTED.Id VALUES (?, ?)",
            rating.movie_id, rating.score
        )
        rating_id = cursor.fetchone()[0] # type: ignore
        conn.commit()
        conn.close()
        
        return JSONResponse(
            content={"id": rating_id, "movie_id": rating.movie_id, "score": rating.score},
            status_code=201,
            headers={
                "Location": f"/api/ratings/{rating_id}",
                "Content-Type": "application/json"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating rating: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host=host, port=port)
