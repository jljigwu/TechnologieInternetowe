# Notatnik z tagami

System notatek z wyszukiwaniem i tagowaniem, backendem w Pythonie (FastAPI) i baza danych MS SQL Server.

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
DB_DATABASE=TI_Lab6
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
CREATE DATABASE TI_Lab6;
```

### Krok 4: Inicjalizacja schematu i danych

```bash
python reset_db.py
```

Ten skrypt wykona plik `Notes_Schema.sql` - utworzy tabele i wstawi przykladowe notatki z tagami.

### Krok 5: Uruchomienie serwera

```bash
python main.py
```

Aplikacja bedzie dostepna pod adresem: http://localhost:3000

---

## Baza danych

### Schemat bazy danych (T-SQL)

Ponizszy skrypt tworzy kompletny schemat bazy danych:

```sql
-- Usuwanie istniejacych tabel (jesli istnieja)
IF OBJECT_ID('dbo.NoteTags', 'U') IS NOT NULL DROP TABLE dbo.NoteTags;
IF OBJECT_ID('dbo.Notes', 'U') IS NOT NULL DROP TABLE dbo.Notes;
IF OBJECT_ID('dbo.Tags', 'U') IS NOT NULL DROP TABLE dbo.Tags;

-- Tabela notatek
CREATE TABLE dbo.Notes (
    Id        INT IDENTITY(1,1) PRIMARY KEY,
    Title     NVARCHAR(200) NOT NULL,
    Body      NVARCHAR(MAX) NOT NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETDATE()
);

-- Tabela tagow
CREATE TABLE dbo.Tags (
    Id   INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(50) NOT NULL UNIQUE
);

-- Tabela laczaca (relacja wiele-do-wielu)
CREATE TABLE dbo.NoteTags (
    NoteId INT NOT NULL 
        CONSTRAINT FK_NoteTags_Notes FOREIGN KEY REFERENCES dbo.Notes(Id) ON DELETE CASCADE,
    TagId  INT NOT NULL 
        CONSTRAINT FK_NoteTags_Tags FOREIGN KEY REFERENCES dbo.Tags(Id),
    CONSTRAINT PK_NoteTags PRIMARY KEY (NoteId, TagId)
);

-- Indeksy dla wydajnosci
CREATE INDEX IX_Notes_Title ON dbo.Notes(Title);
CREATE INDEX IX_Notes_CreatedAt ON dbo.Notes(CreatedAt DESC);
CREATE INDEX IX_Tags_Name ON dbo.Tags(Name);
```

### Przykladowe dane

```sql
-- Tagi
INSERT INTO dbo.Tags (Name) VALUES 
    (N'work'),
    (N'home'),
    (N'ideas'),
    (N'shopping'),
    (N'urgent');

-- Notatki
INSERT INTO dbo.Notes (Title, Body, CreatedAt) VALUES 
    (N'Spotkanie z zespolem', N'Omowic postepy w projekcie i zaplanowac nastepne kroki.', DATEADD(day, -2, GETDATE())),
    (N'Lista zakupow', N'Kupic mleko, chleb, maslo, jajka, ser zolty.', DATEADD(day, -1, GETDATE())),
    (N'Pomysl na aplikacje', N'Stworzyc aplikacje do sledzenia nawykow. Uzyc React i Firebase.', DATEADD(hour, -5, GETDATE())),
    (N'Naprawa roweru', N'Oddac rower do serwisu - naprawic hamulce.', GETDATE());

-- Przypisania tagow do notatek
INSERT INTO dbo.NoteTags (NoteId, TagId) VALUES
    (1, 1), -- Spotkanie = work
    (1, 5), -- Spotkanie = urgent
    (2, 2), -- Lista zakupow = home
    (2, 4), -- Lista zakupow = shopping
    (3, 1), -- Pomysl = work
    (3, 3), -- Pomysl = ideas
    (4, 2); -- Naprawa = home
```

### Relacja wiele-do-wielu

- Jedna notatka moze miec wiele tagow
- Jeden tag moze byc przypisany do wielu notatek
- Klucz glowny `(NoteId, TagId)` zapewnia, ze tag moze byc przypisany tylko raz do danej notatki

---

## API Endpoints

| Metoda | Endpoint | Opis | Body (JSON) | Kody odpowiedzi |
|--------|----------|------|-------------|-----------------|
| GET | `/api/notes` | Lista wszystkich notatek | - | 200 |
| GET | `/api/notes?q=...` | Wyszukaj notatki | - | 200 |
| POST | `/api/notes` | Dodaj nowa notatke | `{"title": "...", "body": "..."}` | 201 |
| GET | `/api/tags` | Lista wszystkich tagow | - | 200 |
| POST | `/api/notes/{id}/tags` | Przypisz tagi do notatki | `{"tags": ["work", "urgent"]}` | 200, 404 |

Kody odpowiedzi:
- 200 - Sukces
- 201 - Utworzono notatke
- 404 - Nie znaleziono (notatka nie istnieje)

### Wyszukiwanie

Parametr `q` wyszukuje w tytule i tresci notatki:
```
GET /api/notes?q=projekt
```
Uzywa operatora SQL `LIKE '%...%'` na polach Title i Body.

### Struktura odpowiedzi GET /api/notes

```json
{
  "notes": [
    {
      "id": 1,
      "title": "Spotkanie z zespolem",
      "body": "Omowic postepy w projekcie...",
      "created_at": "2025-12-29T10:00:00",
      "tags": ["work", "urgent"]
    }
  ]
}
```

---

## Typowy przeplyw

Ponizej przedstawiono typowy scenariusz uzycia notatnika:

```
1. Pobranie wszystkich notatek
   GET /api/notes
   --> Odpowiedz: 200 OK, lista notatek z tagami

2. Wyszukanie notatek zawierajacych slowo "projekt"
   GET /api/notes?q=projekt
   --> Odpowiedz: 200 OK, przefiltrowana lista

3. Utworzenie nowej notatki
   POST /api/notes
   {"title": "Nowa notatka", "body": "Tresc notatki..."}
   --> Odpowiedz: 201 Created, notatka bez tagow

4. Pobranie listy dostepnych tagow
   GET /api/tags
   --> Odpowiedz: 200 OK, lista tagow

5. Przypisanie tagow do notatki
   POST /api/notes/5/tags
   {"tags": ["work", "ideas", "nowy-tag"]}
   --> Odpowiedz: 200 OK
   --> Jesli tag "nowy-tag" nie istnieje, zostanie automatycznie utworzony
```

Pelne testy API z przykladowymi zapytaniami znajduja sie w pliku `tests.rest` (wymaga rozszerzenia REST Client w VS Code).

---

## Testy reczne

### Zapytania T-SQL do weryfikacji danych

```sql
-- Wyswietl wszystkie notatki
SELECT * FROM dbo.Notes ORDER BY CreatedAt DESC;

-- Wyswietl wszystkie tagi
SELECT * FROM dbo.Tags ORDER BY Name;

-- Wyswietl notatki z ich tagami
SELECT 
    n.Id,
    n.Title,
    n.CreatedAt,
    STRING_AGG(t.Name, ', ') AS Tags
FROM dbo.Notes n
LEFT JOIN dbo.NoteTags nt ON n.Id = nt.NoteId
LEFT JOIN dbo.Tags t ON nt.TagId = t.Id
GROUP BY n.Id, n.Title, n.CreatedAt
ORDER BY n.CreatedAt DESC;

-- Wyszukaj notatki zawierajace slowo "projekt"
SELECT * FROM dbo.Notes 
WHERE Title LIKE '%projekt%' OR Body LIKE '%projekt%';

-- Notatki z konkretnym tagiem (np. "work")
SELECT n.Id, n.Title, n.CreatedAt
FROM dbo.Notes n
JOIN dbo.NoteTags nt ON n.Id = nt.NoteId
JOIN dbo.Tags t ON nt.TagId = t.Id
WHERE t.Name = 'work'
ORDER BY n.CreatedAt DESC;

-- Liczba notatek dla kazdego tagu
SELECT 
    t.Name AS Tag,
    COUNT(nt.NoteId) AS LiczbaNotatek
FROM dbo.Tags t
LEFT JOIN dbo.NoteTags nt ON t.Id = nt.TagId
GROUP BY t.Id, t.Name
ORDER BY LiczbaNotatek DESC;

-- Tagi ktore nie sa uzywane
SELECT t.Name
FROM dbo.Tags t
LEFT JOIN dbo.NoteTags nt ON t.Id = nt.TagId
WHERE nt.NoteId IS NULL;

-- Notatki bez tagow
SELECT n.Id, n.Title
FROM dbo.Notes n
LEFT JOIN dbo.NoteTags nt ON n.Id = nt.NoteId
WHERE nt.TagId IS NULL;
```

### Testowanie API

Gotowe testy API znajduja sie w pliku `tests.rest`. Aby z nich skorzystac:

1. Zainstaluj rozszerzenie REST Client w VS Code
2. Otworz plik `tests.rest`
3. Klikaj "Send Request" przy poszczegolnych zapytaniach

Plik zawiera testy dla wszystkich endpointow, w tym wyszukiwanie i przypisywanie tagow.

---

## Struktura projektu

```
lab06/
├── main.py              # Glowna aplikacja FastAPI
├── reset_db.py          # Skrypt wykonujacy Notes_Schema.sql
├── Notes_Schema.sql     # Schemat bazy danych i dane poczatkowe
├── requirements.txt     # Zaleznosci Python
├── tests.rest           # Testy API dla REST Client
├── .env                 # Konfiguracja (nie w repozytorium)
└── static/
    ├── index.html       # Strona notatnika
    ├── notes.js         # Logika aplikacji (wyszukiwanie, tagowanie)
    └── style.css        # Style CSS
```

---

## Technologie

- Backend: Python 3.12, FastAPI, Uvicorn
- Baza danych: MS SQL Server, pyodbc
- Frontend: HTML5, CSS3, JavaScript
- Walidacja: Pydantic
- Srodowisko: python-dotenv
