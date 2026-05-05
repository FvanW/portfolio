-- SQLite schema for Plaid transaction sync engine
-- WAL mode, foreign keys, soft-delete audit trail

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;

-- Encrypted access tokens per linked institution
CREATE TABLE IF NOT EXISTS access_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT UNIQUE NOT NULL,
    institution_name TEXT,
    institution_id TEXT,
    encrypted_token BLOB NOT NULL,
    status TEXT DEFAULT 'active'
        CHECK (status IN ('active', 'needs_reauth', 'error')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sync cursors for idempotency (one per item)
CREATE TABLE IF NOT EXISTS sync_cursors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT UNIQUE NOT NULL,
    cursor TEXT,
    last_synced_at TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES access_tokens(item_id)
        ON DELETE CASCADE
);

-- Transactions with soft-delete audit trail
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT UNIQUE NOT NULL,
    item_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    amount REAL NOT NULL,
    currency_code TEXT DEFAULT 'USD',
    date TEXT NOT NULL,
    name TEXT,
    merchant_name TEXT,
    category TEXT,           -- JSON array stored as text
    payment_channel TEXT,
    pending BOOLEAN DEFAULT 0,
    location_city TEXT,
    location_region TEXT,
    raw_json TEXT,           -- Full Plaid payload for debugging
    is_removed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES access_tokens(item_id)
        ON DELETE CASCADE
);

-- Account metadata and balances
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT UNIQUE NOT NULL,
    item_id TEXT NOT NULL,
    name TEXT,
    official_name TEXT,
    type TEXT,
    subtype TEXT,
    mask TEXT,
    balances_available REAL,
    balances_current REAL,
    balances_limit REAL,
    balances_currency_code TEXT DEFAULT 'USD',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES access_tokens(item_id)
        ON DELETE CASCADE
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_transactions_date
    ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_item
    ON transactions(item_id);
CREATE INDEX IF NOT EXISTS idx_transactions_name
    ON transactions(name);
CREATE INDEX IF NOT EXISTS idx_transactions_removed
    ON transactions(is_removed);
