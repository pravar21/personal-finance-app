# Personal Finance App Backend

This repository contains the first iteration of a serverless backend for a personal finance app.
The current focus is on collecting account and transaction data from Plaid for Chase and Apple
Card users and exporting that data into Amazon S3 as CSV files that can be consumed by analytics
jobs or downstream services.

## Architecture

* **AWS Lambda** — A function (`personal_finance_app.lambda_handler`) exchanges public tokens for
  Plaid access tokens, retrieves account and transaction data, and exports the result to S3.
* **Plaid API** — Integrations for Chase (`ins_3`) and Apple Card (`ins_130893`) using the
  official Plaid Python SDK.
* **Amazon S3** — Raw data is stored as CSV files named after the dataset and capture timestamp.

```
┌──────────────┐   public token   ┌──────────────┐   access token   ┌────────────┐
│  Plaid Link  │ ───────────────▶ │ AWS Lambda   │ ───────────────▶ │ Plaid API  │
└──────────────┘                  │ (this repo)  │                  └────────────┘
       │                          │              │
       │ accounts/transactions    │              │ CSV export
       ▼                          ▼              ▼
┌──────────────┐   S3 CSV Files   ┌──────────────────────────────────────────────┐
│  Analytics   │ ◀──────────────── │ s3://<bucket>/<prefix>/{accounts,transactions} │
└──────────────┘                  └──────────────────────────────────────────────┘
```

## Local Development

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Export the required environment variables:

   ```bash
   export PLAID_CLIENT_ID=your-client-id
   export PLAID_SECRET=your-secret
   export PLAID_ENV=sandbox  # or development/production
   export DATA_BUCKET=your-s3-bucket
   export DATA_PREFIX=personal-finance
   ```

3. Invoke the Lambda handler locally:

   ```python
   from personal_finance_app.lambda_handler import lambda_handler

   event = {
       "public_tokens": {
           "chase": "public-token-from-link",
           "apple_card": "public-token-from-link",
       },
       "transaction_lookback_days": 45,
   }

   response = lambda_handler(event, None)
   print(response)
   ```

   Successful execution writes `accounts_*.csv` and `transactions_*.csv` files to the configured
   S3 bucket and returns upload metadata.

## Testing

Run the automated test suite with `pytest`:

```bash
pytest
```

The included unit test validates the S3 export pipeline end-to-end using a lightweight in-memory
stub, so no AWS resources are required.
