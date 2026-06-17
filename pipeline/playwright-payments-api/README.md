# playwright-payments-api

Playwright Python API test suite for Stripe's payments API.
Built as part of the Cursor Product Quality Engineer application portfolio.

## What this tests
- PaymentIntents (create, retrieve, cancel, error cases)
- Refunds (full, partial, duplicate, over-refund)
- Parallel execution + data isolation (race condition suite)

## Setup
```bash
pip install -r requirements.txt
playwright install chromium
export STRIPE_TEST_KEY=sk_test_xxxx
pytest
pytest -n 4   # parallel — triggers isolation tests
```

## Stripe test cards
- 4242424242424242 — always succeeds
- 4000000000000002 — always declines
- 4000002500003155 — requires 3DS authentication
