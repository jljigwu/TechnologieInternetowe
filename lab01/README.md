# 📚 System Biblioteczny - Library Management System

System zarządzania biblioteką z backendem w Pythonie (FastAPI) i bazą danych MS SQL Server.

---

## 🚀 Jak uruchomić projekt?

### Krok 1: Wymagania wstępne
Upewnij się, że masz zainstalowane:
- **Python 3.8 lub nowszy** 
- **MS SQL Server**
- **ODBC Driver 17 for SQL Server** 

### Krok 2: Sklonujprojekt
```bash
git clone "git..."
```

### Krok 3: Utwórz plik .env
Stwórz plik`.env` z następującymi danymi:
```env
DB_SERVER= 
DB_DATABASE= 
DB_DRIVER=ODBC Driver 17 for SQL Server

HOST=0.0.0.0
PORT=3000
```

**Opcja A - Windows Authentication (zalecane):**
```env
DB_USE_WINDOWS_AUTH=True
```

**Opcja B - SQL Server Authentication:**
```env
DB_USE_WINDOWS_AUTH=False
DB_USERNAME=
DB_PASSWORD=
```

### Krok 4: Zainstaluj zależności Python
```bash
pip install -r requirements.txt
```

### Krok 5: Utwórz bazę danych
Połącz się z SQL Server i wykonaj:
```sql
CREATE DATABASE TI_Lab1;
```

Następnie uruchom skrypt inicjalizujący:
```bash
python reset_db.py
```

### Krok 6: Uruchom aplikację
```bash
python main.py
```

Aplikacja będzie dostępna pod adresem: **http://localhost:3000**

### ✅ Gotowe!
Otwórz przeglądarkę i wejdź na:
- **http://localhost:3000** - Książki
- **http://localhost:3000/members** - Członkowie
- **http://localhost:3000/loans** - Wypożyczenia

---






## 🚀 Funkcjonalności

### API Endpoints

#### Members (Członkowie)
- `GET /api/members` - Lista wszystkich członków
- `POST /api/members` - Dodaj nowego członka
  ```json
  {
    "name": "Ala Nowak",
    "email": "ala@example.com"
  }
  ```
  - **201**: Utworzono pomyślnie
  - **409**: Email już istnieje

#### Books (Książki)
- `GET /api/books` - Lista książek
- `POST /api/books` - Dodaj nową książkę
  ```json
  {
    "title": "Potop",
    "author": "Jan Kowalski",
    "copies": 2
  }
  ```
  - **201**: Utworzono pomyślnie

#### Loans (Wypożyczenia)
- `GET /api/loans` - Lista wszystkich wypożyczeń
- `POST /api/loans/borrow` - Wypożycz książkę
  ```json
  {
    "member_id": 1,
    "book_id": 2,
    "days": 14
  }
  ```
  - **201**: Wypożyczono pomyślnie
  - **404**: Nie znaleziono członka/książki
  - **409**: Brak dostępnych egzemplarzy

- `POST /api/loans/return` - Zwróć książkę
  ```json
  {
    "loan_id": 123
  }
  ```
  - **200**: Zwrócono pomyślnie
  - **404**: Nie znaleziono wypożyczenia
  - **409**: Książka już zwrócona

### UI (Interfejs użytkownika)

- **/** - Książki + dostępność + formularz wypożyczenia
- **/members** - Lista członków + dodawanie nowego członka
- **/loans** - Aktywne/zwrócone wypożyczenia + akcja "Zwróć"

s
## 🗄️ Schema Bazy Danych (T-SQL)

```sql
CREATE TABLE dbo.Members (
  Id       INT IDENTITY(1,1) PRIMARY KEY,
  Name     NVARCHAR(100) NOT NULL,
  Email    NVARCHAR(200) NOT NULL UNIQUE
);

CREATE TABLE dbo.Books (
  Id       INT IDENTITY(1,1) PRIMARY KEY,
  Title    NVARCHAR(200) NOT NULL,
  Author   NVARCHAR(120) NOT NULL,
  Copies   INT NOT NULL CONSTRAINT CK_Books_Copies CHECK (Copies >= 0)
);

CREATE TABLE dbo.Loans (
  Id         INT IDENTITY(1,1) PRIMARY KEY,
  MemberId   INT NOT NULL CONSTRAINT FK_Loans_Members FOREIGN KEY REFERENCES dbo.Members(Id) ON DELETE CASCADE,
  BookId     INT NOT NULL CONSTRAINT FK_Loans_Books   FOREIGN KEY REFERENCES dbo.Books(Id)   ON DELETE CASCADE,
  LoanDate   DATETIME2(0) NOT NULL CONSTRAINT DF_Loans_LoanDate DEFAULT (SYSUTCDATETIME()),
  DueDate    DATETIME2(0) NOT NULL,
  ReturnDate DATETIME2(0) NULL
);

CREATE INDEX IX_Loans_Member ON dbo.Loans(MemberId);
CREATE INDEX IX_Loans_Book   ON dbo.Loans(BookId) INCLUDE(ReturnDate);
```

##  Struktura Projektu

```
TI/
├── main.py                 # Główna aplikacja FastAPI
├── reset_db.py             # Skrypt resetowania bazy danych
├── requirements.txt        # Zależności Python
├── package.json            # Konfiguracja npm i skrypty
├── .env                    # Konfiguracja środowiska (nie w repo)
├── .env.example            # Przykładowa konfiguracja
└── static/                 # Frontend
    ├── index.html          # Strona główna (książki)
    ├── members.html        # Strona członków
    ├── loans.html          # Strona wypożyczeń
    ├── style.css           # Style CSS
    ├── books.js            # Logika strony książek
    ├── members.js          # Logika strony członków
    └── loans.js            # Logika strony wypożyczeń
```

## Implementacja Wymagań

### Walidacja danych
- ✅ Walidacja po stronie backendu (Pydantic models)
- ✅ Statusy HTTP: 400 (Bad Request), 404 (Not Found), 409 (Conflict), 422 (Validation Error), 500 (Server Error)

### Bezpieczeństwo
- ✅ `X-Content-Type-Options: nosniff`
- ✅ `Content-Security-Policy`
- ✅ `Referrer-Policy: strict-origin-when-cross-origin`

### HTTP
- ✅ Poprawne `Content-Type: application/json`
- ✅ `Location` header przy 201 Created
- ✅ `Cache-Control` headers

### Jakość kodu
- ✅ Logowanie żądań (middleware)
- ✅ Rozsądna struktura plików
- ✅ Czytelny README z instrukcją uruchomienia

### Logika biznesowa
- ✅ Walidacja dostępności książek przed wypożyczeniem
- ✅ Unikalność e-maila z obsługą błędu 409
- ✅ Daty w formacie YYYY-MM-DD
- ✅ Logika terminów po stronie serwera

## 🛠️ Technologie

- **Backend**: Python 3.x, FastAPI, Uvicorn
- **Database**: MS SQL Server, pyodbc
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Validation**: Pydantic
- **Environment**: python-dotenv

## 📝 Przykładowe Użycie API

### Dodaj członka

```bash
curl -X POST http://localhost:3000/api/members \
  -H "Content-Type: application/json" \
  -d '{"name":"Jan Kowalski","email":"jan@example.com"}'
```

### Pobierz książki

```bash
curl http://localhost:3000/api/books
```

### Wypożycz książkę

```bash
curl -X POST http://localhost:3000/api/loans/borrow \
  -H "Content-Type: application/json" \
  -d '{"member_id":1,"book_id":2,"days":14}'
```

### Zwróć książkę

```bash
curl -X POST http://localhost:3000/api/loans/return \
  -H "Content-Type: application/json" \
  -d '{"loan_id":1}'
```

