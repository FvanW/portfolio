"""Core Plaid-to-SQLite synchronization engine.

Demonstrates: atomic transactions, cursor-based idempotency,
exponential backoff, soft-delete audit trail, and structured
sync result reporting.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from typing import Any

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class SyncEngine:
    """Synchronize Plaid transactions into SQLite with idempotency guarantees."""

    def __init__(self, settings: Any, db: sqlite3.Connection, client: Any):
        self.settings = settings
        self.db = db
        self.client = client
        self.encryption_key = settings.plaid_encryption_key.get_secret_value()

    def run_sync(self, item_id: str | None = None) -> SyncResult:
        """Run sync for all active items or one specified item."""
        rows = self._load_active_tokens(item_id=item_id)
        result = SyncResult()

        if not rows:
            logger.info("No active Plaid items to sync")
            return result

        for row in rows:
            result.items.append(self._sync_one_item(row))

        return result

    def _sync_one_item(self, token_row: sqlite3.Row) -> SyncItemResult:
        """Sync one Plaid item: fetch deltas, upsert, soft-delete, advance cursor."""
        item_id = str(token_row["item_id"])
        logger.info("Starting sync item_id=%s", item_id)

        try:
            access_token = decrypt_token(
                bytes(token_row["encrypted_token"]), self.encryption_key
            )
            cursor = self._get_cursor(item_id)
            plaid_data = self._fetch_all_pages(access_token, cursor)

            # Atomic commit: DB state + cursor move together
            with self.db:
                self._upsert_transactions([*plaid_data["added"], *plaid_data["modified"]], item_id)
                self._soft_remove_transactions(plaid_data["removed"])
                self._upsert_accounts(plaid_data["accounts"], item_id)
                if plaid_data["next_cursor"] is not None:
                    self._update_cursor(item_id, str(plaid_data["next_cursor"]))

            return SyncItemResult(
                item_id=item_id,
                added=len(plaid_data["added"]),
                modified=len(plaid_data["modified"]),
                removed=len(plaid_data["removed"]),
                accounts_updated=len(plaid_data["accounts"]),
            )
        except Exception as exc:
            self._mark_item_status(item_id, "error")
            logger.exception("Sync failed item_id=%s", item_id)
            return SyncItemResult(item_id=item_id, success=False, error=str(exc))

    @retry(
        retry=retry_if_exception_type((ApiException, TimeoutError, ConnectionError)),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _fetch_all_pages(self, access_token: str, cursor: str | None) -> dict[str, Any]:
        """Fetch all paginated transaction deltas from Plaid."""
        all_added: list[dict] = []
        all_modified: list[dict] = []
        all_removed: list[dict] = []
        latest_cursor = cursor
        has_more = True

        while has_more:
            page = self._sync_page(access_token, latest_cursor)
            all_added.extend(page.get("added", []))
            all_modified.extend(page.get("modified", []))
            all_removed.extend(page.get("removed", []))
            latest_cursor = page.get("next_cursor")
            has_more = bool(page.get("has_more", False))

        accounts = self._get_accounts(access_token)
        return {
            "added": all_added,
            "modified": all_modified,
            "removed": all_removed,
            "accounts": accounts,
            "next_cursor": latest_cursor,
        }

    def _upsert_transactions(self, transactions: list[dict], item_id: str) -> None:
        """INSERT OR REPLACE transactions. Restores soft-deleted rows on re-add."""
        for tx in transactions:
            location = tx.get("location") or {}
            category = tx.get("category")
            self.db.execute(
                """
                INSERT INTO transactions (
                    transaction_id, item_id, account_id, amount, currency_code, date,
                    name, merchant_name, category, payment_channel, pending,
                    location_city, location_region, raw_json, is_removed, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
                ON CONFLICT(transaction_id) DO UPDATE SET
                    amount = excluded.amount,
                    date = excluded.date,
                    name = excluded.name,
                    merchant_name = excluded.merchant_name,
                    category = excluded.category,
                    pending = excluded.pending,
                    raw_json = excluded.raw_json,
                    is_removed = 0,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    tx.get("transaction_id"),
                    item_id,
                    tx.get("account_id"),
                    float(tx.get("amount", 0.0)),
                    tx.get("iso_currency_code") or "USD",
                    str(tx.get("date")),
                    tx.get("name"),
                    tx.get("merchant_name"),
                    json.dumps(category) if category else None,
                    tx.get("payment_channel"),
                    1 if tx.get("pending") else 0,
                    location.get("city"),
                    location.get("region"),
                    json.dumps(tx, default=str),
                ),
            )

    def _soft_remove_transactions(self, removed: list[dict]) -> None:
        """Mark removed Plaid transactions as soft-deleted instead of deleting."""
        for tx in removed:
            tid = tx.get("transaction_id")
            if tid:
                self.db.execute(
                    """
                    UPDATE transactions
                    SET is_removed = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE transaction_id = ?
                    """,
                    (tid,),
                )

    def _upsert_accounts(self, accounts: list[dict], item_id: str) -> None:
        """Upsert account metadata and balances."""
        for account in accounts:
            balances = account.get("balances") or {}
            self.db.execute(
                """
                INSERT INTO accounts (...)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(account_id) DO UPDATE SET
                    balances_available = excluded.balances_available,
                    balances_current = excluded.balances_current,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (account.get("account_id"), item_id, ...),
            )

    def _update_cursor(self, item_id: str, cursor: str) -> None:
        """Advance sync cursor only after successful DB commit."""
        self.db.execute(
            """
            INSERT INTO sync_cursors (item_id, cursor, last_synced_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(item_id) DO UPDATE SET
                cursor = excluded.cursor,
                last_synced_at = CURRENT_TIMESTAMP
            """,
            (item_id, cursor),
        )
