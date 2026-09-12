def authorize_transaction(trust_score, amount):
    """
    AgentShield authorization gate.

    Trust determines provider risk.
    Transaction amount adds context to the decision.
    """

    if trust_score >= 80 and amount <= 10:
        return {
            "decision": "APPROVE",
            "risk_level": "LOW",
            "authorized": True,
            "reason": "Trusted provider and transaction amount is within the spending limit."
        }

    if trust_score >= 80 and amount > 10:
        return {
            "decision": "REVIEW",
            "risk_level": "MEDIUM",
            "authorized": False,
            "reason": "Provider is trusted, but the transaction amount requires review."
        }

    if trust_score >= 60:
        return {
            "decision": "REVIEW",
            "risk_level": "MEDIUM",
            "authorized": False,
            "reason": "Provider has moderate trust and requires additional verification."
        }

    return {
        "decision": "BLOCK",
        "risk_level": "HIGH",
        "authorized": False,
        "reason": "Provider trust score is below the authorization threshold."
    }