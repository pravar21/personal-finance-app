"""Configuration models for the Personal Finance App backend."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PlaidConfig:
    """Configuration necessary to communicate with Plaid."""

    client_id: str
    secret: str
    environment: str = "sandbox"
    products: tuple[str, ...] = ("transactions",)
    country_codes: tuple[str, ...] = ("US",)


@dataclass(frozen=True)
class S3Config:
    """Configuration for the AWS S3 bucket where data will be written."""

    bucket: str
    prefix: str = "personal-finance"


@dataclass(frozen=True)
class AppConfig:
    """Aggregate application configuration."""

    plaid: PlaidConfig
    s3: S3Config

    @staticmethod
    def from_env(environ: Mapping[str, str] | None = None) -> "AppConfig":
        env = environ or os.environ
        plaid_config = PlaidConfig(
            client_id=_require(env, "PLAID_CLIENT_ID"),
            secret=_require(env, "PLAID_SECRET"),
            environment=env.get("PLAID_ENV", "sandbox"),
        )
        s3_config = S3Config(
            bucket=_require(env, "DATA_BUCKET"),
            prefix=env.get("DATA_PREFIX", "personal-finance"),
        )
        return AppConfig(plaid=plaid_config, s3=s3_config)


def _require(env: Mapping[str, str], key: str) -> str:
    try:
        value = env[key]
    except KeyError as exc:  # pragma: no cover - defensive programming
        raise ValueError(f"Missing required environment variable: {key}") from exc
    if not value:
        raise ValueError(f"Environment variable {key} must not be empty")
    return value
