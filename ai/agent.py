"""
AgentShield AI Agent

The AI agent is responsible for:
1. Understanding the user's request
2. Selecting a suitable service
3. Sending provider information to AgentShield
4. Asking the authorization layer for permission
5. Proceeding only when AgentShield approves

The AI agent NEVER directly controls payment.
AgentShield remains the security boundary.
"""

import os
import requests
from typing import Optional


AGENTSHIELD_API = os.getenv(
    "AGENTSHIELD_API",
    "http://172.20.10.10:8000"
)

REQUEST_TIMEOUT = 10


class AgentShieldAgent:
    def __init__(self, api_url: str = AGENTSHIELD_API):
        self.api_url = api_url.rstrip("/")

    # ---------------------------------------------------------
    # HEALTH CHECK
    # ---------------------------------------------------------

    def check_system(self):
        """Check whether AgentShield backend is available."""

        try:
            response = requests.get(
                f"{self.api_url}/health",
                timeout=REQUEST_TIMEOUT
            )

            if response.status_code == 200:
                return {
                    "online": True,
                    "message": "AgentShield is online"
                }

            return {
                "online": False,
                "message": f"AgentShield returned HTTP {response.status_code}"
            }

        except requests.RequestException as error:
            return {
                "online": False,
                "message": f"Unable to connect to AgentShield: {error}"
            }

    # ---------------------------------------------------------
    # SERVICE DISCOVERY
    # ---------------------------------------------------------

    def discover_services(self):
        """
        Discover available digital services.

        In the prototype, providers are returned by the
        AgentShield backend.
        """

        try:
            response = requests.get(
                f"{self.api_url}/providers",
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            return data.get("providers", [])

        except requests.RequestException as error:
            print(f"[AI AGENT] Service discovery failed: {error}")
            return []

    # ---------------------------------------------------------
    # SERVICE SELECTION
    # ---------------------------------------------------------

    def select_service(
        self,
        services,
        service_name: Optional[str] = None
    ):
        """
        Select a service from discovered providers.

        If a service name is provided, try to find it.
        Otherwise select the first available provider.
        """

        if not services:
            return None

        if service_name:
            requested = service_name.lower()

            for service in services:
                name = service.get("name", "").lower()
                provider_id = service.get("id", "").lower()

                if requested in name or requested == provider_id:
                    return service

        # Prototype fallback:
        # choose the first available service.
        return services[0]

    # ---------------------------------------------------------
    # TRUST ANALYSIS
    # ---------------------------------------------------------

    def analyze_service(self, service):
        """
        Ask AgentShield's Trust Engine to evaluate a provider.
        """

        payload = {
            "reputation": service.get("reputation", 0),
            "successful_transactions": service.get(
                "successful_transactions",
                0
            ),
            "verified": service.get("verified", False),
            "price": service.get("price", 0)
        }

        try:
            response = requests.post(
                f"{self.api_url}/analyze",
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as error:
            return {
                "error": str(error)
            }

    # ---------------------------------------------------------
    # AUTHORIZATION
    # ---------------------------------------------------------

    def request_authorization(
        self,
        service,
        amount: Optional[float] = None
    ):
        """
        Ask AgentShield whether the AI agent is allowed
        to perform this transaction.

        IMPORTANT:
        The AI agent does NOT decide authorization itself.
        The backend authorization gate does.
        """

        transaction_amount = (
            amount
            if amount is not None
            else service.get("price", 0)
        )

        payload = {
            "service": service.get("name", "Unknown Service"),
            "reputation": service.get("reputation", 0),
            "successful_transactions": service.get(
                "successful_transactions",
                0
            ),
            "verified": service.get("verified", False),
            "price": service.get("price", 0),
            "amount": transaction_amount
        }

        try:
            response = requests.post(
                f"{self.api_url}/authorize",
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as error:
            return {
                "error": str(error)
            }

    # ---------------------------------------------------------
    # COMPLETE AGENT DECISION FLOW
    # ---------------------------------------------------------

    def evaluate_service(
        self,
        service_name: Optional[str] = None,
        amount: Optional[float] = None
    ):
        """
        Complete AI-agent decision flow:

        Discover
            ↓
        Select service
            ↓
        Analyze trust
            ↓
        Request authorization
            ↓
        APPROVE / REVIEW / BLOCK
        """

        print("\n========================================")
        print("        AGENTSHIELD AI AGENT")
        print("========================================")

        # Step 1: Check backend
        health = self.check_system()

        if not health["online"]:
            return {
                "status": "FAILED",
                "reason": health["message"]
            }

        print("[1] AgentShield backend: ONLINE")

        # Step 2: Discover services
        services = self.discover_services()

        if not services:
            return {
                "status": "FAILED",
                "reason": "No services discovered."
            }

        print(f"[2] Services discovered: {len(services)}")

        # Step 3: Select service
        service = self.select_service(
            services,
            service_name
        )

        if not service:
            return {
                "status": "FAILED",
                "reason": "Requested service was not found."
            }

        print(f"[3] Selected service: {service.get('name')}")

        # Step 4: Trust analysis
        analysis = self.analyze_service(service)

        if "error" in analysis:
            return {
                "status": "FAILED",
                "reason": analysis["error"]
            }

        print(
            f"[4] Trust Score: "
            f"{analysis.get('trust_score')}"
        )

        print(
            f"[5] Risk Level: "
            f"{analysis.get('risk_level')}"
        )

        # Step 5: Authorization
        authorization = self.request_authorization(
            service,
            amount
        )

        if "error" in authorization:
            return {
                "status": "FAILED",
                "reason": authorization["error"]
            }

        decision = authorization.get(
            "decision",
            "BLOCK"
        )

        print(f"[6] Authorization Decision: {decision}")

        # -----------------------------------------------------
        # SECURITY BOUNDARY
        # -----------------------------------------------------

        if decision == "APPROVE":

            print("[7] AgentShield: TRANSACTION AUTHORIZED")
            print("[8] Payment layer may proceed.")

            return {
                "status": "AUTHORIZED",
                "service": service,
                "analysis": analysis,
                "authorization": authorization,
                "next_step": "x402 payment"
            }

        if decision == "REVIEW":

            print("[7] AgentShield: TRANSACTION REQUIRES REVIEW")
            print("[8] Payment BLOCKED until review.")

            return {
                "status": "REVIEW",
                "service": service,
                "analysis": analysis,
                "authorization": authorization,
                "next_step": "manual review"
            }

        # Anything other than APPROVE is fail-closed.
        print("[7] AgentShield: TRANSACTION BLOCKED")
        print("[8] Payment will NOT be attempted.")

        return {
            "status": "BLOCKED",
            "service": service,
            "analysis": analysis,
            "authorization": authorization,
            "next_step": "no payment"
        }


# -------------------------------------------------------------
# DEMO
# -------------------------------------------------------------

def main():

    agent = AgentShieldAgent()

    print("\nAgentShield Autonomous Commerce Demo")

    result = agent.evaluate_service(
        service_name="Weather Intelligence API"
    )

    print("\n----------------------------------------")
    print("FINAL AGENT RESULT")
    print("----------------------------------------")

    print(f"Status: {result.get('status')}")

    if result.get("service"):
        print(
            f"Service: "
            f"{result['service'].get('name')}"
        )

    if result.get("analysis"):
        print(
            f"Trust Score: "
            f"{result['analysis'].get('trust_score')}"
        )

    if result.get("authorization"):
        print(
            f"Decision: "
            f"{result['authorization'].get('decision')}"
        )

        print(
            f"Authorized: "
            f"{result['authorization'].get('authorized')}"
        )

        print(
            f"Reason: "
            f"{result['authorization'].get('reason')}"
        )

    print(
        f"Next Step: "
        f"{result.get('next_step')}"
    )


if __name__ == "__main__":
    main()