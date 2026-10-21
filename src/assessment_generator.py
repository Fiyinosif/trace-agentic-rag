
import json
from dataclasses import asdict
from urllib.request import Request, urlopen

from evidence_collector import EvidenceCollector
from evidence_verifier import EvidenceVerifier, MODEL


class AssessmentGenerator:

    def __init__(self):
        self.verifier = EvidenceVerifier()

    def ask_llm(self, prompt):
        payload = {
            "model": MODEL,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a cybersecurity assessment assistant. "
                        "Use only the supplied message and evidence. "
                        "Distinguish suspicious indicators from confirmed "
                        "malicious activity. Do not invent facts."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

        request = Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.verifier.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urlopen(request, timeout=180) as response:
            data = json.load(response)

        return data["choices"][0]["message"]["content"]

    def generate_draft(self, message, evidence):
        evidence_text = "\n\n".join(
            f"[{item.evidence_id}] {item.content}"
            for item in evidence
        )

        prompt = f"""
Assess this suspicious message:

{message}

Available evidence:
{evidence_text}

Return:
1. Risk assessment (high/medium/low/inconclusive)
2. Three or fewer factual claims explaining the assessment,
   numbered as separate lines under CLAIMS
3. Supporting evidence IDs for each claim, if available
4. Missing information
5. Recommended safe action

Do not claim a domain is confirmed malicious without proof.
"""

        return self.ask_llm(prompt)

    def verify_draft(self, message, evidence, draft):
        extraction = self.ask_llm(
            "Extract the factual assessment claims from the "
            "following draft. Return only a JSON array of strings. "
            "Do not include recommendations.\n\n" + draft
        )

        extraction = extraction.strip()

        if extraction.startswith("```"):
            extraction = extraction.split("\n", 1)[1]
            extraction = extraction.rsplit("```", 1)[0].strip()

        claims = json.loads(extraction)

        if not isinstance(claims, list) or not all(
            isinstance(claim, str) for claim in claims
        ):
            raise ValueError("Expected a JSON array of claims")

        # Verify all claims in ONE API request.
        verification_results = self.verifier.verify_batch(
            claims,
            evidence,
            message=message
        )

        feedback = "\n".join(
            f"Claim: {result.claim}\n"
            f"Verdict: {result.verdict}\n"
            f"Evidence IDs: {result.evidence_ids}\n"
            f"Explanation: {result.explanation}\n"
            for result in verification_results
        )

        final_assessment = self.ask_llm(
            f"""
You are producing the FINAL user-facing phishing assessment.

ORIGINAL MESSAGE:
{message}

RETRIEVED EVIDENCE:
{chr(10).join(
    f"[{item.evidence_id}] {item.content}"
    for item in evidence
)}

ORIGINAL DRAFT:
{draft}

VERIFICATION RESULTS:
{feedback}

Rules:
1. Use supported claims as evidence-backed explanations.
2. Remove claims marked contradicted.
3. Do not repeat insufficient claims as established facts.
4. If an insufficient claim describes something directly
   observable in the original message, you may describe
   that observation without claiming external verification.
5. Do not confuse lack of domain verification with low risk.
6. Assess risk using the message indicators and supported
   evidence, while clearly acknowledging uncertainty.
7. Do not display internal verifier verdicts or explanations.
8. Do not invent new evidence or source citations.
9. Cite only evidence IDs present in the retrieved evidence.

Return only:
Risk: HIGH / MEDIUM / LOW / INCONCLUSIVE

Key indicators:
- ...

Supporting evidence:
- ...

Missing evidence:
- ...

Recommended safe action:
- ...
"""
        )

        return {
            "draft": draft,
            "final_assessment": final_assessment,
            "claims": claims,
            "verification_results": [
                asdict(result)
                for result in verification_results
            ],
        }

    def generate(
        self,
        message,
        evidence,
        use_verifier=False,
        return_details=False,
        draft=None
    ):
        if draft is None:
            draft = self.generate_draft(message, evidence)

        if not use_verifier:
            if return_details:
                return {
                    "draft": draft,
                    "final_assessment": draft,
                    "claims": [],
                    "verification_results": [],
                }

            return draft

        result = self.verify_draft(
            message,
            evidence,
            draft
        )

        if return_details:
            return result

        return result["final_assessment"]


if __name__ == "__main__":

    collector = EvidenceCollector()
    generator = AssessmentGenerator()

    message = """
    Microsoft IT Support says my account will be
    suspended today. Enter your username and password at:
    https://microsoft-login.example.com
    """

    evidence = collector.collect(message)

    # Generate the draft ONCE for both configurations.
    shared_draft = generator.generate_draft(
        message,
        evidence
    )

    print("\n========== WITHOUT VERIFIER ==========")

    baseline = generator.generate(
        message,
        evidence,
        use_verifier=False,
        draft=shared_draft
    )

    print(baseline)

    print("\n========== WITH VERIFIER ==========")

    verified = generator.generate(
        message,
        evidence,
        use_verifier=True,
        return_details=True,
        draft=shared_draft
    )

    print(verified["final_assessment"])

    print("\n========== VERIFICATION DETAILS ==========")

    print(
        json.dumps(
            verified["verification_results"],
            indent=2
        )
    )
