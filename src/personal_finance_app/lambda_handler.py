"""AWS Lambda entry point for exporting Plaid data into S3."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict

from .config import AppConfig
from .plaid_service import PlaidService, SUPPORTED_INSTITUTIONS
from .storage import S3Storage

_LOGGER = logging.getLogger(__name__)


def _today() -> date:
    return date.today()


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    """Entry point for the ``fetch_financial_data`` Lambda.

    The event payload is expected to contain a ``public_tokens`` mapping where the keys are
    institution aliases (``chase`` or ``apple_card``) and the values are the public tokens produced
    by the Plaid Link front-end flow. ``transaction_lookback_days`` controls the date range for
    transaction retrieval and defaults to 30 days.
    """

    config = AppConfig.from_env()
    plaid_service = PlaidService(config.plaid)
    storage = S3Storage(config.s3)

    tokens = event.get("public_tokens", {})
    lookback_days = int(event.get("transaction_lookback_days", 30))
    end = _today()
    start = end - timedelta(days=lookback_days)

    accounts_rows: list[dict[str, Any]] = []
    transactions_rows: list[dict[str, Any]] = []
    uploads: dict[str, Any] = {}

    for alias, institution in SUPPORTED_INSTITUTIONS.items():
        public_token = tokens.get(alias)
        if not public_token:
            _LOGGER.info("Skipping institution %s because no public token was provided", alias)
            continue
        access_token = plaid_service.exchange_public_token(public_token)
        metadata = plaid_service.fetch_institution_metadata(institution.id)

        accounts = plaid_service.fetch_accounts(access_token)
        accounts_rows.extend(
            {
                "institution_alias": alias,
                "institution_id": institution.id,
                "institution_name": institution.display_name,
                **account,
            }
            for account in accounts
        )

        transactions = plaid_service.fetch_transactions(access_token, start_date=start, end_date=end)
        transactions_rows.extend(
            {
                "institution_alias": alias,
                "institution_id": institution.id,
                "institution_name": institution.display_name,
                **txn,
            }
            for txn in transactions
        )
        uploads[alias] = {
            "institution": metadata,
            "account_count": len(accounts),
            "transaction_count": len(transactions),
        }

    if accounts_rows:
        accounts_metadata = storage.write_csv(dataset="accounts", rows=accounts_rows)
        uploads["accounts_csv"] = accounts_metadata.to_dict()
    if transactions_rows:
        transactions_metadata = storage.write_csv(dataset="transactions", rows=transactions_rows)
        uploads["transactions_csv"] = transactions_metadata.to_dict()

    return {"uploads": uploads, "institution_tokens": list(tokens.keys())}
