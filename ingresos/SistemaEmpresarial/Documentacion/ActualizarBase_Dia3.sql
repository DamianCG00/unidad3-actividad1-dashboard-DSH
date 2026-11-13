-- Unidad II · Actividad 7 — Balances por cuenta y balance general
-- Ejecutar UNA vez sobre una base que YA EXISTÍA. EnsureCreated no modifica tablas existentes.
-- Antes de ejecutar, confirmar que ningún importe alcanza el nuevo límite:
--   SELECT MAX("Amount") FROM "Transactions";   -- debe ser < 10000000000.00

BEGIN;

ALTER TABLE "Transactions"
    ALTER COLUMN "Amount" TYPE numeric(12,2);

CREATE INDEX IF NOT EXISTS "IX_Transactions_AccountId_TransactionDate"
    ON "Transactions" ("AccountId", "TransactionDate");

COMMIT;
