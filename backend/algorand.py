import os
from dotenv import load_dotenv

from algosdk import account
from algosdk.v2client.algod import AlgodClient
from algosdk.transaction import PaymentTxn

load_dotenv()


ALGOD_URL = os.getenv(
    "ALGORAND_ALGOD_URL",
    "https://testnet-api.algonode.cloud"
)

ALGOD_TOKEN = os.getenv(
    "ALGORAND_ALGOD_TOKEN",
    ""
)

BUYER_PRIVATE_KEY = os.getenv(
    "ALGORAND_BUYER_PRIVATE_KEY"
)

PROVIDER_ADDRESS = os.getenv(
    "ALGORAND_PROVIDER_ADDRESS"
)

algod = AlgodClient(
    ALGOD_TOKEN,
    ALGOD_URL
)


def send_algorand_payment(amount_algo: float = 0.001):

    if not BUYER_PRIVATE_KEY:
        raise RuntimeError(
            "ALGORAND_BUYER_PRIVATE_KEY is missing"
        )

    if not PROVIDER_ADDRESS:
        raise RuntimeError(
            "ALGORAND_PROVIDER_ADDRESS is missing"
        )

    # Derive buyer address from private key
    buyer_address = account.address_from_private_key(
        BUYER_PRIVATE_KEY
    )

    # Check balance
    account_info = algod.account_info(
        buyer_address
    )

    balance_algo = (
        account_info["amount"] / 1_000_000
    )

    if balance_algo < amount_algo:
        raise RuntimeError(
            f"Insufficient ALGO balance. "
            f"Available: {balance_algo}"
        )

    # Transaction parameters
    params = algod.suggested_params()

    amount_microalgo = int(
        amount_algo * 1_000_000
    )

    # Create transaction
    txn = PaymentTxn(
        sender=buyer_address,
        sp=params,
        receiver=PROVIDER_ADDRESS,
        amt=amount_microalgo
    )

    # Sign
    signed_txn = txn.sign(
        BUYER_PRIVATE_KEY
    )

    # Submit
    txid = algod.send_transaction(
        signed_txn
    )

    # Wait for confirmation using polling
    confirmed_round = None

    for _ in range(20):

        info = algod.pending_transaction_info(
            txid
        )

        confirmed_round = info.get(
            "confirmed-round",
            0
        )

        if confirmed_round:
            break

        if info.get("pool-error"):
            raise RuntimeError(
                info["pool-error"]
            )

        import time
        time.sleep(1)

    return {
        "success": True,
        "txid": txid,
        "confirmed_round": confirmed_round,
        "network": "Algorand Testnet",
        "amount": amount_algo,
        "buyer": buyer_address,
        "provider": PROVIDER_ADDRESS
    }