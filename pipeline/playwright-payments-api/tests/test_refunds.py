import pytest
from playwright.sync_api import APIRequestContext

@pytest.fixture(scope="function")
def confirmed_charge(stripe_context: APIRequestContext):
    response = stripe_context.post("/v1/charges", form={
        "amount": "5000",
        "currency": "usd",
        "source": "tok_visa",
        "description": "Test charge for refund tests",
    })
    assert response.status == 200
    return response.json()

def test_full_refund(stripe_context: APIRequestContext, confirmed_charge):
    """P1 — Full refund on a successful charge."""
    response = stripe_context.post("/v1/refunds", form={
        "charge": confirmed_charge["id"],
    })
    assert response.status == 200
    data = response.json()
    assert data["amount"] == confirmed_charge["amount"]
    assert data["status"] == "succeeded"

def test_partial_refund(stripe_context: APIRequestContext, confirmed_charge):
    """P1 — Partial refund should return the refunded amount only."""
    response = stripe_context.post("/v1/refunds", form={
        "charge": confirmed_charge["id"],
        "amount": "2000",
    })
    assert response.status == 200
    assert response.json()["amount"] == 2000

def test_duplicate_refund_fails(stripe_context: APIRequestContext, confirmed_charge):
    """P0 — Refunding an already-fully-refunded charge should return error."""
    stripe_context.post("/v1/refunds", form={"charge": confirmed_charge["id"]})
    second = stripe_context.post("/v1/refunds", form={"charge": confirmed_charge["id"]})
    assert second.status == 400
    assert second.json()["error"]["code"] == "charge_already_refunded"

def test_refund_exceeds_charge(stripe_context: APIRequestContext, confirmed_charge):
    """P1 — Refund amount greater than charge should be rejected."""
    response = stripe_context.post("/v1/refunds", form={
        "charge": confirmed_charge["id"],
        "amount": "9999999",
    })
    assert response.status == 400
