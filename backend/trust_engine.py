def calculate_trust_score(
    reputation,
    successful_transactions,
    verified,
    price,
):
    """
    Calculate the trust score of a service provider.
    """

    # Reputation contributes 40%
    reputation_score = reputation * 0.40

    # Transaction history contributes 25%
    transaction_score = min(successful_transactions / 200, 1) * 100
    transaction_score = transaction_score * 0.25

    # Verification contributes 20%
    verification_score = 100 if verified else 0
    verification_score = verification_score * 0.20

    # Price fairness contributes 15%
    if price <= 0.001:
        price_score = 100
    elif price <= 0.005:
        price_score = 80
    elif price <= 0.01:
        price_score = 60
    else:
        price_score = 30

    price_score = price_score * 0.15

    # Final score
    score = (
        reputation_score
        + transaction_score
        + verification_score
        + price_score
    )

    score = round(score)

    # Risk classification
    if score >= 90:
        risk_level = "LOW"
        decision = "APPROVE"

    elif score >= 70:
        risk_level = "MEDIUM"
        decision = "REVIEW"

    else:
        risk_level = "HIGH"
        decision = "BLOCK"

    return {
        "trust_score": score,
        "risk_level": risk_level,
        "decision": decision
    }

if __name__ == "__main__":

    result = calculate_trust_score(
        reputation=98,
        successful_transactions=127,
        verified=True,
        price=0.001
    )

    print(result)
# ==========================================
# AGENTSHIELD PHASE 3
# DECISION ENGINE
# ==========================================

def make_decision(trust_score):

    """
    Decide whether an AI agent should be
    allowed to transact with a service provider.
    """

    if trust_score >= 90:

        return {
            "decision": "APPROVE",
            "risk_level": "LOW",
            "authorized": True,
            "reason": "Provider meets AgentShield trust requirements"
        }

    elif trust_score >= 70:

        return {
            "decision": "REVIEW",
            "risk_level": "MEDIUM",
            "authorized": False,
            "reason": "Provider requires additional verification"
        }

    else:

        return {
            "decision": "BLOCK",
            "risk_level": "HIGH",
            "authorized": False,
            "reason": "Provider trust score is below the transaction threshold"
        }