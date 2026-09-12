"""Algorand network selection for x402 settlement."""

import os

from dotenv import load_dotenv

load_dotenv()

FACILITATOR_URL = os.getenv(
    "FACILITATOR_URL",
    "https://facilitator.goplausible.xyz"
)

NETWORKS = {
    "testnet": {
        "name": "testnet",
        "label": "Algorand Testnet",
        "caip2": "algorand:SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=",
        "genesis_id": "testnet-v1.0",
        "genesis_hash": "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI=",
        "usdc_asset": "10458941",
        "algod_url": "https://testnet-api.algonode.cloud",
        "explorer_tx": "https://lora.algokit.io/testnet/transaction/{txid}",
        "default_paid_resource": (
            "https://example.x402.goplausible.xyz/avm/weather"
        ),
    },
    "mainnet": {
        "name": "mainnet",
        "label": "Algorand Mainnet",
        "caip2": "algorand:wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8=",
        "genesis_id": "mainnet-v1.0",
        "genesis_hash": "wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8=",
        "usdc_asset": "31566704",
        "algod_url": "https://mainnet-api.algonode.cloud",
        "explorer_tx": "https://lora.algokit.io/mainnet/transaction/{txid}",
        "default_paid_resource": "",
    },
}


def get_network_config() -> dict:
    raw = (os.getenv("ALGORAND_NETWORK") or "").strip().lower()
    if raw not in NETWORKS:
        raise RuntimeError(
            "ALGORAND_NETWORK must be 'testnet' or 'mainnet'."
        )

    pay_to = (os.getenv("PAY_TO") or "").strip()
    if not pay_to:
        raise RuntimeError("PAY_TO is required.")

    config = dict(NETWORKS[raw])
    config["pay_to"] = pay_to
    config["facilitator"] = FACILITATOR_URL
    config["algod_url"] = os.getenv(
        "ALGORAND_ALGOD_URL",
        config["algod_url"]
    )

    paid_url = (os.getenv("PAID_RESOURCE_URL") or "").strip()
    if not paid_url:
        paid_url = config["default_paid_resource"]
    if config["name"] == "mainnet" and not paid_url:
        raise RuntimeError(
            "PAID_RESOURCE_URL is required when ALGORAND_NETWORK=mainnet."
        )

    config["paid_resource_url"] = paid_url
    return config


def explorer_url(txid: str | None, network: str | None = None) -> str | None:
    if not txid:
        return None
    config = get_network_config()
    if network and "wGHE2Pwdvd7S12BL5FaOP20EGYesN73ktiC1qzkkit8=" in network:
        return f"https://lora.algokit.io/mainnet/transaction/{txid}"
    return config["explorer_tx"].format(txid=txid)
