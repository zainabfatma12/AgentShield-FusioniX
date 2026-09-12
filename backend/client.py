import asyncio
import os
import sys
from decimal import Decimal

import httpx
from dotenv import load_dotenv
from eth_account import Account

from x402 import x402Client
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client


# ============================================================
# AgentShield x402 Client
# ============================================================

load_dotenv()


# ============================================================
# Configuration
# ============================================================

AGENTSHIELD_API = os.getenv(
    "AGENTSHIELD_API",
    "http://172.20.10.10:8000"
)

PAID_RESOURCE_URL = os.getenv(
    "PAID_RESOURCE_URL",
    ""
)

EVM_PRIVATE_KEY = os.getenv("EVM_PRIVATE_KEY")

MAX_PAYMENT_USD = Decimal(
    os.getenv("MAX_PAYMENT_USD", "0.05")
)


# ============================================================
# Wallet
# ============================================================

def require_private_key():
    """
    Load and validate the buyer wallet.

    NEVER print the private key.
    """

    if not EVM_PRIVATE_KEY:
        raise RuntimeError(
            "EVM_PRIVATE_KEY is missing from .env\n\n"
            "Add the PRIVATE KEY of the EVM test wallet.\n"
            "Do NOT use the wallet address here."
        )

    try:
        account = Account.from_key(EVM_PRIVATE_KEY)

    except Exception as exc:
        raise RuntimeError(
            "EVM_PRIVATE_KEY is invalid.\n"
            "Check that the private key belongs to the "
            "EVM wallet and is stored correctly in .env."
        ) from exc

    return account


# ============================================================
# Step 1 — AgentShield Health
# ============================================================

async def check_agentshield_health():

    print("\n[1/4] Checking AgentShield backend...")

    async with httpx.AsyncClient(timeout=10) as http:

        response = await http.get(
            f"{AGENTSHIELD_API}/health"
        )

        response.raise_for_status()

        data = response.json()

        print("      AgentShield:", data)


# ============================================================
# Step 2 — AgentShield Authorization
# ============================================================

async def authorize_transaction(
    service: str,
    reputation: float,
    successful_transactions: int,
    verified: bool,
    price: float,
    amount: float
):
    """
    Ask AgentShield whether the transaction is allowed.

    IMPORTANT:
    Payment MUST NOT happen unless AgentShield
    returns APPROVE.
    """

    print("\n[2/4] Asking AgentShield authorization engine...")

    payload = {
        "service": service,
        "reputation": reputation,
        "successful_transactions": successful_transactions,
        "verified": verified,
        "price": price,
        "amount": amount
    }

    async with httpx.AsyncClient(timeout=15) as http:

        response = await http.post(
            f"{AGENTSHIELD_API}/authorize",
            json=payload
        )

        response.raise_for_status()

        result = response.json()

        print(
            "      Service:",
            result.get("service")
        )

        print(
            "      Trust Score:",
            result.get("trust_score")
        )

        print(
            "      Risk Level:",
            result.get("risk_level")
        )

        print(
            "      Decision:",
            result.get("decision")
        )

        print(
            "      Authorized:",
            result.get("authorized")
        )

        print(
            "      Amount:",
            result.get("amount")
        )

        print(
            "      Reason:",
            result.get("reason")
        )

        return result


# ============================================================
# Step 3 — x402 Payment
# ============================================================

async def perform_x402_payment():

    print("\n[3/4] Starting x402 payment client...")

    if not PAID_RESOURCE_URL:

        raise RuntimeError(
            "PAID_RESOURCE_URL is missing from .env\n\n"
            "Set it to the actual x402-protected "
            "provider endpoint before running the payment flow."
        )

    account = require_private_key()

    print(
        "      Buyer wallet:",
        account.address
    )

    print(
        "      Maximum payment:",
        f"${MAX_PAYMENT_USD}"
    )

    # Create x402 client
    client = x402Client()

    # Register EVM payment mechanism
    register_exact_evm_client(
        client,
        EthAccountSigner(account)
    )

    # x402 HTTP client
    async with x402HttpxClient(
        client) as http:

        print(
            "      Requesting:",
            PAID_RESOURCE_URL
        )

        response = await http.get(
            PAID_RESOURCE_URL
        )
        print("Response headers:", dict(response.headers))

        await response.aread()

        print(
            "      Provider status:",
            response.status_code
        )

        print(
            "      Provider response:",
            response.text[:1000]
        )

        return response


# ============================================================
# Main AgentShield Flow
# ============================================================

async def main():

    print("\n")
    print("=" * 62)
    print("        AGENTSHIELD — x402 PAYMENT CLIENT")
    print("=" * 62)

    try:

        # ----------------------------------------------------
        # STEP 1
        # Check AgentShield backend
        # ----------------------------------------------------

        await check_agentshield_health()


        # ----------------------------------------------------
        # STEP 2
        # Ask AgentShield for authorization
        # ----------------------------------------------------

        authorization = await authorize_transaction(

            service="Weather Intelligence API",

            reputation=98,

            successful_transactions=127,

            verified=True,

            price=0.001,

            amount=0.001
        )


        # ----------------------------------------------------
        # SECURITY BOUNDARY
        # ----------------------------------------------------

        decision = str(
            authorization.get(
                "decision",
                ""
            )
        ).upper()

        authorized = bool(
            authorization.get(
                "authorized",
                False
            )
        )


        # ----------------------------------------------------
        # BLOCK PAYMENT
        # ----------------------------------------------------

        if decision not in {
            "APPROVE",
            "APPROVED"
        } or not authorized:

            print("\n" + "=" * 62)
            print("       PAYMENT BLOCKED BY AGENTSHIELD")
            print("=" * 62)

            print(
                "\nThe x402 client was NOT allowed "
                "to attempt payment."
            )

            print(
                "\nAuthorization result:"
            )

            print(
                authorization
            )

            return


        # ----------------------------------------------------
        # APPROVED
        # ----------------------------------------------------

        print("\n" + "=" * 62)
        print("       AGENTSHIELD AUTHORIZATION APPROVED")
        print("=" * 62)

        print(
            "\n✓ Provider trusted"
        )

        print(
            "✓ Transaction authorized"
        )

        print(
            "✓ x402 payment may proceed"
        )


        # ----------------------------------------------------
        # STEP 3
        # Execute x402 payment
        # ----------------------------------------------------

        response = await perform_x402_payment()


        # ----------------------------------------------------
        # STEP 4
        # Final result
        # ----------------------------------------------------

        print("\n[4/4] Transaction result")

        if response.is_success:

            print(
                "\n✓ PAYMENT FLOW COMPLETED"
            )

            print(
                "✓ Provider response received"
            )

            # Look for payment/settlement information
            # in response headers.

            print(
                "\nPayment / settlement headers:"
            )

            found_header = False

            for key, value in response.headers.items():

                key_lower = key.lower()

                if (
                    "payment" in key_lower
                    or "receipt" in key_lower
                    or "settle" in key_lower
                    or "transaction" in key_lower
                ):

                    print(
                        f"  {key}: {value}"
                    )

                    found_header = True

            if not found_header:

                print(
                    "  No payment/settlement "
                    "header exposed by provider."
                )

        else:

            print(
                "\n✗ Payment/resource request "
                "did not succeed."
            )

            print(
                "HTTP status:",
                response.status_code
            )


    except Exception as exc:

        print("\n" + "=" * 62)
        print("       AGENTSHIELD CLIENT ERROR")
        print("=" * 62)

        print(
            "\n",
            type(exc).__name__,
            ":",
            exc
        )

        sys.exit(1)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    asyncio.run(main())