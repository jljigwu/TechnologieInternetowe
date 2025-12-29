/* Lab05_Kanban_Schema.sql
   Tablica Kanban z kolumnami i zadaniami
*/
SET NOCOUNT ON;
GO



IF OBJECT_ID('dbo.Tasks', 'U') IS NOT NULL DROP TABLE dbo.Tasks;
IF OBJECT_ID('dbo.Columns', 'U') IS NOT NULL DROP TABLE dbo.Columns;
GO

CREATE TABLE dbo.Columns (
  Id   INT IDENTITY(1,1) PRIMARY KEY,
  Name NVARCHAR(50) NOT NULL,
  Ord  INT NOT NULL
);
GO

CREATE TABLE dbo.Tasks (
  Id    INT IDENTITY(1,1) PRIMARY KEY,
  Title NVARCHAR(200) NOT NULL,
  ColId INT NOT NULL CONSTRAINT FK_Tasks_Columns FOREIGN KEY REFERENCES dbo.Columns(Id),
  Ord   INT NOT NULL
);
GO

CREATE INDEX IX_Tasks_Column ON dbo.Tasks(ColId) INCLUDE(Ord);
GO

-- Seed: Predefiniowane kolumny
INSERT INTO dbo.Columns(Name, Ord) VALUES 
(N'Todo', 1),
(N'Doing', 2),
(N'Done', 3);
GO

-- Seed: Przykładowe zadania
INSERT INTO dbo.Tasks(Title, ColId, Ord) VALUES 
(N'Zaprojektować UI', 1, 1),
(N'Napisać backend', 1, 2),
(N'Stworzyć bazę danych', 2, 1),
(N'Dodać testy', 1, 3);
GO
