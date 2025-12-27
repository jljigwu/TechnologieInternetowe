
SET NOCOUNT ON;
GO

IF OBJECT_ID('dbo.Comments', 'U') IS NOT NULL DROP TABLE dbo.Comments;
IF OBJECT_ID('dbo.Posts', 'U') IS NOT NULL DROP TABLE dbo.Posts;
GO

CREATE TABLE dbo.Posts (
  Id        INT IDENTITY(1,1) PRIMARY KEY,
  Title     NVARCHAR(200) NOT NULL,
  Body      NVARCHAR(MAX) NOT NULL,
  CreatedAt DATETIME2(0)  NOT NULL CONSTRAINT DF_Posts_CreatedAt DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE dbo.Comments (
  Id        INT IDENTITY(1,1) PRIMARY KEY,
  PostId    INT NOT NULL CONSTRAINT FK_Comments_Posts FOREIGN KEY REFERENCES dbo.Posts(Id) ON DELETE CASCADE,
  Author    NVARCHAR(100) NOT NULL,
  Body      NVARCHAR(1000) NOT NULL,
  CreatedAt DATETIME2(0)  NOT NULL CONSTRAINT DF_Comments_CreatedAt DEFAULT (SYSUTCDATETIME()),
  Approved  BIT NOT NULL CONSTRAINT DF_Comments_Approved DEFAULT (0)
);
GO

CREATE INDEX IX_Comments_Post ON dbo.Comments(PostId) INCLUDE(Approved, CreatedAt);
GO

-- Seed
INSERT INTO dbo.Posts(Title, Body) VALUES 
(N'Witaj w blogu!', N'To jest pierwszy post na naszym blogu. Możesz dodawać komentarze, które zostaną zatwierdzone przez moderatora.'),
(N'Jak działa moderacja?', N'Każdy komentarz jest domyślnie niezatwierdzony. Moderator musi go zaakceptować, aby był widoczny dla innych użytkowników.');
GO

-- Add sample comments
INSERT INTO dbo.Comments(PostId, Author, Body, Approved) VALUES 
(1, N'Jan Kowalski', N'Super blog!', 1),
(1, N'Anna Nowak', N'Czekam na więcej postów', 0),
(2, N'Piotr Wiśniewski', N'Świetnie wyjaśnione', 1);
GO

-- Public view query example
-- SELECT c.* FROM dbo.Comments AS c WHERE c.PostId=1 AND c.Approved=1 ORDER BY c.CreatedAt DESC;
