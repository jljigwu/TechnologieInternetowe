# 📝 Blog z Moderacją Komentarzy

System blogowy z dodawaniem komentarzy i ręczną moderacją z backendem w Pythonie (FastAPI) i bazą danych MS SQL Server.

## 🔒 Bezpieczeństwo - TYLKO DOSTĘP LOKALNY

**Aplikacja działa TYLKO na localhost (127.0.0.1)** - nikt z zewnątrz nie może się połączyć!

- ✅ Serwer nasłuchuje tylko na `127.0.0.1`
- ✅ CORS ograniczone do `localhost:3000` i `127.0.0.1:3000`
- ✅ Brak dostępu z innych komputerów w sieci
- ✅ Brak dostępu z Internetu

---

## 🚀 Jak uruchomić projekt?

### Krok 1: Wymagania wstępne
- **Python 3.8 lub nowszy** 
- **MS SQL Server**
- **ODBC Driver 17 for SQL Server** 

### Krok 2: Zainstaluj zależności
```bash
cd lab03
pip install -r requirements.txt
```

### Krok 3: Utwórz bazę danych
W SQL Server Management Studio:
```sql
CREATE DATABASE TI_Lab3;
```

Następnie uruchom skrypt inicjalizujący:
```bash
python reset_db.py
```

### Krok 4: Uruchom aplikację
```bash
python main.py
```

Aplikacja będzie dostępna **TYLKO lokalnie**: **http://localhost:3000**

---

## 🚀 Funkcjonalności

### Posty
- Przeglądanie listy postów
- Dodawanie nowych postów (tytuł + treść)
- Wyświetlanie szczegółów posta

### Komentarze
- Dodawanie komentarzy do postów
- Nowe komentarze domyślnie `approved=0` (niewidoczne)
- Widok publiczny pokazuje tylko zatwierdzone komentarze (`approved=1`)

### Moderacja
- Panel moderatora z listą oczekujących komentarzy
- Przycisk "Zatwierdź" dla każdego komentarza
- Po zatwierdzeniu komentarz natychmiast widoczny publicznie

---

## 📋 API Endpoints

### Posts
- `GET /api/posts` - Lista wszystkich postów
- `POST /api/posts` - Dodaj nowy post
  ```json
  {
    "title": "Tytuł posta",
    "body": "Treść posta"
  }
  ```

### Comments
- `GET /api/posts/{id}/comments` - Pobierz zatwierdzone komentarze do posta
- `POST /api/posts/{id}/comments` - Dodaj komentarz (domyślnie `approved=0`)
  ```json
  {
    "author": "Jan Kowalski",
    "body": "Treść komentarza"
  }
  ```

### Moderation
- `GET /api/comments/pending` - Lista komentarzy oczekujących na moderację
- `POST /api/comments/{id}/approve` - Zatwierdź komentarz (`approved=1`)

---

## 🗄️ Model danych

### Posts
```sql
CREATE TABLE dbo.Posts (
  Id        INT IDENTITY(1,1) PRIMARY KEY,
  Title     NVARCHAR(200) NOT NULL,
  Body      NVARCHAR(MAX) NOT NULL,
  CreatedAt DATETIME2(0)  NOT NULL DEFAULT (SYSUTCDATETIME())
);
```

### Comments
```sql
CREATE TABLE dbo.Comments (
  Id        INT IDENTITY(1,1) PRIMARY KEY,
  PostId    INT NOT NULL FOREIGN KEY REFERENCES dbo.Posts(Id),
  Author    NVARCHAR(100) NOT NULL,
  Body      NVARCHAR(1000) NOT NULL,
  CreatedAt DATETIME2(0)  NOT NULL DEFAULT (SYSUTCDATETIME()),
  Approved  BIT NOT NULL DEFAULT (0)
);
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
- ✅ Walidacja danych (Pydantic)
- ✅ Parametryzowane zapytania SQL
- ✅ Escape HTML w JavaScript

---

## 📝 Statusy HTTP

- **200 OK** - Sukces
- **201 Created** - Zasób utworzony (+ header Location)
- **400 Bad Request** - Nieprawidłowe dane
- **404 Not Found** - Post/komentarz nie znaleziony
- **422 Unprocessable Entity** - Walidacja nie powiodła się
- **500 Internal Server Error** - Błąd serwera

---

## 🧪 Testowanie

### REST Client (VS Code)
Użyj pliku `tests.rest`:
```http
### Lista postów
GET http://localhost:3000/api/posts

### Dodaj komentarz
POST http://localhost:3000/api/posts/1/comments
Content-Type: application/json

{
  "author": "Jan Kowalski",
  "body": "Świetny post!"
}

### Zatwierdź komentarz
POST http://localhost:3000/api/comments/1/approve
```

### Swagger UI
Interaktywna dokumentacja API: **http://localhost:3000/docs**

---

## 📦 Struktura projektu

```
lab03/
├── main.py                     # Backend FastAPI
├── reset_db.py                 # Inicjalizacja bazy
├── requirements.txt            # Zależności Python
├── Lab03_Blog_Schema.sql       # Schema + seed
├── tests.rest                  # Testy API
├── .env                        # Konfiguracja
├── README.md                   # Dokumentacja
└── static/
    ├── index.html              # Lista postów
    ├── post.html               # Szczegóły posta + komentarze
    ├── moderate.html           # Panel moderatora
    ├── blog.js                 # Logika listy postów
    ├── post.js                 # Logika posta i komentarzy
    ├── moderate.js             # Logika moderacji
    └── style.css               # Style CSS
```

---

## 💡 Technologie

- **Backend**: FastAPI, Python 3.8+
- **Baza danych**: MS SQL Server
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Driver**: pyodbc
- **Walidacja**: Pydantic
- **Server**: Uvicorn (localhost only)

---

## 📖 Instrukcja użytkowania

### Dla użytkowników:
1. Otwórz http://localhost:3000
2. Przeglądaj posty
3. Kliknij "Zobacz komentarze" aby zobaczyć post
4. Dodaj komentarz - będzie oczekiwał na moderację

### Dla moderatorów:
1. Przejdź do http://localhost:3000/moderate
2. Zobacz listę oczekujących komentarzy
3. Kliknij "Zatwierdź" aby opublikować komentarz
4. Komentarz natychmiast pojawi się w widoku publicznym

---

## ⚠️ Ważne uwagi

1. **Aplikacja działa TYLKO lokalnie**
2. Komentarze są domyślnie niewidoczne (`approved=0`)
3. Wymaga ręcznego zatwierdzenia przez moderatora
4. Brak autentykacji - każdy może moderować (tylko lokalnie)

---

## 👨‍💻 Autor

Projekt wykonany na potrzeby kursu Technologie Internetowe (Lab 03).
