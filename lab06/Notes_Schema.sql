/* Lab06_Notes_Schema.sql
   Notatnik z tagowaniem i wyszukiwaniem
*/
SET NOCOUNT ON;
GO

IF OBJECT_ID('dbo.NoteTags', 'U') IS NOT NULL DROP TABLE dbo.NoteTags;
IF OBJECT_ID('dbo.Notes', 'U') IS NOT NULL DROP TABLE dbo.Notes;
IF OBJECT_ID('dbo.Tags', 'U') IS NOT NULL DROP TABLE dbo.Tags;
GO

CREATE TABLE dbo.Notes (
  Id        INT IDENTITY(1,1) PRIMARY KEY,
  Title     NVARCHAR(200) NOT NULL,
  Body      NVARCHAR(MAX) NOT NULL,
  CreatedAt DATETIME2 NOT NULL DEFAULT GETDATE()
);
GO

CREATE TABLE dbo.Tags (
  Id   INT IDENTITY(1,1) PRIMARY KEY,
  Name NVARCHAR(50) NOT NULL UNIQUE
);
GO

CREATE TABLE dbo.NoteTags (
  NoteId INT NOT NULL CONSTRAINT FK_NoteTags_Notes FOREIGN KEY REFERENCES dbo.Notes(Id) ON DELETE CASCADE,
  TagId  INT NOT NULL CONSTRAINT FK_NoteTags_Tags FOREIGN KEY REFERENCES dbo.Tags(Id),
  CONSTRAINT PK_NoteTags PRIMARY KEY (NoteId, TagId)
);
GO

CREATE INDEX IX_Notes_Title ON dbo.Notes(Title);
CREATE INDEX IX_Notes_CreatedAt ON dbo.Notes(CreatedAt DESC);
CREATE INDEX IX_Tags_Name ON dbo.Tags(Name);
GO

-- Seed: Przykładowe tagi
INSERT INTO dbo.Tags(Name) VALUES 
(N'work'),
(N'home'),
(N'ideas'),
(N'shopping'),
(N'urgent');
GO

-- Seed: Przykładowe notatki
INSERT INTO dbo.Notes(Title, Body, CreatedAt) VALUES 
(N'Spotkanie z zespołem', N'Omówić postępy w projekcie i zaplanować następne kroki. Przygotować prezentację dla klienta.', DATEADD(day, -2, GETDATE())),
(N'Lista zakupów', N'Kupić mleko, chleb, masło, jajka, ser żółty, pomidory i sałatę.', DATEADD(day, -1, GETDATE())),
(N'Pomysł na aplikację', N'Stworzyć aplikację do śledzenia nawyków. Użyć React i Firebase. Dodać powiadomienia push.', DATEADD(hour, -5, GETDATE())),
(N'Naprawa rowerem', N'Oddać rower do serwisu - trzeba naprawić hamulce i wymienić oponę tylną.', GETDATE());
GO

-- Seed: Przypisania tagów
INSERT INTO dbo.NoteTags(NoteId, TagId) VALUES
(1, 1), -- Spotkanie = work
(1, 5), -- Spotkanie = urgent
(2, 2), -- Lista zakupów = home
(2, 4), -- Lista zakupów = shopping
(3, 1), -- Pomysł = work
(3, 3), -- Pomysł = ideas
(4, 2); -- Naprawa = home
GO
