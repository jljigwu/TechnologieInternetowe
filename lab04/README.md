# Ranking filmow

System rankingowy filmow z glosowaniem uzytkownikow, backendem w Pythonie (FastAPI) i baza danych MS SQL Server.


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
DB_DATABASE=TI_Lab4
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
CREATE DATABASE TI_Lab4;
```

### Krok 4: Inicjalizacja schematu i danych

```bash
python reset_db.py
```

Ten skrypt wykona plik `Movies_Schema.sql` - utworzy tabele, widok i wstawi przykladowe filmy z ocenami.

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
-- Usuwanie istniejacych obiektow (jesli istnieja)
IF OBJECT_ID('dbo.vMoviesRanking', 'V') IS NOT NULL DROP VIEW dbo.vMoviesRanking;
IF OBJECT_ID('dbo.Ratings', 'U') IS NOT NULL DROP TABLE dbo.Ratings;
IF OBJECT_ID('dbo.Movies', 'U') IS NOT NULL DROP TABLE dbo.Movies;

-- Tabela filmow
CREATE TABLE dbo.Movies (
    Id    INT IDENTITY(1,1) PRIMARY KEY,
    Title NVARCHAR(200) NOT NULL,
    [Year] INT NOT NULL
);

-- Tabela ocen
CREATE TABLE dbo.Ratings (
    Id      INT IDENTITY(1,1) PRIMARY KEY,
    MovieId INT NOT NULL 
        CONSTRAINT FK_Ratings_Movies FOREIGN KEY REFERENCES dbo.Movies(Id) ON DELETE CASCADE,
    Score   INT NOT NULL 
        CONSTRAINT CK_Ratings_Score CHECK (Score BETWEEN 1 AND 5)
);

-- Indeks dla wydajnosci
CREATE INDEX IX_Ratings_Movie ON dbo.Ratings(MovieId) INCLUDE(Score);

-- Widok rankingowy (agreguje srednia ocene i liczbe glosow)
CREATE VIEW dbo.vMoviesRanking AS
SELECT 
    m.Id, 
    m.Title, 
    m.[Year],
    CAST(AVG(CAST(r.Score AS DECIMAL(5,2))) AS DECIMAL(5,2)) AS AvgScore,
    COUNT(r.Id) AS Votes
FROM dbo.Movies m
LEFT JOIN dbo.Ratings r ON r.MovieId = m.Id
GROUP BY m.Id, m.Title, m.[Year];
```

### Przykladowe dane

```sql
-- Filmy
INSERT INTO dbo.Movies (Title, [Year]) VALUES 
    (N'The Matrix', 1999),
    (N'Inception', 2010),
    (N'Interstellar', 2014),
    (N'Blade Runner 2049', 2017),
    (N'Arrival', 2016),
    (N'Tenet', 2020);

-- Oceny
INSERT INTO dbo.Ratings (MovieId, Score) VALUES 
    (1, 5), (1, 4), (1, 5),    -- The Matrix: 3 glosy
    (2, 5), (2, 4),             -- Inception: 2 glosy
    (3, 5), (3, 5), (3, 4),    -- Interstellar: 3 glosy
    (4, 4),                     -- Blade Runner 2049: 1 glos
    (5, 4), (5, 5);             -- Arrival: 2 glosy
    -- Tenet: brak glosow
```

### Widok vMoviesRanking

Widok `vMoviesRanking` automatycznie oblicza:
- `AvgScore` - srednia ocena filmu (1.00 - 5.00)
- `Votes` - liczba oddanych glosow

Dzieki widokowi nie trzeba recznie obliczac srednich - wystarczy SELECT z widoku.

---

## API Endpoints

| Metoda | Endpoint | Opis | Body (JSON) | Kody odpowiedzi |
|--------|----------|------|-------------|-----------------|
| GET | `/api/movies` | Lista filmow z rankingiem | - | 200 |
| POST | `/api/movies` | Dodaj nowy film | `{"title": "...", "year": 2021}` | 201 |
| POST | `/api/ratings` | Dodaj ocene do filmu | `{"movie_id": 1, "score": 5}` | 201, 404 |

Kody odpowiedzi:
- 200 - Sukces
- 201 - Utworzono zasob (film, ocena)
- 404 - Nie znaleziono (film nie istnieje)
- 422 - Bledna walidacja (rok poza zakresem 1888-2100, ocena poza 1-5)

---

## Typowy przeplyw

Ponizej przedstawiono typowy scenariusz uzycia systemu:

```
1. Przegladanie rankingu filmow
   GET /api/movies
   --> Odpowiedz: 200 OK, lista filmow posortowana wg avg_score DESC

2. Dodanie nowego filmu
   POST /api/movies
   {"title": "Dune", "year": 2021}
   --> Odpowiedz: 201 Created, zwraca id filmu
   --> Film pojawia sie w rankingu z avg_score=0 i votes=0

3. Ocena filmu (pierwsza ocena)
   POST /api/ratings
   {"movie_id": 7, "score": 5}
   --> Odpowiedz: 201 Created
   --> Film ma teraz avg_score=5.00 i votes=1

4. Kolejna ocena tego samego filmu
   POST /api/ratings
   {"movie_id": 7, "score": 4}
   --> Odpowiedz: 201 Created
   --> Film ma teraz avg_score=4.50 i votes=2

5. Sprawdzenie zaktualizowanego rankingu
   GET /api/movies
   --> Odpowiedz: 200 OK, lista z nowymi srednimi
```

Pelne testy API z przykladowymi zapytaniami znajduja sie w pliku `tests.rest` (wymaga rozszerzenia REST Client w VS Code).

---

## Testy reczne

### Zapytania T-SQL do weryfikacji danych

```sql
-- Wyswietl wszystkie filmy
SELECT * FROM dbo.Movies;

-- Wyswietl wszystkie oceny
SELECT * FROM dbo.Ratings;

-- Wyswietl ranking filmow (uzywa widoku)
SELECT * FROM dbo.vMoviesRanking ORDER BY AvgScore DESC, Votes DESC;

-- Wyswietl filmy z ocenami (szczegolowo)
SELECT 
    m.Title,
    m.[Year],
    r.Score,
    r.Id AS RatingId
FROM dbo.Movies m
LEFT JOIN dbo.Ratings r ON m.Id = r.MovieId
ORDER BY m.Title, r.Id;

-- Statystyki ocen dla kazdego filmu
SELECT 
    m.Title,
    COUNT(r.Id) AS LiczbaOcen,
    MIN(r.Score) AS MinOcena,
    MAX(r.Score) AS MaxOcena,
    AVG(CAST(r.Score AS DECIMAL(5,2))) AS SredniaOcena
FROM dbo.Movies m
LEFT JOIN dbo.Ratings r ON m.Id = r.MovieId
GROUP BY m.Id, m.Title
ORDER BY SredniaOcena DESC;

-- Filmy bez ocen
SELECT m.Title, m.[Year]
FROM dbo.Movies m
LEFT JOIN dbo.Ratings r ON m.Id = r.MovieId
WHERE r.Id IS NULL;

-- Rozklad ocen (ile razy kazda ocena zostala uzyta)
SELECT 
    Score,
    COUNT(*) AS Liczba
FROM dbo.Ratings
GROUP BY Score
ORDER BY Score;
```

### Testowanie API

Gotowe testy API znajduja sie w pliku `tests.rest`. Aby z nich skorzystac:

1. Zainstaluj rozszerzenie REST Client w VS Code
2. Otworz plik `tests.rest`
3. Klikaj "Send Request" przy poszczegolnych zapytaniach

Plik zawiera testy dla wszystkich endpointow, w tym scenariusze bledow (nieistniejacy film, nieprawidlowa ocena).

---

## Struktura projektu

```
lab04/
├── main.py              # Glowna aplikacja FastAPI
├── reset_db.py          # Skrypt wykonujacy Movies_Schema.sql
├── Movies_Schema.sql    # Schemat bazy danych, widok i dane poczatkowe
├── requirements.txt     # Zaleznosci Python
├── tests.rest           # Testy API dla REST Client
├── .env                 # Konfiguracja (nie w repozytorium)
└── static/
    ├── index.html       # Strona rankingu filmow
    ├── movies.js        # Logika aplikacji (ocenianie, wyswietlanie)
    └── style.css        # Style CSS
```

---

## Technologie

- Backend: Python 3.12, FastAPI, Uvicorn
- Baza danych: MS SQL Server, pyodbc
- Frontend: HTML5, CSS3, JavaScript
- Walidacja: Pydantic
- Srodowisko: python-dotenv

