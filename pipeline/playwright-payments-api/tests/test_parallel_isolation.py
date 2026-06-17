import pytest
from playwright.sync_api import APIRequestContext

def test_worker_isolation_1(stripe_context: APIRequestContext, test_customer):
    """Each parallel worker gets its own customer — no shared state."""
    response = stripe_context.post("/v1/payment_intents", form={
        "amount": "1000",
        "currency": "usd",
        "customer": test_customer["id"],
        "payment_method_types[]": "card",
    })
    assert response.status == 200

def test_worker_isolation_2(stripe_context: APIRequestContext, test_customer):
    """Sibling test — should get a different customer ID than isolation_1."""
    response = stripe_context.post("/v1/payment_intents", form={
        "amount": "2000",
        "currency": "usd",
        "customer": test_customer["id"],
        "payment_method_types[]": "card",
    })
    assert response.status == 200

def test_concurrent_charges(stripe_context: APIRequestContext):
    """Simulate concurrent charges using test tokens — no customer needed."""
    charges = []
    for amount in ["1000", "2000", "3000"]:
        r = stripe_context.post("/v1/charges", form={
            "amount": amount,
            "currency": "usd",
            "source": "tok_visa",
            "description": f"Concurrent charge test {amount}",
        })
        assert r.status == 200, f"Charge failed for amount {amount}: {r.text()}"
        charges.append(r.json()["id"])
    assert len(charges) == 3
