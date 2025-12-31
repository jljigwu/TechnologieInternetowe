# Sklep internetowy

System sklepu internetowego z koszykiem zakupowym, backendem w Pythonie (FastAPI) i bazą danych MS SQL Server.


## Wymagania

Przed uruchomieniem upewnij sie, ze masz zainstalowane:

- Python 3.12
- MS SQL Server
- ODBC Driver 17 for SQL Server

---

## Uruchomienie aplikacji

### Krok 1: Konfiguracja srodowiska

Utworz plik `.env` w katalogu projektu:

```env
DB_SERVER=localhost
DB_DATABASE=TI_Lab2
DB_DRIVER=ODBC Driver 17 for SQL Server

HOST=0.0.0.0
PORT=3000
```

Dla uwierzytelniania Windows (zalecane):
```env
DB_USE_WINDOWS_AUTH=True
```

Dla uwierzytelniania SQL Server:
```env
DB_USE_WINDOWS_AUTH=False
DB_USERNAME=twoj_login
DB_PASSWORD=twoje_haslo
```

### Krok 2: Instalacja zaleznosci

```bash
pip install -r requirements.txt
```

### Krok 3: Utworzenie bazy danych

Polacz sie z SQL Server (np. przez SSMS) i wykonaj:

```sql
CREATE DATABASE TI_Lab2;
```

### Krok 4: Inicjalizacja schematu i danych

```bash
python reset_db.py
```

Ten skrypt wykona plik `Shop_Schema.sql` - utworzy tabele i wstawi przykladowe produkty.

### Krok 5: Uruchomienie serwera

```bash
python main.py
```

Aplikacja bedzie dostepna pod adresem: http://localhost:3000

Dostepne strony:
- http://localhost:3000 - Lista produktow
- http://localhost:3000/cart - Koszyk zakupowy

---

## Baza danych

### Schemat bazy danych (T-SQL)

Ponizszy skrypt tworzy kompletny schemat bazy danych:

```sql
-- Usuwanie istniejacych tabel (jesli istnieja)
IF OBJECT_ID('dbo.OrderItems', 'U') IS NOT NULL DROP TABLE dbo.OrderItems;
IF OBJECT_ID('dbo.Orders', 'U') IS NOT NULL DROP TABLE dbo.Orders;
IF OBJECT_ID('dbo.Products', 'U') IS NOT NULL DROP TABLE dbo.Products;

-- Tabela produktow
CREATE TABLE dbo.Products (
    Id    INT IDENTITY(1,1) PRIMARY KEY,
    Name  NVARCHAR(120) NOT NULL,
    Price DECIMAL(12,2) NOT NULL CONSTRAINT CK_Products_Price CHECK (Price >= 0)
);

-- Tabela zamowien
CREATE TABLE dbo.Orders (
    Id        INT IDENTITY(1,1) PRIMARY KEY,
    CreatedAt DATETIME2(0) NOT NULL CONSTRAINT DF_Orders_CreatedAt DEFAULT (SYSUTCDATETIME())
);

-- Tabela pozycji zamowienia
CREATE TABLE dbo.OrderItems (
    Id        INT IDENTITY(1,1) PRIMARY KEY,
    OrderId   INT NOT NULL 
        CONSTRAINT FK_OrderItems_Orders FOREIGN KEY REFERENCES dbo.Orders(Id) ON DELETE CASCADE,
    ProductId INT NOT NULL 
        CONSTRAINT FK_OrderItems_Products FOREIGN KEY REFERENCES dbo.Products(Id),
    Qty       INT NOT NULL CONSTRAINT CK_OrderItems_Qty CHECK (Qty > 0),
    Price     DECIMAL(12,2) NOT NULL
);

-- Indeks dla wydajnosci
CREATE INDEX IX_OrderItems_Order ON dbo.OrderItems(OrderId) INCLUDE(Qty, Price);
```

### Przykladowe dane

```sql
-- Produkty
INSERT INTO dbo.Products (Name, Price) VALUES 
    (N'Kawa ziarnista 1kg', 79.90),
    (N'Kubek porcelanowy', 24.50),
    (N'Notes A5 kropki', 12.00),
    (N'Dlugopis zelowy', 5.99),
    (N'Herbata Earl Grey 100g', 18.50),
    (N'Termos stalowy 0.5L', 45.00);
```

### Uwaga o koszyku

Koszyk zakupowy jest przechowywany w pamieci serwera (slownik `cart_storage`). W produkcyjnej aplikacji nalezy uzyc Redis lub sesji bazodanowej.

---

## API Endpoints

| Metoda | Endpoint | Opis | Body (JSON) | Kody odpowiedzi |
|--------|----------|------|-------------|-----------------|
| GET | `/api/products` | Lista wszystkich produktow | - | 200 |
| POST | `/api/products` | Dodaj nowy produkt | `{"name": "...", "price": 99.99}` | 201 |
| GET | `/api/cart` | Pobierz zawartosc koszyka | - | 200 |
| POST | `/api/cart/add` | Dodaj produkt do koszyka | `{"product_id": 1, "qty": 2}` | 201, 404 |
| PATCH | `/api/cart/item` | Zmien ilosc produktu w koszyku | `{"product_id": 1, "qty": 5}` | 200, 404 |
| DELETE | `/api/cart/item/{id}` | Usun produkt z koszyka | - | 200, 404 |
| POST | `/api/checkout` | Zloz zamowienie | - | 201, 400 |

Kody odpowiedzi:
- 200 - Sukces
- 201 - Utworzono zasob (produkt, pozycja w koszyku, zamowienie)
- 400 - Bledne zadanie (np. pusty koszyk przy checkout)
- 404 - Nie znaleziono (produkt nie istnieje / produkt nie jest w koszyku)

---

## Typowy przeplyw

Ponizej przedstawiono typowy scenariusz zakupowy:

```
1. Przegladanie produktow
   GET /api/products
   --> Odpowiedz: 200 OK, lista produktow z cenami

2. Dodanie produktu do koszyka
   POST /api/cart/add
   {"product_id": 1, "qty": 2}
   --> Odpowiedz: 201 Created

3. Dodanie kolejnego produktu
   POST /api/cart/add
   {"product_id": 3, "qty": 1}
   --> Odpowiedz: 201 Created

4. Sprawdzenie zawartosci koszyka
   GET /api/cart
   --> Odpowiedz: 200 OK, lista pozycji z suma

5. Zmiana ilosci produktu
   PATCH /api/cart/item
   {"product_id": 1, "qty": 3}
   --> Odpowiedz: 200 OK

6. Usuniecie produktu z koszyka
   DELETE /api/cart/item/3
   --> Odpowiedz: 200 OK

7. Finalizacja zamowienia
   POST /api/checkout
   --> Odpowiedz: 201 Created, zwraca order_id i total
   --> Koszyk zostaje wyczyszczony
   --> Zamowienie zapisane w bazie (Orders + OrderItems)
```

Pelne testy API z przykladowymi zapytaniami znajduja sie w pliku `tests.rest` (wymaga rozszerzenia REST Client w VS Code).

---

## Testy reczne

### Zapytania T-SQL do weryfikacji danych

```sql
-- Wyswietl wszystkie produkty
SELECT * FROM dbo.Products;

-- Wyswietl wszystkie zamowienia
SELECT * FROM dbo.Orders ORDER BY CreatedAt DESC;

-- Wyswietl pozycje zamowienia z nazwami produktow
SELECT 
    o.Id AS OrderId,
    o.CreatedAt,
    p.Name AS ProductName,
    oi.Qty,
    oi.Price,
    (oi.Qty * oi.Price) AS Subtotal
FROM dbo.Orders o
JOIN dbo.OrderItems oi ON o.Id = oi.OrderId
JOIN dbo.Products p ON oi.ProductId = p.Id
ORDER BY o.Id DESC, p.Name;

-- Podsumowanie zamowien (suma dla kazdego zamowienia)
SELECT 
    o.Id AS OrderId,
    o.CreatedAt,
    COUNT(oi.Id) AS LiczbaPozycji,
    SUM(oi.Qty) AS LacznaIlosc,
    SUM(oi.Qty * oi.Price) AS Suma
FROM dbo.Orders o
JOIN dbo.OrderItems oi ON o.Id = oi.OrderId
GROUP BY o.Id, o.CreatedAt
ORDER BY o.CreatedAt DESC;

-- Najpopularniejsze produkty (najczesciej zamawiane)
SELECT 
    p.Name,
    SUM(oi.Qty) AS LacznaSprzedaz,
    SUM(oi.Qty * oi.Price) AS Przychod
FROM dbo.Products p
JOIN dbo.OrderItems oi ON p.Id = oi.ProductId
GROUP BY p.Id, p.Name
ORDER BY LacznaSprzedaz DESC;

-- Produkty ktore nigdy nie byly zamowione
SELECT p.Name, p.Price
FROM dbo.Products p
LEFT JOIN dbo.OrderItems oi ON p.Id = oi.ProductId
WHERE oi.Id IS NULL;
```

### Testowanie API

Gotowe testy API znajduja sie w pliku `tests.rest`. Aby z nich skorzystac:

1. Zainstaluj rozszerzenie REST Client w VS Code
2. Otworz plik `tests.rest`
3. Klikaj "Send Request" przy poszczegolnych zapytaniach

Plik zawiera testy dla wszystkich endpointow, w tym scenariusze bledow (pusty koszyk, nieistniejacy produkt).

---

## Struktura projektu

```
lab02/
├── main.py              # Glowna aplikacja FastAPI
├── reset_db.py          # Skrypt wykonujacy Shop_Schema.sql
├── Shop_Schema.sql      # Schemat bazy danych i dane poczatkowe
├── requirements.txt     # Zaleznosci Python
├── tests.rest           # Testy API dla REST Client
├── .env                 # Konfiguracja (nie w repozytorium)
└── static/
    ├── index.html       # Strona glowna (produkty)
    ├── cart.html        # Strona koszyka
    ├── style.css        # Style CSS
    ├── products.js      # Logika strony produktow
    └── cart.js          # Logika strony koszyka
```

---

## Technologie

- Backend: Python 3.12, FastAPI, Uvicorn
- Baza danych: MS SQL Server, pyodbc
- Frontend: HTML5, CSS3, JavaScript
- Walidacja: Pydantic
- Srodowisko: python-dotenv
