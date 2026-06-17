import pytest
from playwright.sync_api import APIRequestContext

def test_create_payment_intent(stripe_context: APIRequestContext, test_customer):
    """P1 — Core flow: create a payment intent for a customer."""
    response = stripe_context.post("/payment_intents", form={
        "amount": "2000",
        "currency": "usd",
        "customer": test_customer["id"],
        "payment_method_types[]": "card",
    })
    assert response.status == 200
    data = response.json()
    assert data["object"] == "payment_intent"
    assert data["amount"] == 2000
    assert data["currency"] == "usd"
    assert data["status"] == "requires_payment_method"
    assert data["customer"] == test_customer["id"]

def test_payment_intent_invalid_currency(stripe_context: APIRequestContext):
    """P1 — Error handling: invalid currency should return 400."""
    response = stripe_context.post("/payment_intents", form={
        "amount": "1000",
        "currency": "xyz",
        "payment_method_types[]": "card",
    })
    assert response.status == 400
    error = response.json()
    assert error["error"]["type"] == "invalid_request_error"

def test_payment_intent_below_minimum(stripe_context: APIRequestContext):
    """P2 — Edge case: amount below Stripe minimum should fail."""
    response = stripe_context.post("/payment_intents", form={
        "amount": "10",
        "currency": "usd",
        "payment_method_types[]": "card",
    })
    assert response.status == 400

def test_retrieve_payment_intent(stripe_context: APIRequestContext, test_customer):
    """P1 — Create then retrieve — verifies idempotency."""
    create = stripe_context.post("/payment_intents", form={
        "amount": "5000",
        "currency": "usd",
        "customer": test_customer["id"],
        "payment_method_types[]": "card",
    })
    assert create.status == 200
    pi_id = create.json()["id"]
    get = stripe_context.get(f"/payment_intents/{pi_id}")
    assert get.status == 200
    assert get.json()["id"] == pi_id

def test_cancel_payment_intent(stripe_context: APIRequestContext, test_customer):
    """P1 — Cancel a payment intent before confirmation."""
    create = stripe_context.post("/payment_intents", form={
        "amount": "3000",
        "currency": "usd",
        "customer": test_customer["id"],
        "payment_method_types[]": "card",
    })
    pi_id = create.json()["id"]
    cancel = stripe_context.post(f"/payment_intents/{pi_id}/cancel")
    assert cancel.status == 200
    assert cancel.json()["status"] == "canceled"

def test_payment_intent_missing_amount(stripe_context: APIRequestContext):
    """P0 — Required field missing: no amount should return 400."""
    response = stripe_context.post("/payment_intents", form={
        "currency": "usd",
        "payment_method_types[]": "card",
    })
    assert response.status == 400
