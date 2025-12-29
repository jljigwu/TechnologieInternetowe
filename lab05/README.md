# Kanban Board

Prosta tablica Kanban do zarządzania zadaniami.

## Jak uruchomić?

Potrzebne:
- Python 3.8+
- MS SQL Server
- ODBC Driver 17

```bash
cd lab05
pip install -r requirements.txt
```

Stwórz bazę w SSMS:
```sql
CREATE DATABASE TI_Lab5;
```

Uruchom:
```bash
python reset_db.py
python main.py
```

Otwórz: http://localhost:3000

## Co robi?

- 3 kolumny: Todo, Doing, Done
- Dodawanie zadań do kolumn
- Przenoszenie zadań między kolumnami (strzałki ← →)
- Utrzymuje kolejność zadań (ord)

## API

**GET /api/board**  
Zwraca całą tablicę (kolumny + zadania).
```json
{
  "cols": [
    {"id": 1, "name": "Todo", "ord": 1}
  ],
  "tasks": [
    {"id": 1, "title": "Zadanie", "col_id": 1, "ord": 1}
  ]
}
```

**POST /api/tasks**  
Dodaje nowe zadanie.
```json
{
  "title": "Zaprojektować UI",
  "col_id": 1
}
```

**POST /api/tasks/{id}/move**  
Przenosi zadanie do innej kolumny.
```json
{
  "col_id": 2,
  "ord": 1
}
```

## Baza danych

```sql
-- Kolumny
CREATE TABLE Columns (
  Id INT PRIMARY KEY,
  Name NVARCHAR(50),
  Ord INT
);

-- Zadania
CREATE TABLE Tasks (
  Id INT PRIMARY KEY,
  Title NVARCHAR(200),
  ColId INT REFERENCES Columns(Id),
  Ord INT
);
```

Kolumny są predefiniowane (Todo, Doing, Done).  
Zadania mają pole `ord` do zachowania kolejności w kolumnie.

## Jak używać?

1. Kliknij "+ Dodaj" w kolumnie
2. Wpisz tytuł zadania
3. Użyj strzałek ← → żeby przenosić zadania
4. Zadania zachowują pozycję po odświeżeniu

---

Made for Technologie Internetowe Lab05
