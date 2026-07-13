"""
Thin wrapper around Paystack's REST API for transaction initialization
and verification. Uses the secret key from settings (which reads from
your .env file — see .env.example -> PAYSTACK_SECRET_KEY).

Docs: https://paystack.com/docs/api/transaction/

To make this live:
    1. Create a free Paystack account: https://dashboard.paystack.com/#/signup
    2. Go to Settings -> API Keys & Webhooks
    3. Copy the TEST secret key (starts with sk_test_...)
    4. Paste it into your .env file as PAYSTACK_SECRET_KEY
No real money moves in test mode — Paystack gives you fake test cards
(see the testing guide in the README) so you can simulate full payments.
"""

import requests
from django.conf import settings


class PaystackError(Exception):
    """Raised when Paystack's API returns an error or is unreachable."""


def _headers():
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def initialize_transaction(email: str, amount: float, reference: str, callback_url: str = None) -> dict:
    """
    Starts a Paystack transaction. Amount must be sent in kobo (smallest
    currency unit), so we multiply by 100. Returns Paystack's response data
    dict, which includes `authorization_url` (where the customer pays) and
    `access_code`.
    """
    if not settings.PAYSTACK_SECRET_KEY:
        raise PaystackError(
            "PAYSTACK_SECRET_KEY is not set. Add your test secret key to .env."
        )

    payload = {
        "email": email,
        "amount": int(round(amount * 100)),
        "reference": reference,
    }
    if callback_url:
        payload["callback_url"] = callback_url

    try:
        response = requests.post(
            f"{settings.PAYSTACK_BASE_URL}/transaction/initialize",
            json=payload,
            headers=_headers(),
            timeout=15,
        )
    except requests.RequestException as exc:
        raise PaystackError(f"Could not reach Paystack: {exc}") from exc

    body = response.json()
    if not response.ok or not body.get("status"):
        raise PaystackError(body.get("message", "Paystack initialization failed."))

    return body["data"]


def verify_transaction(reference: str) -> dict:
    """
    Confirms whether a transaction reference was actually paid. Always call
    this server-side before marking an order as paid — never trust the
    frontend's redirect alone.
    """
    if not settings.PAYSTACK_SECRET_KEY:
        raise PaystackError(
            "PAYSTACK_SECRET_KEY is not set. Add your test secret key to .env."
        )

    try:
        response = requests.get(
            f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}",
            headers=_headers(),
            timeout=15,
        )
    except requests.RequestException as exc:
        raise PaystackError(f"Could not reach Paystack: {exc}") from exc

    body = response.json()
    if not response.ok or not body.get("status"):
        raise PaystackError(body.get("message", "Paystack verification failed."))

    return body["data"]
