# Tablica Kanban

System tablicy Kanban do zarzadzania zadaniami z backendem w Pythonie (FastAPI) i baza danych MS SQL Server.


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
DB_DATABASE=TI_Lab5
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
CREATE DATABASE TI_Lab5;
```

### Krok 4: Inicjalizacja schematu i danych

```bash
python reset_db.py
```

Ten skrypt wykona plik `Kanban_Schema.sql` - utworzy tabele i wstawi predefiniowane kolumny oraz przykladowe zadania.

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
IF OBJECT_ID('dbo.Tasks', 'U') IS NOT NULL DROP TABLE dbo.Tasks;
IF OBJECT_ID('dbo.Columns', 'U') IS NOT NULL DROP TABLE dbo.Columns;

-- Tabela kolumn tablicy Kanban
CREATE TABLE dbo.Columns (
    Id   INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(50) NOT NULL,
    Ord  INT NOT NULL
);

-- Tabela zadan
CREATE TABLE dbo.Tasks (
    Id    INT IDENTITY(1,1) PRIMARY KEY,
    Title NVARCHAR(200) NOT NULL,
    ColId INT NOT NULL 
        CONSTRAINT FK_Tasks_Columns FOREIGN KEY REFERENCES dbo.Columns(Id),
    Ord   INT NOT NULL
);

-- Indeks dla wydajnosci
CREATE INDEX IX_Tasks_Column ON dbo.Tasks(ColId) INCLUDE(Ord);
```

### Przykladowe dane

```sql
-- Predefiniowane kolumny (stale - nie dodajemy nowych przez API)
INSERT INTO dbo.Columns (Name, Ord) VALUES 
    (N'Todo', 1),
    (N'Doing', 2),
    (N'Done', 3);

-- Przykladowe zadania
INSERT INTO dbo.Tasks (Title, ColId, Ord) VALUES 
    (N'Zaprojektowac UI', 1, 1),
    (N'Napisac backend', 1, 2),
    (N'Stworzyc baze danych', 2, 1),
    (N'Dodac testy', 1, 3);
```

### Pole Ord (kolejnosc)

- `Columns.Ord` - kolejnosc wyswietlania kolumn (1, 2, 3)
- `Tasks.Ord` - kolejnosc zadan w ramach kolumny

Dzieki polu `Ord` zadania zachowuja swoja pozycje po przeladowaniu strony.

---

## API Endpoints

| Metoda | Endpoint | Opis | Body (JSON) | Kody odpowiedzi |
|--------|----------|------|-------------|-----------------|
| GET | `/api/board` | Pobierz cala tablice (kolumny + zadania) | - | 200 |
| POST | `/api/tasks` | Dodaj nowe zadanie | `{"title": "...", "col_id": 1}` | 201, 404 |
| POST | `/api/tasks/{id}/move` | Przenies zadanie do innej kolumny | `{"col_id": 2, "ord": 1}` | 200, 404 |

Kody odpowiedzi:
- 200 - Sukces
- 201 - Utworzono zadanie
- 404 - Nie znaleziono (kolumna/zadanie nie istnieje)

### Struktura odpowiedzi GET /api/board

```json
{
  "cols": [
    {"id": 1, "name": "Todo", "ord": 1},
    {"id": 2, "name": "Doing", "ord": 2},
    {"id": 3, "name": "Done", "ord": 3}
  ],
  "tasks": [
    {"id": 1, "title": "Zaprojektowac UI", "col_id": 1, "ord": 1},
    {"id": 2, "title": "Napisac backend", "col_id": 1, "ord": 2}
  ]
}
```

---

## Typowy przeplyw

Ponizej przedstawiono typowy scenariusz uzycia tablicy Kanban:

```
1. Pobranie calej tablicy
   GET /api/board
   --> Odpowiedz: 200 OK, kolumny + zadania

2. Dodanie nowego zadania do kolumny "Todo"
   POST /api/tasks
   {"title": "Nowe zadanie", "col_id": 1}
   --> Odpowiedz: 201 Created
   --> Zadanie pojawia sie na koncu kolumny (automatyczny ord)

3. Przeniesienie zadania do kolumny "Doing"
   POST /api/tasks/1/move
   {"col_id": 2, "ord": 1}
   --> Odpowiedz: 200 OK
   --> Zadanie jest teraz w kolumnie "Doing" na pozycji 1

4. Przeniesienie zadania do kolumny "Done"
   POST /api/tasks/1/move
   {"col_id": 3, "ord": 1}
   --> Odpowiedz: 200 OK
   --> Zadanie jest ukonczone
```

Pelne testy API z przykladowymi zapytaniami znajduja sie w pliku `tests.rest` (wymaga rozszerzenia REST Client w VS Code).

---

## Testy reczne

### Zapytania T-SQL do weryfikacji danych

```sql
-- Wyswietl wszystkie kolumny
SELECT * FROM dbo.Columns ORDER BY Ord;

-- Wyswietl wszystkie zadania
SELECT * FROM dbo.Tasks ORDER BY ColId, Ord;

-- Wyswietl zadania z nazwami kolumn
SELECT 
    t.Id,
    t.Title,
    c.Name AS ColumnName,
    t.Ord AS PositionInColumn
FROM dbo.Tasks t
JOIN dbo.Columns c ON t.ColId = c.Id
ORDER BY c.Ord, t.Ord;

-- Liczba zadan w kazdej kolumnie
SELECT 
    c.Name AS Kolumna,
    COUNT(t.Id) AS LiczbaZadan
FROM dbo.Columns c
LEFT JOIN dbo.Tasks t ON c.Id = t.ColId
GROUP BY c.Id, c.Name, c.Ord
ORDER BY c.Ord;

-- Zadania w kolumnie "Todo"
SELECT t.Id, t.Title, t.Ord
FROM dbo.Tasks t
JOIN dbo.Columns c ON t.ColId = c.Id
WHERE c.Name = 'Todo'
ORDER BY t.Ord;

-- Sprawdz czy kolejnosc (Ord) jest poprawna (bez luk)
SELECT 
    c.Name AS Kolumna,
    t.Ord,
    t.Title
FROM dbo.Tasks t
JOIN dbo.Columns c ON t.ColId = c.Id
ORDER BY c.Ord, t.Ord;
```

### Testowanie API

Gotowe testy API znajduja sie w pliku `tests.rest`. Aby z nich skorzystac:

1. Zainstaluj rozszerzenie REST Client w VS Code
2. Otworz plik `tests.rest`
3. Klikaj "Send Request" przy poszczegolnych zapytaniach

Plik zawiera testy dla wszystkich endpointow, w tym scenariusze bledow (nieistniejaca kolumna, nieistniejace zadanie).

---

## Struktura projektu

```
lab05/
├── main.py              # Glowna aplikacja FastAPI
├── reset_db.py          # Skrypt wykonujacy Kanban_Schema.sql
├── Kanban_Schema.sql    # Schemat bazy danych i dane poczatkowe
├── requirements.txt     # Zaleznosci Python
├── tests.rest           # Testy API dla REST Client
├── .env                 # Konfiguracja (nie w repozytorium)
└── static/
    ├── index.html       # Strona tablicy Kanban
    ├── kanban.js        # Logika aplikacji (drag & drop, przenoszenie)
    └── style.css        # Style CSS
```

---

## Technologie

- Backend: Python 3.12, FastAPI, Uvicorn
- Baza danych: MS SQL Server, pyodbc
- Frontend: HTML5, CSS3, JavaScript
- Walidacja: Pydantic
- Srodowisko: python-dotenv
