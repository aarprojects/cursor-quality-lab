import pytest
from playwright.sync_api import Playwright, APIRequestContext
from typing import Generator
import os

STRIPE_BASE_URL = "https://api.stripe.com/v1"
STRIPE_TEST_KEY = os.getenv("STRIPE_TEST_KEY", "sk_test_YOUR_KEY_HERE")

@pytest.fixture(scope="session")
def stripe_context(playwright: Playwright) -> Generator[APIRequestContext, None, None]:
    context = playwright.request.new_context(
        base_url=STRIPE_BASE_URL,
        extra_http_headers={
            "Authorization": f"Bearer {STRIPE_TEST_KEY}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Stripe-Version": "2023-10-16",
        }
    )
    yield context
    context.dispose()

@pytest.fixture(scope="function")
def test_customer(stripe_context: APIRequestContext):
    response = stripe_context.post("/customers", form={
        "email": "test_user@example.com",
        "name": "Test Customer",
        "description": "Created by playwright-payments-api test suite",
    })
    assert response.status == 200, f"Customer creation failed: {response.text()}"
    customer = response.json()
    yield customer
    stripe_context.delete(f"/customers/{customer['id']}")

@pytest.fixture(scope="function")
def test_payment_method(stripe_context: APIRequestContext):
    response = stripe_context.post("/payment_methods", form={
        "type": "card",
        "card[number]": "4242424242424242",
        "card[exp_month]": "12",
        "card[exp_year]": "2026",
        "card[cvc]": "123",
    })
    assert response.status == 200
    return response.json()
