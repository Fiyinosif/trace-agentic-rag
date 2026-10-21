
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "data" / "evaluation_cases.json"

# These are synthetic research fixtures, not real threat
# intelligence or quotations from FTC/NIST.
SCENARIOS = [
    {
        "name": "account_suspension",
        "message": (
            "From: Microsoft IT Support\n"
            "Your account will be suspended today. "
            "Enter your password at "
            "https://microsoft-login.example.com"
        ),
        "indicator": "The message requests a password through a link.",
        "unsupported": "The URL is confirmed malicious.",
        "benign": "The sender's domain has been independently verified.",
    },
    {
        "name": "bank_verification",
        "message": (
            "Security alert: Your bank account is locked. "
            "Confirm your login details immediately at "
            "https://bank-check.example.com"
        ),
        "indicator": "The message requests banking login details.",
        "unsupported": "The bank confirmed that this is a phishing campaign.",
        "benign": "The message was authenticated by the bank.",
    },
    {
        "name": "delivery_payment",
        "message": (
            "Delivery failed. Pay a redelivery fee today at "
            "https://parcel-fee.example.com"
        ),
        "indicator": "The message requests a redelivery payment.",
        "unsupported": "The payment page has stolen credit card information.",
        "benign": "The courier verified the payment request.",
    },
    {
        "name": "university_login",
        "message": (
            "Campus IT: Your student email expires tonight. "
            "Sign in at https://campus-verify.example.com "
            "to prevent account deletion."
        ),
        "indicator": "The message requests account sign-in.",
        "unsupported": "The university confirmed the link is fraudulent.",
        "benign": "The university confirmed the notice is genuine.",
    },
    {
        "name": "payroll_update",
        "message": (
            "Payroll notice: Update your direct deposit details "
            "before 5 PM at https://payroll-update.example.com"
        ),
        "indicator": "The message requests payroll information.",
        "unsupported": "The website is operated by a criminal organization.",
        "benign": "The payroll department authenticated the notice.",
    },
]

def passage(evidence_id, content, kind):
    return {
        "evidence_id": evidence_id,
        "content": content,
        "source": "Synthetic evaluation fixture",
        "source_url": "",
        "organization": "Trace Research",
        "authority": 0.0,
        "reranker_score": 0.0,
        "kind": kind,
    }

def build_evidence(scenario, condition):
    relevant = passage(
        "EV-1",
        (
            "In this evaluation scenario, the message contains "
            f"the following observable indicator: "
            f"{scenario['indicator']} "
            "This observation alone does not establish that "
            "the destination is malicious."
        ),
        "relevant",
    )

    unrelated = passage(
        "EV-2",
        (
            "This document discusses password length, "
            "software updates, and device inventory. "
            "It provides no findings about the sender or "
            "destination in the investigated message."
        ),
        "irrelevant",
    )

    gap = passage(
        "EV-3",
        (
            "No independent investigation of the destination "
            "URL, sender identity, or organizational account "
            "records is available in this evidence set."
        ),
        "incomplete",
    )

    conflict_a = passage(
        "EV-4",
        (
            "Synthetic investigation record A states: "
            f"{scenario['benign']}"
        ),
        "conflict_a",
    )

    conflict_b = passage(
        "EV-5",
        (
            "Synthetic investigation record B disputes "
            "record A and states that the sender's "
            "authenticity has not been established."
        ),
        "conflict_b",
    )

    if condition == "clean":
        return [relevant]

    if condition == "noisy":
        return [unrelated, relevant]

    if condition == "incomplete":
        return [gap]

    if condition == "conflicting":
        return [relevant, conflict_a, conflict_b]

    raise ValueError(f"Unknown condition: {condition}")

def main():
    cases = []
    conditions = [
        "clean",
        "noisy",
        "incomplete",
        "conflicting",
    ]

    for condition in conditions:
        for index, scenario in enumerate(SCENARIOS, start=1):
            cases.append({
                "case_id": f"{condition[:3].upper()}-{index:02d}",
                "scenario": scenario["name"],
                "condition": condition,
                "message": scenario["message"],
                "evidence": build_evidence(scenario, condition),
                "expected_observation": scenario["indicator"],
                "unsupported_claim_probe": scenario["unsupported"],
                "ground_truth_note": (
                    "The message text is observable, but "
                    "external maliciousness or authenticity "
                    "must not be inferred without evidence."
                ),
            })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as file:
        json.dump(cases, file, indent=2, ensure_ascii=False)

    print(f"Created {len(cases)} evaluation cases")
    print(f"Saved to: {OUTPUT}")

    for condition in conditions:
        count = sum(
            case["condition"] == condition
            for case in cases
        )
        print(f"{condition}: {count}")

if __name__ == "__main__":
    main()
