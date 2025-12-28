# Ranking Filmów

System rankingowy filmów z głosowaniem użytkowników, backendem w Pythonie (FastAPI) i bazą danych MS SQL Server.
## Jak uruchomić?

Potrzebne:
- Python 3.8+
- MS SQL Server
- ODBC Driver 17

```bash
cd lab04
pip install -r requirements.txt
```

W SSMS stwórz bazę:
```sql
CREATE DATABASE TI_Lab4;
```

Uruchom:
```bash
python reset_db.py
python main.py
```

Otwórz: http://localhost:3000

## Co robi?

- Dodawanie filmów (tytuł + rok)
- Ocenianie filmów (1-5 gwiazdek)
- Ranking według średniej oceny
- Licznik głosów

## API

**GET /api/movies**  
Zwraca listę filmów z rankingiem.

**POST /api/movies**  
Dodaje nowy film.
```json
{
  "title": "Inception",
  "year": 2010
}
```

**POST /api/ratings**  
Dodaje ocenę.
```json
{
  "movie_id": 1,
  "score": 5
}
```

## Baza danych

Dwie tabele + widok:

```sql
-- Filmy
CREATE TABLE Movies (
  Id INT PRIMARY KEY,
  Title NVARCHAR(200),
  Year INT
);

-- Oceny
CREATE TABLE Ratings (
  Id INT PRIMARY KEY,
  MovieId INT REFERENCES Movies(Id),
  Score INT CHECK (Score BETWEEN 1 AND 5)
);

-- Widok z rankingiem
CREATE VIEW vMoviesRanking AS
SELECT m.Id, m.Title, m.Year,
       AVG(r.Score) AS AvgScore,
       COUNT(r.Id) AS Votes
FROM Movies m
LEFT JOIN Ratings r ON r.MovieId = m.Id
GROUP BY m.Id, m.Title, m.Year;
```

---

## 🔒 Bezpieczeństwo

### Zabezpieczenia sieciowe
- ✅ **Host: 127.0.0.1** - TYLKO localhost
- ✅ **CORS: localhost only**

### Zabezpieczenia aplikacji
- ✅ **X-Content-Type-Options: nosniff**
- ✅ **Content-Security-Policy**
- ✅ **Referrer-Policy**
- ✅ Walidacja danych (Pydantic): rok 1888-2100, ocena 1-5
- ✅ Parametryzowane zapytania SQL
- ✅ Escape HTML w JavaScript


---

## 📦 Struktura projektu

```
lab04/
├── main.py                     # Backend FastAPI
├── reset_db.py                 # Inicjalizacja bazy
├── requirements.txt            # Zależności Python
├── Movies_Schema.sql           # Schema + seed + widok
├── tests.rest                  # Testy API
├── .env                        # Konfiguracja
├── README.md                   # Dokumentacja
└── static/
    ├── index.html              # Interfejs rankingu
    ├── movies.js               # Logika aplikacji
    └── style.css               # Style CSS
```

---

