"""Plaid integration helpers used by the Personal Finance App backend."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Dict, Iterable, List

from plaid import ApiClient, Configuration, Environment
from plaid.api import plaid_api
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest

from .config import PlaidConfig

_LOGGER = logging.getLogger(__name__)


PLAID_ENVIRONMENTS = {
    "sandbox": Environment.Sandbox,
    "development": Environment.Development,
    "production": Environment.Production,
}


@dataclass(frozen=True)
class Institution:
    """Represents a supported Plaid institution."""

    id: str
    display_name: str


SUPPORTED_INSTITUTIONS: Dict[str, Institution] = {
    "chase": Institution(id="ins_3", display_name="JPMorgan Chase"),
    # Apple's credit card is issued by Goldman Sachs, which is represented by this Plaid ID.
    "apple_card": Institution(id="ins_130893", display_name="Apple Card"),
}


class PlaidService:
    """Facade over the Plaid API used by the Lambda functions."""

    def __init__(self, config: PlaidConfig) -> None:
        environment = PLAID_ENVIRONMENTS.get(config.environment, Environment.Sandbox)
        configuration = Configuration(
            host=environment,
            api_key={
                "clientId": config.client_id,
                "secret": config.secret,
            },
        )
        api_client = ApiClient(configuration)
        self._client = plaid_api.PlaidApi(api_client)
        self._products = list(config.products)
        self._country_codes = list(config.country_codes)

    def exchange_public_token(self, public_token: str) -> str:
        """Exchange a public token for an access token."""

        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self._client.item_public_token_exchange(request)
        access_token = response["access_token"]
        _LOGGER.info("Successfully exchanged public token for item %s", response["item_id"])
        return access_token

    def fetch_accounts(self, access_token: str) -> List[dict]:
        """Return all accounts associated with the Plaid item."""

        request = AccountsGetRequest(access_token=access_token)
        response = self._client.accounts_get(request)
        return [account.to_dict() for account in response["accounts"]]

    def fetch_transactions(
        self,
        access_token: str,
        start_date: date,
        end_date: date,
        *,
        count: int = 500,
    ) -> List[dict]:
        """Fetch transactions between ``start_date`` and ``end_date`` for the Plaid item."""

        transactions: List[dict] = []
        offset = 0
        while True:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                options={"count": count, "offset": offset},
            )
            response = self._client.transactions_get(request)
            transactions.extend(txn.to_dict() for txn in response["transactions"])
            if len(transactions) >= response["total_transactions"]:
                break
            offset += count
        return transactions

    def fetch_institution_metadata(self, institution_id: str) -> dict:
        request = InstitutionsGetByIdRequest(institution_id=institution_id, country_codes=self._country_codes)
        response = self._client.institutions_get_by_id(request)
        return response["institution"].to_dict()

    @staticmethod
    def list_supported_institutions() -> Iterable[Institution]:
        return SUPPORTED_INSTITUTIONS.values()
