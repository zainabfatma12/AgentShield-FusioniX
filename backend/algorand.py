import os
import time

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
            "ALGORAND_BUYER_PRIVATE_KEY is missing from .env"
        )

    if not PROVIDER_ADDRESS:
        raise RuntimeError(
            "ALGORAND_PROVIDER_ADDRESS is missing from .env"
        )

    buyer_address = account.address_from_private_key(
        BUYER_PRIVATE_KEY.strip()
    )

    account_info = algod.account_info(
        buyer_address
    )

    balance_algo = account_info["amount"] / 1_000_000

    print("Buyer:", buyer_address)
    print("Balance:", balance_algo, "ALGO")
    print("Provider:", PROVIDER_ADDRESS)

    if balance_algo < amount_algo:
        raise RuntimeError(
            f"Insufficient ALGO balance. Available: {balance_algo} ALGO"
        )

    params = algod.suggested_params()

    amount_microalgo = int(
        amount_algo * 1_000_000
    )

    txn = PaymentTxn(
        sender=buyer_address,
        sp=params,
        receiver=PROVIDER_ADDRESS,
        amt=amount_microalgo
    )

    signed_txn = txn.sign(
        BUYER_PRIVATE_KEY.strip()
    )

    txid = algod.send_transaction(
        signed_txn
    )

    print("Transaction submitted!")
    print("TXID:", txid)

    return {
        "success": True,
        "status": "submitted",
        "txid": txid,
        "network": "Algorand Testnet",
        "amount": amount_algo,
        "buyer": buyer_address,
        "provider": PROVIDER_ADDRESS
    }