# Plaid Transaction Sync Engine

> A local-first, encrypted financial data ingestion pipeline that syncs bank transactions via Plaid API into SQLite with idempotency guarantees and audit-safe soft deletes.

---

## Problem Statement

Commercial personal finance tools (Mint, Monarch, YNAB) require cloud data access, charge subscription fees, and provide limited programmatic control. I needed a system that was:

- **Private** — bank credentials and transaction history never leave my hardware
- **Free to operate** — no SaaS subscription after build
- **Programmatic** — queryable via SQL, extensible for custom dashboards and alerts
- **Reliable** — handles API failures, rate limits, and token expiry without manual intervention

**Solution:** Build a custom sync engine using Plaid's API, store data locally in SQLite with encryption at rest, and orchestrate via a cron-scheduled Python CLI.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                          Plaid Sync Pipeline                                        │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌────────────────────┐     ┌─────────────┐     ┌───────────────────┐
│  Plaid API   │────▶│  Sync Engine    │────▶│  SQLite DB  │────▶│  Telegram   │
│  (REST)      │     │  (Python)       │     │  (local)    │     │  Alerts     │
└─────────────┘     └────────────────────┘     └─────────────┘     └───────────────────┘
                           │
                           ▼
                    ┌────────────────────┐
                    │  Cron Scheduler   │
                    │  (Hermes Agent)   │
                    └────────────────────┘
```

---

## Active Automations

| Job | Schedule | Purpose |
|-----|----------|---------|
| Transaction Sync | Every 6 hours | Pull new/modified/removed transactions from Plaid |
| Database Backup | Daily | Encrypted SQLite dump to secondary storage |
| Balance Alert | On threshold | Notify when account balances cross configured limits |
| Re-auth Monitor | Weekly | Flag items needing Plaid re-authentication |

---

## Key Design Decisions

### 1. SQLite Over PostgreSQL

Chose SQLite for zero operational overhead — no server process, no network port, file-level backups. WAL mode enabled for concurrent read/write. File permissions locked to `0o600`.

### 2. Soft Deletes for Audit Trail

Transactions marked as removed by Plaid (refunds, corrections, chargebacks) are soft-deleted (`is_removed = 1`) rather than hard-deleted. This preserves audit history for reconciliation and fraud detection. A `idx_transactions_removed` index ensures query performance isn't degraded.

### 3. Cursor-Based Idempotency

Plaid's `transactions/sync` endpoint returns a cursor. Each sync stores the cursor in a dedicated `sync_cursors` table. Subsequent syncs resume from the last cursor, ensuring:
- No duplicate transactions on re-runs
- Minimal API calls (only delta fetched)
- Crash-safe recovery (cursor only updates after successful DB commit)

### 4. Atomic Transaction Wrapping

Each sync run is a single SQLite `BEGIN...COMMIT` block:
1. Upsert transactions (added + modified)
2. Apply soft-deletions
3. Upsert account metadata and balances
4. Update sync cursor

If any step fails, the entire sync rolls back. The cursor never moves without a committed database state.

### 5. Fernet Encryption at Rest

Plaid access tokens are encrypted with Fernet (AES-128 in CBC mode) using a key stored in `.env`. The encryption key is generated once and never derived at runtime — no PBKDF2, no salt management, no password complexity requirements. Tokens are decrypted only in memory during sync execution.

### 6. Exponential Backoff on API Failures

All Plaid API calls wrapped with `tenacity`:
- Retry on `ApiException`, `TimeoutError`, `ConnectionError`
- Exponential wait: 1s → 2s → 4s → 8s → 16s
- Max 3 attempts before marking item as `error` status

### 7. Item Status Lifecycle

Each linked bank item tracks status: `active` | `needs_reauth` | `error`. The sync engine skips non-active items automatically, and Telegram alerts notify when re-authentication is required.

---

## Outcomes

- **620+ transactions** synced in initial run, covering 3+ months of banking history
- **6 accounts** tracked across checking, savings, credit, and loan products
- **Idempotent verified:** Second sync run added 0 duplicates, updated 0 records — cursor advanced correctly
- **Zero operational cost** after build — Plaid production API included in free tier for personal use
- **Sub-15-second sync time** for full delta across all accounts
- **100% sync reliability** since deployment (monitored via Hermes Agent cron)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Database | SQLite 3 (WAL mode) |
| API Client | Plaid Python SDK |
| Encryption | cryptography (Fernet) |
| Retry Logic | tenacity |
| Scheduling | Hermes Agent cron |
| Alerts | Telegram Bot API |
| Config | pydantic-settings |

---

## Files

- [Sync Engine Core](../../code-samples/sync_engine.py) — Atomic sync with cursor management and soft-delete
- [Database Schema](../../code-samples/plaid_schema.sql) — SQLite schema with WAL mode, indexes, foreign keys
