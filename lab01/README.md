# System Biblioteczny

System zarządzania biblioteką z backendem w Pythonie (FastAPI) i bazą danych MS SQL Server.


## Wymagania

Przed uruchomieniem potrzebne są:

- Python 3.12
- MS SQL Server
- ODBC Driver 17 for SQL Server


## Uruchomienie aplikacji

### Krok 1: Konfiguracja srodowiska

Utwórz plik `.env` w katalogu projektu:

```env
DB_SERVER=localhost
DB_DATABASE=TI_Lab1
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
CREATE DATABASE TI_Lab1;
```

### Krok 4: Inicjalizacja schematu i danych

```bash
python reset_db.py
```

Ten skrypt utworzy tabele i wstawi przykladowe dane.

### Krok 5: Uruchomienie serwera

```bash
python main.py
```

Aplikacja bedzie dostepna pod adresem: http://localhost:3000

Dostepne strony:
- http://localhost:3000 - Zarzadzanie ksiazkami
- http://localhost:3000/members - Zarzadzanie czlonkami
- http://localhost:3000/loans - Zarzadzanie wypozyczeniami

---

## Baza danych

### Schemat bazy danych (T-SQL)

Ponizszy skrypt tworzy kompletny schemat bazy danych:

```sql
-- Usuwanie istniejacych tabel (jesli istnieja)
IF OBJECT_ID('dbo.Loans', 'U') IS NOT NULL DROP TABLE dbo.Loans;
IF OBJECT_ID('dbo.Books', 'U') IS NOT NULL DROP TABLE dbo.Books;
IF OBJECT_ID('dbo.Members', 'U') IS NOT NULL DROP TABLE dbo.Members;

-- Tabela czlonkow biblioteki
CREATE TABLE dbo.Members (
    Id       INT IDENTITY(1,1) PRIMARY KEY,
    Name     NVARCHAR(100) NOT NULL,
    Email    NVARCHAR(200) NOT NULL UNIQUE
);

-- Tabela ksiazek
CREATE TABLE dbo.Books (
    Id       INT IDENTITY(1,1) PRIMARY KEY,
    Title    NVARCHAR(200) NOT NULL,
    Author   NVARCHAR(120) NOT NULL,
    Copies   INT NOT NULL CONSTRAINT CK_Books_Copies CHECK (Copies >= 0)
);

-- Tabela wypozyczen
CREATE TABLE dbo.Loans (
    Id         INT IDENTITY(1,1) PRIMARY KEY,
    MemberId   INT NOT NULL 
        CONSTRAINT FK_Loans_Members FOREIGN KEY REFERENCES dbo.Members(Id) ON DELETE CASCADE,
    BookId     INT NOT NULL 
        CONSTRAINT FK_Loans_Books FOREIGN KEY REFERENCES dbo.Books(Id) ON DELETE CASCADE,
    LoanDate   DATETIME2(0) NOT NULL 
        CONSTRAINT DF_Loans_LoanDate DEFAULT (SYSUTCDATETIME()),
    DueDate    DATETIME2(0) NOT NULL,
    ReturnDate DATETIME2(0) NULL
);

-- Indeksy dla wydajnosci
CREATE INDEX IX_Loans_Member ON dbo.Loans(MemberId);
CREATE INDEX IX_Loans_Book ON dbo.Loans(BookId) INCLUDE(ReturnDate);
```

### Przykladowe dane

```sql
-- Czlonkowie biblioteki
INSERT INTO dbo.Members (Name, Email) VALUES 
    ('Jan Kowalski', 'jan.kowalski@example.com'),
    ('Anna Nowak', 'anna.nowak@example.com'),
    ('Piotr Wisniewski', 'piotr.wisniewski@example.com'),
    ('Maria Wojcik', 'maria.wojcik@example.com'),
    ('Tomasz Kaminski', 'tomasz.kaminski@example.com');

-- Ksiazki
INSERT INTO dbo.Books (Title, Author, Copies) VALUES 
    ('Pan Tadeusz', 'Adam Mickiewicz', 3),
    ('Quo Vadis', 'Henryk Sienkiewicz', 2),
    ('Lalka', 'Boleslaw Prus', 2),
    ('Wesele', 'Stanislaw Wyspianski', 1),
    ('Ferdydurke', 'Witold Gombrowicz', 2),
    ('Solaris', 'Stanislaw Lem', 4),
    ('Zbrodnia i kara', 'Fiodor Dostojewski', 2),
    ('1984', 'George Orwell', 3),
    ('Wladca Pierscieni', 'J.R.R. Tolkien', 2),
    ('Harry Potter i Kamien Filozoficzny', 'J.K. Rowling', 3);

-- Przykladowe wypozyczenia
INSERT INTO dbo.Loans (MemberId, BookId, LoanDate, DueDate, ReturnDate) VALUES 
    (1, 1, DATEADD(day, -20, GETDATE()), DATEADD(day, -6, GETDATE()), DATEADD(day, -5, GETDATE()));

INSERT INTO dbo.Loans (MemberId, BookId, LoanDate, DueDate) VALUES 
    (2, 6, DATEADD(day, -10, GETDATE()), DATEADD(day, 4, GETDATE())),
    (3, 8, DATEADD(day, -5, GETDATE()), DATEADD(day, 9, GETDATE()));
```

---

## API Endpoints

| Metoda | Endpoint | Opis | Body (JSON) | Kody odpowiedzi |
|--------|----------|------|-------------|-----------------|
| GET | `/api/members` | Lista wszystkich czlonkow | - | 200 |
| POST | `/api/members` | Dodaj nowego czlonka | `{"name": "...", "email": "..."}` | 201, 409 |
| GET | `/api/books` | Lista wszystkich ksiazek | - | 200 |
| POST | `/api/books` | Dodaj nowa ksiazke | `{"title": "...", "author": "...", "copies": 2}` | 201 |
| GET | `/api/loans` | Lista wszystkich wypozyczen | - | 200 |
| POST | `/api/loans/borrow` | Wypozycz ksiazke | `{"member_id": 1, "book_id": 2, "days": 14}` | 201, 404, 409 |
| POST | `/api/loans/return` | Zwroc ksiazke | `{"loan_id": 1}` | 200, 404, 409 |

Kody odpowiedzi:
- 200 - Sukces (dla GET i return)
- 201 - Utworzono zasob
- 404 - Nie znaleziono (czlonek/ksiazka/wypozyczenie nie istnieje)
- 409 - Konflikt (email juz istnieje / brak dostepnych egzemplarzy / ksiazka juz zwrocona)

---

## Typowy przeplyw

Ponizej przedstawiono typowy scenariusz uzycia systemu bibliotecznego:

```
1. Rejestracja czlonka
   POST /api/members
   {"name": "Jan Kowalski", "email": "jan@example.com"}
   --> Odpowiedz: 201 Created, zwraca id nowego czlonka

2. Dodanie ksiazki do katalogu
   POST /api/books
   {"title": "Solaris", "author": "Stanislaw Lem", "copies": 3}
   --> Odpowiedz: 201 Created, zwraca id nowej ksiazki

3. Sprawdzenie dostepnych ksiazek
   GET /api/books
   --> Odpowiedz: 200 OK, lista ksiazek z polem "available"

4. Wypozyczenie ksiazki
   POST /api/loans/borrow
   {"member_id": 1, "book_id": 1, "days": 14}
   --> Odpowiedz: 201 Created, zwraca dane wypozyczenia z terminem zwrotu

5. Sprawdzenie aktywnych wypozyczen
   GET /api/loans
   --> Odpowiedz: 200 OK, lista wypozyczen

6. Zwrot ksiazki
   POST /api/loans/return
   {"loan_id": 1}
   --> Odpowiedz: 200 OK, ksiazka oznaczona jako zwrocona
```

Pelne testy API z przykladowymi zapytaniami znajduja sie w pliku `tests.rest` (wymaga rozszerzenia REST Client w VS Code).

---

## Testy reczne

### Zapytania T-SQL do weryfikacji danych

```sql
-- Wyswietl wszystkich czlonkow
SELECT * FROM dbo.Members;

-- Wyswietl wszystkie ksiazki
SELECT * FROM dbo.Books;

-- Wyswietl wszystkie wypozyczenia z danymi czlonka i ksiazki
SELECT 
    l.Id AS LoanId,
    m.Name AS MemberName,
    b.Title AS BookTitle,
    l.LoanDate,
    l.DueDate,
    l.ReturnDate
FROM dbo.Loans l
JOIN dbo.Members m ON l.MemberId = m.Id
JOIN dbo.Books b ON l.BookId = b.Id
ORDER BY l.LoanDate DESC;

-- Wyswietl aktywne wypozyczenia (niezwrocone)
SELECT 
    m.Name AS Czlonek,
    b.Title AS Ksiazka,
    l.DueDate AS TerminZwrotu,
    CASE 
        WHEN l.DueDate < GETDATE() THEN 'Przeterminowane'
        ELSE 'W terminie'
    END AS Status
FROM dbo.Loans l
JOIN dbo.Members m ON l.MemberId = m.Id
JOIN dbo.Books b ON l.BookId = b.Id
WHERE l.ReturnDate IS NULL;

-- Sprawdz dostepnosc ksiazek
SELECT 
    b.Title,
    b.Author,
    b.Copies AS LacznieEgzemplarzy,
    b.Copies - COUNT(CASE WHEN l.ReturnDate IS NULL THEN 1 END) AS Dostepne
FROM dbo.Books b
LEFT JOIN dbo.Loans l ON b.Id = l.BookId
GROUP BY b.Id, b.Title, b.Author, b.Copies;

-- Znajdz czlonkow z przeterminowanymi wypozyczeniami
SELECT DISTINCT
    m.Name,
    m.Email,
    DATEDIFF(day, l.DueDate, GETDATE()) AS DniSpoznienia
FROM dbo.Members m
JOIN dbo.Loans l ON m.Id = l.MemberId
WHERE l.ReturnDate IS NULL 
  AND l.DueDate < GETDATE();
```

### Testowanie API

Gotowe testy API znajduja sie w pliku `tests.rest`. Aby z nich skorzystac:

1. Zainstaluj rozszerzenie REST Client w VS Code
2. Otworz plik `tests.rest`
3. Klikaj "Send Request" przy poszczegolnych zapytaniach

Plik zawiera testy dla wszystkich endpointow wraz z obsluga zaleznosci miedzy zapytaniami (np. tworzenie czlonka, a potem wypozyczenie ksiazki dla tego czlonka).

---

## Struktura projektu

```
lab01/
├── main.py              # Glowna aplikacja FastAPI
├── reset_db.py          # Skrypt tworzacy schemat i dane
├── requirements.txt     # Zaleznosci Python
├── tests.rest           # Testy API dla REST Client
├── .env                 # Konfiguracja (nie w repozytorium)
└── static/
    ├── index.html       # Strona glowna (ksiazki)
    ├── members.html     # Strona czlonkow
    ├── loans.html       # Strona wypozyczen
    ├── style.css        # Style CSS
    ├── books.js         # Logika strony ksiazek
    ├── members.js       # Logika strony czlonkow
    └── loans.js         # Logika strony wypozyczen
```

---

