/* Lab04_Movies_Schema.sql
   Ranking filmów z głosowaniem
*/
SET NOCOUNT ON;
GO



IF OBJECT_ID('dbo.vMoviesRanking', 'V') IS NOT NULL DROP VIEW dbo.vMoviesRanking;
GO

IF OBJECT_ID('dbo.Ratings', 'U') IS NOT NULL DROP TABLE dbo.Ratings;
IF OBJECT_ID('dbo.Movies', 'U') IS NOT NULL DROP TABLE dbo.Movies;
GO

CREATE TABLE dbo.Movies (
  Id    INT IDENTITY(1,1) PRIMARY KEY,
  Title NVARCHAR(200) NOT NULL,
  [Year] INT NOT NULL
);
GO

CREATE TABLE dbo.Ratings (
  Id      INT IDENTITY(1,1) PRIMARY KEY,
  MovieId INT NOT NULL CONSTRAINT FK_Ratings_Movies FOREIGN KEY REFERENCES dbo.Movies(Id) ON DELETE CASCADE,
  Score   INT NOT NULL CONSTRAINT CK_Ratings_Score CHECK (Score BETWEEN 1 AND 5)
);
GO

CREATE INDEX IX_Ratings_Movie ON dbo.Ratings(MovieId) INCLUDE(Score);
GO

-- Ranking view
CREATE VIEW dbo.vMoviesRanking AS
SELECT m.Id, m.Title, m.[Year],
       CAST(AVG(CAST(r.Score AS DECIMAL(5,2))) AS DECIMAL(5,2)) AS AvgScore,
       COUNT(r.Id) AS Votes
FROM dbo.Movies m
LEFT JOIN dbo.Ratings r ON r.MovieId = m.Id
GROUP BY m.Id, m.Title, m.[Year];
GO

-- Seed
INSERT INTO dbo.Movies(Title,[Year]) VALUES 
(N'The Matrix', 1999),
(N'Inception', 2010),
(N'Interstellar', 2014),
(N'Blade Runner 2049', 2017),
(N'Arrival', 2016),
(N'Tenet', 2020);
GO

INSERT INTO dbo.Ratings(MovieId,Score) VALUES 
(1, 5), (1, 4), (1, 5),
(2, 5), (2, 4),
(3, 5), (3, 5), (3, 4),
(4, 4),
(5, 4), (5, 5);
GO
