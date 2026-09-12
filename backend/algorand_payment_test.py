import os
import time
from pathlib import Path

from dotenv import load_dotenv, set_key
from algosdk import account, mnemonic
from algosdk.v2client.algod import AlgodClient
from algosdk.transaction import PaymentTxn
from algosdk.encoding import decode_address


# ============================================================
# AGENTSHIELD - ALGORAND TESTNET PAYMENT
# ============================================================

ENV_FILE = Path(__file__).resolve().parent / ".env"

load_dotenv(ENV_FILE, override=True)


# ============================================================
# CONFIGURATION
# ============================================================

ALGOD_URL = os.getenv(
    "ALGORAND_ALGOD_URL",
    "https://testnet-api.algonode.cloud"
)

ALGOD_TOKEN = os.getenv(
    "ALGORAND_ALGOD_TOKEN",
    ""
)

BUYER_ADDRESS = os.getenv(
    "ALGORAND_BUYER_ADDRESS",
    ""
).strip()

BUYER_PRIVATE_KEY = os.getenv(
    "ALGORAND_BUYER_PRIVATE_KEY",
    ""
).strip()

PROVIDER_ADDRESS = os.getenv(
    "ALGORAND_PROVIDER_ADDRESS",
    ""
).strip()

AMOUNT_ALGO = float(
    os.getenv("AMOUNT_ALGO", "0.001")
)


# ============================================================
# HEADER
# ============================================================

print("\n" + "=" * 65)
print("        AGENTSHIELD - ALGORAND TESTNET")
print("              PAYMENT ENGINE")
print("=" * 65)


# ============================================================
# CONNECT
# ============================================================

print("\n[1/7] Connecting to Algorand Testnet...")

algod = AlgodClient(
    ALGOD_TOKEN,
    ALGOD_URL
)

try:
    status = algod.status()

    print("      Algorand node: ONLINE ✅")
    print(
        "      Last round:",
        status.get("last-round")
    )

except Exception as e:
    raise RuntimeError(
        f"Could not connect to Algorand Testnet: {e}"
    )


# ============================================================
# BUYER WALLET
# ============================================================

print("\n[2/7] Loading buyer wallet...")


if BUYER_PRIVATE_KEY:

    print("      Existing Algorand private key found.")

    try:

        derived_address = account.address_from_private_key(
            BUYER_PRIVATE_KEY
        )

    except Exception as e:

        raise RuntimeError(
            "ALGORAND_BUYER_PRIVATE_KEY is invalid.\n"
            f"Error: {e}"
        )

    BUYER_ADDRESS = derived_address

else:

    print("      No buyer private key found.")
    print("      Creating Algorand Testnet buyer wallet...")

    BUYER_PRIVATE_KEY, BUYER_ADDRESS = (
        account.generate_account()
    )

    BUYER_MNEMONIC = mnemonic.from_private_key(
        BUYER_PRIVATE_KEY
    )

    set_key(
        str(ENV_FILE),
        "ALGORAND_BUYER_ADDRESS",
        BUYER_ADDRESS
    )

    set_key(
        str(ENV_FILE),
        "ALGORAND_BUYER_PRIVATE_KEY",
        BUYER_PRIVATE_KEY
    )

    set_key(
        str(ENV_FILE),
        "ALGORAND_BUYER_MNEMONIC",
        BUYER_MNEMONIC
    )

    print("      New buyer wallet created ✅")


print("\n      BUYER:")
print("     ", BUYER_ADDRESS)


# ============================================================
# VALIDATE BUYER
# ============================================================

print("\n[3/7] Validating buyer address...")

try:

    decode_address(BUYER_ADDRESS)

except Exception:

    raise RuntimeError(
        "Invalid Algorand buyer address."
    )

print("      Buyer address valid ✅")


# ============================================================
# PROVIDER
# ============================================================

print("\n[4/7] Validating provider address...")


if not PROVIDER_ADDRESS:

    print("      No provider address found.")
    print("      Creating provider wallet...")

    provider_private_key, PROVIDER_ADDRESS = (
        account.generate_account()
    )

    provider_mnemonic = mnemonic.from_private_key(
        provider_private_key
    )

    set_key(
        str(ENV_FILE),
        "ALGORAND_PROVIDER_ADDRESS",
        PROVIDER_ADDRESS
    )

    set_key(
        str(ENV_FILE),
        "ALGORAND_PROVIDER_MNEMONIC",
        provider_mnemonic
    )

else:

    try:

        decode_address(PROVIDER_ADDRESS)

    except Exception:

        raise RuntimeError(
            "ALGORAND_PROVIDER_ADDRESS is not "
            "a valid Algorand address."
        )


print("\n      PROVIDER:")
print("     ", PROVIDER_ADDRESS)


# ============================================================
# CHECK BALANCE
# ============================================================

print("\n[5/7] Checking buyer Testnet ALGO balance...")

try:

    account_info = algod.account_info(
        BUYER_ADDRESS
    )

except Exception as e:

    raise RuntimeError(
        f"Could not read buyer account: {e}"
    )


balance_microalgo = account_info.get(
    "amount",
    0
)

balance_algo = balance_microalgo / 1_000_000

print(
    f"      Balance: {balance_algo:.6f} ALGO"
)


if balance_algo < AMOUNT_ALGO:

    print("\n" + "!" * 65)
    print("       BUYER NEEDS TESTNET ALGO")
    print("!" * 65)

    print("\nFund this address:")

    print(BUYER_ADDRESS)

    print(
        f"\nRequired: {AMOUNT_ALGO} ALGO"
    )

    print(
        "\nAfter funding, run:"
    )

    print(
        "python .\\algorand_payment_test.py"
    )

    raise SystemExit(0)


# ============================================================
# CREATE TRANSACTION
# ============================================================

print("\n[6/7] Creating Algorand payment...")

params = algod.suggested_params()

amount_microalgo = int(
    AMOUNT_ALGO * 1_000_000
)

transaction = PaymentTxn(
    sender=BUYER_ADDRESS,
    sp=params,
    receiver=PROVIDER_ADDRESS,
    amt=amount_microalgo
)

print("\n      Transaction details:")
print("      --------------------")
print("      Network :", "Algorand Testnet")
print("      From    :", BUYER_ADDRESS)
print("      To      :", PROVIDER_ADDRESS)
print("      Amount  :", AMOUNT_ALGO, "ALGO")


# ============================================================
# SIGN
# ============================================================

print("\n      Signing transaction...")

try:

    signed_transaction = transaction.sign(
        BUYER_PRIVATE_KEY
    )

except Exception as e:

    raise RuntimeError(
        f"Algorand signing failed: {e}"
    )

print(
    "      Transaction signed successfully ✅"
)


# ============================================================
# SEND
# ============================================================

print("\n[7/7] Sending transaction to Algorand...")

try:

    txid = algod.send_transaction(
        signed_transaction
    )

except Exception as e:

    raise RuntimeError(
        f"Transaction submission failed: {e}"
    )


print("\n      Transaction submitted ✅")

print("\n      TXID:")
print("     ", txid)


# ============================================================
# CONFIRMATION
# ============================================================

print("\n      Waiting for blockchain confirmation...")

confirmed = False
confirmation = None

try:

    # Algorand SDK version in your environment does not provide
    # algod.wait_for_confirmation(), so we poll the transaction.

    for attempt in range(20):

        info = algod.pending_transaction_info(
            txid
        )

        confirmed_round = info.get(
            "confirmed-round",
            0
        )

        pool_error = info.get(
            "pool-error",
            ""
        )

        if pool_error:

            raise RuntimeError(
                f"Algorand transaction rejected: {pool_error}"
            )

        if confirmed_round and confirmed_round > 0:

            confirmed = True
            confirmation = info

            break

        print(
            f"      Waiting... {attempt + 1}/20"
        )

        time.sleep(2)


except Exception as e:

    print(
        "\n      Confirmation check error:",
        e
    )


# ============================================================
# FINAL RESULT
# ============================================================

print("\n" + "=" * 65)

if confirmed:

    print("        ALGORAND PAYMENT SUCCESSFUL ✅")

else:

    print("        TRANSACTION SUBMITTED ✅")

print("=" * 65)

print("\nTransaction ID:")
print(txid)

if confirmed:

    print(
        "\nConfirmed round:",
        confirmation.get("confirmed-round")
    )

print(
    "\nAmount:",
    AMOUNT_ALGO,
    "ALGO"
)

print("\nBuyer:")
print(BUYER_ADDRESS)

print("\nProvider:")
print(PROVIDER_ADDRESS)

print("\nNetwork: Algorand Testnet")

print("\n" + "=" * 65)
print("       AGENTSHIELD ALGORAND PHASE COMPLETE")
print("=" * 65)