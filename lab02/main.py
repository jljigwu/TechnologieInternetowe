import os
import logging
import pyodbc
from typing import Dict
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Shop API")

# In-memory cart storage (per session - simplified version)
# In production, use Redis or database with session management
cart_storage: Dict[str, Dict[int, int]] = {"default": {}}

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
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    price: float = Field(..., ge=0)

class Product(ProductCreate):
    id: int

class CartAddItem(BaseModel):
    product_id: int = Field(..., gt=0)
    qty: int = Field(..., gt=0)

class CartUpdateItem(BaseModel):
    product_id: int = Field(..., gt=0)
    qty: int = Field(..., gt=0)

# Helper functions
def get_cart_session():
    return "default"

# API Endpoints

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

@app.get("/cart")
async def serve_cart():
    return FileResponse("static/cart.html")

@app.get("/api/products")
async def get_products():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Id, Name, Price FROM dbo.Products ORDER BY Name")
        rows = cursor.fetchall()
        conn.close()
        
        products = [{"id": row[0], "name": row[1], "price": float(row[2])} for row in rows]
        return JSONResponse(content=products, headers={"Cache-Control": "public, max-age=60"})
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/products", status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO dbo.Products (Name, Price) OUTPUT INSERTED.Id VALUES (?, ?)",
            product.name, product.price
        )
        product_id = cursor.fetchone()[0] # type: ignore
        conn.commit()
        conn.close()
        
        return JSONResponse(
            content={"id": product_id, "name": product.name, "price": product.price},
            status_code=201,
            headers={
                "Location": f"/api/products/{product_id}",
                "Content-Type": "application/json"
            }
        )
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/cart")
async def get_cart():
    try:
        session_id = get_cart_session()
        cart = cart_storage.get(session_id, {})
        
        if not cart:
            return JSONResponse(content={"items": [], "total": 0})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        product_ids = list(cart.keys())
        placeholders = ','.join('?' * len(product_ids))
        query = f"SELECT Id, Name, Price FROM dbo.Products WHERE Id IN ({placeholders})"
        cursor.execute(query, product_ids)
        rows = cursor.fetchall()
        conn.close()
        
        items = []
        total = 0
        for row in rows:
            product_id = row[0]
            qty = cart[product_id]
            price = float(row[2])
            subtotal = price * qty
            total += subtotal
            
            items.append({
                "product_id": product_id,
                "product_name": row[1],
                "price": price,
                "qty": qty,
                "subtotal": subtotal
            })
        
        return JSONResponse(
            content={"items": items, "total": round(total, 2)},
            headers={"Cache-Control": "no-cache"}
        )
    except Exception as e:
        logger.error(f"Error fetching cart: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/cart/add", status_code=status.HTTP_201_CREATED)
async def add_to_cart(item: CartAddItem):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Id FROM dbo.Products WHERE Id = ?", item.product_id)
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Product not found")
        conn.close()
        
        session_id = get_cart_session()
        if session_id not in cart_storage:
            cart_storage[session_id] = {}
        
        if item.product_id in cart_storage[session_id]:
            cart_storage[session_id][item.product_id] += item.qty
        else:
            cart_storage[session_id][item.product_id] = item.qty
        
        return JSONResponse(
            content={"message": "Product added to cart", "product_id": item.product_id, "qty": cart_storage[session_id][item.product_id]},
            status_code=201
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.patch("/api/cart/item")
async def update_cart_item(item: CartUpdateItem):
    try:
        session_id = get_cart_session()
        cart = cart_storage.get(session_id, {})
        
        if item.product_id not in cart:
            raise HTTPException(status_code=404, detail="Product not in cart")
        
        if item.qty <= 0:
            raise HTTPException(status_code=422, detail="Quantity must be greater than 0")
        
        cart_storage[session_id][item.product_id] = item.qty
        
        return JSONResponse(
            content={"message": "Cart item updated", "product_id": item.product_id, "qty": item.qty}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cart item: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/cart/item/{product_id}")
async def remove_from_cart(product_id: int):
    try:
        session_id = get_cart_session()
        cart = cart_storage.get(session_id, {})
        
        if product_id not in cart:
            raise HTTPException(status_code=404, detail="Product not in cart")
        
        del cart_storage[session_id][product_id]
        
        return JSONResponse(
            content={"message": "Product removed from cart", "product_id": product_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from cart: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/checkout", status_code=status.HTTP_201_CREATED)
async def checkout():
    try:
        session_id = get_cart_session()
        cart = cart_storage.get(session_id, {})
        
        if not cart:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        product_ids = list(cart.keys())
        placeholders = ','.join('?' * len(product_ids))
        query = f"SELECT Id, Price FROM dbo.Products WHERE Id IN ({placeholders})"
        cursor.execute(query, product_ids)
        rows = cursor.fetchall()
        
        price_map = {row[0]: float(row[1]) for row in rows}
        
        if len(price_map) != len(cart):
            conn.close()
            raise HTTPException(status_code=400, detail="Some products in cart no longer exist")
        
        cursor.execute("INSERT INTO dbo.Orders DEFAULT VALUES; SELECT SCOPE_IDENTITY()")
        order_id = int(cursor.fetchone()[0]) # type: ignore
        
        total = 0
        for product_id, qty in cart.items():
            price = price_map[product_id]
            subtotal = price * qty
            total += subtotal
            
            cursor.execute(
                "INSERT INTO dbo.OrderItems (OrderId, ProductId, Qty, Price) VALUES (?, ?, ?, ?)",
                order_id, product_id, qty, price
            )
        
        conn.commit()
        conn.close()
        
        cart_storage[session_id] = {}
        
        return JSONResponse(
            content={"order_id": order_id, "total": round(total, 2)},
            status_code=201,
            headers={
                "Location": f"/api/orders/{order_id}",
                "Content-Type": "application/json"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during checkout: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(app, host=host, port=port)
