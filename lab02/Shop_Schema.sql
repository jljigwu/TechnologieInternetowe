/* Lab02_Shop_Schema.sql
   Sklep – schema + seed + testy checkout
*/
SET NOCOUNT ON;
GO

IF OBJECT_ID('dbo.OrderItems', 'U') IS NOT NULL DROP TABLE dbo.OrderItems;
IF OBJECT_ID('dbo.Orders', 'U') IS NOT NULL DROP TABLE dbo.Orders;
IF OBJECT_ID('dbo.Products', 'U') IS NOT NULL DROP TABLE dbo.Products;
GO

CREATE TABLE dbo.Products (
  Id    INT IDENTITY(1,1) PRIMARY KEY,
  Name  NVARCHAR(120) NOT NULL,
  Price DECIMAL(12,2) NOT NULL CONSTRAINT CK_Products_Price CHECK (Price >= 0)
);
GO

CREATE TABLE dbo.Orders (
  Id        INT IDENTITY(1,1) PRIMARY KEY,
  CreatedAt DATETIME2(0) NOT NULL CONSTRAINT DF_Orders_CreatedAt DEFAULT (SYSUTCDATETIME())
);
GO

CREATE TABLE dbo.OrderItems (
  Id        INT IDENTITY(1,1) PRIMARY KEY,
  OrderId   INT NOT NULL CONSTRAINT FK_OrderItems_Orders   FOREIGN KEY REFERENCES dbo.Orders(Id)   ON DELETE CASCADE,
  ProductId INT NOT NULL CONSTRAINT FK_OrderItems_Products FOREIGN KEY REFERENCES dbo.Products(Id),
  Qty       INT NOT NULL CONSTRAINT CK_OrderItems_Qty CHECK (Qty > 0),
  Price     DECIMAL(12,2) NOT NULL
);
GO

CREATE INDEX IX_OrderItems_Order ON dbo.OrderItems(OrderId) INCLUDE(Qty, Price);
GO

-- Seed
INSERT INTO dbo.Products(Name, Price) VALUES
(N'Kawa ziarnista 1kg', 79.90),
(N'Kubek porcelanowy', 24.50),
(N'Notes A5 kropki', 12.00),
(N'Długopis żelowy', 5.99),
(N'Herbata Earl Grey 100g', 18.50),
(N'Termos stalowy 0.5L', 45.00);
GO

-- Checkout demo
DECLARE @Cart TABLE(ProductId INT, Qty INT);
INSERT INTO @Cart VALUES (1,2),(3,1);

BEGIN TRAN;

INSERT INTO dbo.Orders DEFAULT VALUES;
DECLARE @Id INT = SCOPE_IDENTITY();

INSERT INTO dbo.OrderItems(OrderId, ProductId, Qty, Price)
SELECT @Id, p.Id, c.Qty, p.Price
FROM @Cart AS c
JOIN dbo.Products AS p ON p.Id = c.ProductId;

-- Total
SELECT OrderId = @Id, Total = SUM(Qty*Price) FROM dbo.OrderItems WHERE OrderId = @Id;

COMMIT;
