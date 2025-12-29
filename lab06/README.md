# Notatnik z tagami

Aplikacja do zarządzania notatkami z wyszukiwaniem i tagowaniem.

## Jak uruchomić?

Potrzebne:
- Python 3.8+
- MS SQL Server
- ODBC Driver 17

```bash
cd lab06
pip install -r requirements.txt
```

Stwórz bazę w SSMS:
```sql
CREATE DATABASE TI_Lab6;
```

Uruchom:
```bash
python reset_db.py
python main.py
```

Otwórz: http://localhost:3000

## Co robi?

- Dodawanie notatek (tytuł + treść)
- Wyszukiwanie po tytule i treści
- Tagowanie notatek
- Automatyczne tworzenie nowych tagów
- Tag może być przypisany tylko raz do notatki

## API

**GET /api/notes?q=...**  
Zwraca notatki, opcjonalnie filtruje po zapytaniu.
```json
{
  "notes": [
    {
      "id": 1,
      "title": "Spotkanie",
      "body": "Omówić projekt...",
      "created_at": "2025-12-29T10:00:00",
      "tags": ["work", "urgent"]
    }
  ]
}
```

**POST /api/notes**  
Dodaje nową notatkę.
```json
{
  "title": "Tytuł notatki",
  "body": "Treść notatki"
}
```

**GET /api/tags**  
Zwraca wszystkie tagi.
```json
{
  "tags": [
    {"id": 1, "name": "work"},
    {"id": 2, "name": "home"}
  ]
}
```

**POST /api/notes/{id}/tags**  
Przypisuje tagi do notatki.
```json
{
  "tags": ["work", "urgent", "home"]
}
```

## Baza danych

```sql
-- Notatki
CREATE TABLE Notes (
  Id INT PRIMARY KEY,
  Title NVARCHAR(200),
  Body NVARCHAR(MAX),
  CreatedAt DATETIME2
);

-- Tagi
CREATE TABLE Tags (
  Id INT PRIMARY KEY,
  Name NVARCHAR(50) UNIQUE
);

-- Relacja wiele do wielu
CREATE TABLE NoteTags (
  NoteId INT REFERENCES Notes(Id),
  TagId INT REFERENCES Tags(Id),
  PRIMARY KEY (NoteId, TagId)
);
```

Wyszukiwanie używa LIKE na tytule i treści.  
Tag może być przypisany tylko raz do notatki (PK na relacji).

## Jak używać?

1. Wpisz w pole wyszukiwania żeby filtrować
2. Kliknij "Dodaj notatkę" żeby stworzyć nową
3. Użyj przycisku "+ Tag" żeby dodać tagi
4. Tagi oddzielaj przecinkami: work, home, urgent

---

Made for Technologie Internetowe Lab06
