# Blog z moderacja komentarzy

System blogowy z dodawaniem komentarzy i reczna moderacja, backendem w Pythonie (FastAPI) i baza danych MS SQL Server.


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
DB_DATABASE=TI_Lab3
DB_DRIVER=ODBC Driver 17 for SQL Server

HOST=127.0.0.1
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
CREATE DATABASE TI_Lab3;
```

### Krok 4: Inicjalizacja schematu i danych

```bash
python reset_db.py
```

Ten skrypt wykona plik `Blog_Schema.sql` - utworzy tabele i wstawi przykladowe posty oraz komentarze.

### Krok 5: Uruchomienie serwera

```bash
python main.py
```

Aplikacja bedzie dostepna pod adresem: http://localhost:3000

Dostepne strony:
- http://localhost:3000 - Lista postow
- http://localhost:3000/post/{id} - Szczegoly posta z komentarzami
- http://localhost:3000/moderate - Panel moderacji komentarzy

---

## Baza danych

### Schemat bazy danych (T-SQL)

Ponizszy skrypt tworzy kompletny schemat bazy danych:

```sql
-- Usuwanie istniejacych tabel (jesli istnieja)
IF OBJECT_ID('dbo.Comments', 'U') IS NOT NULL DROP TABLE dbo.Comments;
IF OBJECT_ID('dbo.Posts', 'U') IS NOT NULL DROP TABLE dbo.Posts;

-- Tabela postow
CREATE TABLE dbo.Posts (
    Id        INT IDENTITY(1,1) PRIMARY KEY,
    Title     NVARCHAR(200) NOT NULL,
    Body      NVARCHAR(MAX) NOT NULL,
    CreatedAt DATETIME2(0) NOT NULL CONSTRAINT DF_Posts_CreatedAt DEFAULT (SYSUTCDATETIME())
);

-- Tabela komentarzy
CREATE TABLE dbo.Comments (
    Id        INT IDENTITY(1,1) PRIMARY KEY,
    PostId    INT NOT NULL 
        CONSTRAINT FK_Comments_Posts FOREIGN KEY REFERENCES dbo.Posts(Id) ON DELETE CASCADE,
    Author    NVARCHAR(100) NOT NULL,
    Body      NVARCHAR(1000) NOT NULL,
    CreatedAt DATETIME2(0) NOT NULL CONSTRAINT DF_Comments_CreatedAt DEFAULT (SYSUTCDATETIME()),
    Approved  BIT NOT NULL CONSTRAINT DF_Comments_Approved DEFAULT (0)
);

-- Indeks dla wydajnosci
CREATE INDEX IX_Comments_Post ON dbo.Comments(PostId) INCLUDE(Approved, CreatedAt);
```

### Przykladowe dane

```sql
-- Posty
INSERT INTO dbo.Posts (Title, Body) VALUES 
    (N'Witaj w blogu!', N'To jest pierwszy post na naszym blogu. Mozesz dodawac komentarze, ktore zostana zatwierdzone przez moderatora.'),
    (N'Jak dziala moderacja?', N'Kazdy komentarz jest domyslnie niezatwierdzony. Moderator musi go zaakceptowac, aby byl widoczny dla innych uzytkownikow.');

-- Komentarze (przykladowe - niektore zatwierdzone, niektore nie)
INSERT INTO dbo.Comments (PostId, Author, Body, Approved) VALUES 
    (1, N'Jan Kowalski', N'Super blog!', 1),
    (1, N'Anna Nowak', N'Czekam na wiecej postow', 0),
    (2, N'Piotr Wisniewski', N'Swietnie wyjasione', 1);
```

### Logika moderacji

- Nowe komentarze maja domyslnie `Approved = 0` (niezatwierdzone)
- Tylko komentarze z `Approved = 1` sa widoczne publicznie
- Moderator moze zatwierdzic komentarz przez endpoint `/api/comments/{id}/approve`

---

## API Endpoints

| Metoda | Endpoint | Opis | Body (JSON) | Kody odpowiedzi |
|--------|----------|------|-------------|-----------------|
| GET | `/api/posts` | Lista wszystkich postow | - | 200 |
| POST | `/api/posts` | Dodaj nowy post | `{"title": "...", "body": "..."}` | 201 |
| GET | `/api/posts/{id}/comments` | Zatwierdzone komentarze do posta | - | 200, 404 |
| POST | `/api/posts/{id}/comments` | Dodaj komentarz (approved=0) | `{"author": "...", "body": "..."}` | 201, 404 |
| GET | `/api/comments/pending` | Komentarze oczekujace na moderacje | - | 200 |
| POST | `/api/comments/{id}/approve` | Zatwierdz komentarz | - | 200, 404 |

Kody odpowiedzi:
- 200 - Sukces
- 201 - Utworzono zasob (post, komentarz)
- 404 - Nie znaleziono (post/komentarz nie istnieje)

---

## Typowy przeplyw

### Scenariusz uzytkownika (dodawanie komentarza):

```
1. Przegladanie postow
   GET /api/posts
   --> Odpowiedz: 200 OK, lista postow

2. Wyswietlenie posta ze szczegolami
   GET /api/posts/1/comments
   --> Odpowiedz: 200 OK, lista ZATWIERDZONYCH komentarzy

3. Dodanie komentarza
   POST /api/posts/1/comments
   {"author": "Jan Kowalski", "body": "Swietny post!"}
   --> Odpowiedz: 201 Created, approved=false
   --> Komentarz NIE jest jeszcze widoczny publicznie
```

### Scenariusz moderatora:

```
1. Pobranie listy oczekujacych komentarzy
   GET /api/comments/pending
   --> Odpowiedz: 200 OK, lista niezatwierdzonych komentarzy

2. Zatwierdzenie komentarza
   POST /api/comments/1/approve
   --> Odpowiedz: 200 OK
   --> Komentarz jest teraz widoczny publicznie
```

Pelne testy API z przykladowymi zapytaniami znajduja sie w pliku `tests.rest` (wymaga rozszerzenia REST Client w VS Code).

---

## Testy reczne

### Zapytania T-SQL do weryfikacji danych

```sql
-- Wyswietl wszystkie posty
SELECT * FROM dbo.Posts ORDER BY CreatedAt DESC;

-- Wyswietl wszystkie komentarze z tytulami postow
SELECT 
    c.Id,
    p.Title AS PostTitle,
    c.Author,
    c.Body,
    c.CreatedAt,
    CASE WHEN c.Approved = 1 THEN 'Zatwierdzony' ELSE 'Oczekujacy' END AS Status
FROM dbo.Comments c
JOIN dbo.Posts p ON c.PostId = p.Id
ORDER BY c.CreatedAt DESC;

-- Wyswietl tylko komentarze oczekujace na moderacje
SELECT 
    c.Id,
    p.Title AS PostTitle,
    c.Author,
    c.Body,
    c.CreatedAt
FROM dbo.Comments c
JOIN dbo.Posts p ON c.PostId = p.Id
WHERE c.Approved = 0
ORDER BY c.CreatedAt ASC;

-- Statystyki komentarzy dla kazdego posta
SELECT 
    p.Id,
    p.Title,
    COUNT(c.Id) AS LacznieKomentarzy,
    SUM(CASE WHEN c.Approved = 1 THEN 1 ELSE 0 END) AS Zatwierdzone,
    SUM(CASE WHEN c.Approved = 0 THEN 1 ELSE 0 END) AS Oczekujace
FROM dbo.Posts p
LEFT JOIN dbo.Comments c ON p.Id = c.PostId
GROUP BY p.Id, p.Title;

-- Zatwierdz wszystkie oczekujace komentarze (uwaga - operacja masowa)
-- UPDATE dbo.Comments SET Approved = 1 WHERE Approved = 0;
```

### Testowanie API

Gotowe testy API znajduja sie w pliku `tests.rest`. Aby z nich skorzystac:

1. Zainstaluj rozszerzenie REST Client w VS Code
2. Otworz plik `tests.rest`
3. Klikaj "Send Request" przy poszczegolnych zapytaniach

Plik zawiera testy dla wszystkich endpointow, w tym scenariusze bledow (nieistniejacy post, nieistniejacy komentarz).

---

## Struktura projektu

```
lab03/
├── main.py              # Glowna aplikacja FastAPI
├── reset_db.py          # Skrypt wykonujacy Blog_Schema.sql
├── Blog_Schema.sql      # Schemat bazy danych i dane poczatkowe
├── requirements.txt     # Zaleznosci Python
├── tests.rest           # Testy API dla REST Client
├── .env                 # Konfiguracja (nie w repozytorium)
└── static/
    ├── index.html       # Strona glowna (lista postow)
    ├── post.html        # Strona szczegolowa posta
    ├── moderate.html    # Panel moderacji
    ├── style.css        # Style CSS
    ├── blog.js          # Logika strony glownej
    ├── post.js          # Logika strony posta
    └── moderate.js      # Logika panelu moderacji
```

---

## Technologie

- Backend: Python 3.12, FastAPI, Uvicorn
- Baza danych: MS SQL Server, pyodbc
- Frontend: HTML5, CSS3, JavaScript
- Walidacja: Pydantic
- Srodowisko: python-dotenv
