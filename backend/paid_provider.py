import os

from dotenv import load_dotenv
from fastapi import FastAPI

from x402.http import (
    FacilitatorConfig,
    HTTPFacilitatorClient,
    PaymentOption,
    RouteConfig,
)
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.mechanisms.evm.exact import ExactEvmServerScheme
from x402.server import x402ResourceServer

load_dotenv()

app = FastAPI(title="AgentShield x402 Protected Provider")

PAY_TO = os.getenv("PAY_TO")

if not PAY_TO:
    raise RuntimeError("PAY_TO is missing from .env")

FACILITATOR_URL = os.getenv(
    "FACILITATOR_URL",
    "https://x402.org/facilitator"
)

NETWORK = "eip155:84532"

# Connect to the x402 facilitator
facilitator = HTTPFacilitatorClient(
    FacilitatorConfig(url=FACILITATOR_URL)
)

# Create x402 resource server
server = x402ResourceServer(facilitator)

# Register EVM exact payment scheme
server.register(
    NETWORK,
    ExactEvmServerScheme()
)

# Define the paid route
routes = {
    "GET /paid-weather": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                pay_to=PAY_TO,
                price="$0.001",
                network=NETWORK,
            )
        ],
        mime_type="application/json",
        description="Premium weather intelligence",
    )
}

# Protect the route with x402
app.add_middleware(
    PaymentMiddlewareASGI,
    routes=routes,
    server=server,
)


@app.get("/")
async def root():
    return {
        "service": "Weather Intelligence API",
        "status": "online",
        "payment_protocol": "x402",
    }


@app.get("/paid-weather")
async def paid_weather():
    return {
        "service": "Weather Intelligence API",
        "data": {
            "temperature": "28°C",
            "condition": "Partly Cloudy",
            "humidity": "72%",
        },
        "message": "Premium weather intelligence delivered after x402 payment.",
    }