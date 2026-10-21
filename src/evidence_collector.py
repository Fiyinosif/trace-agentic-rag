
from dataclasses import dataclass, asdict
import random

from document_loader import load_and_chunk_documents
from hybrid_retriever import HybridRetriever
from reranker import Reranker, RETRIEVAL_CANDIDATES


@dataclass
class Evidence:
    evidence_id: str
    content: str
    source: str
    source_url: str
    organization: str
    authority: float
    reranker_score: float


class EvidenceCollector:

    def __init__(self):

        print("Initializing Evidence Collector...")

        self.chunks = load_and_chunk_documents()

        self.retriever = HybridRetriever(self.chunks)
        self.reranker = Reranker()

        print("Evidence Collector ready.")

    def collect(self, message, top_k=5):

        candidates = self.retriever.search(
            message,
            top_k=RETRIEVAL_CANDIDATES
        )

        results = self.reranker.rerank(
            message,
            candidates,
            top_k=top_k
        )

        evidence = []

        for index, result in enumerate(results, start=1):

            chunk = result["chunk"]

            evidence.append(
                Evidence(
                    evidence_id=f"KB-{index}",
                    content=chunk.text,
                    source=chunk.title,
                    source_url=chunk.source_url,
                    organization=chunk.organization,
                    authority=chunk.authority,
                    reranker_score=result["reranker_score"],
                )
            )

        return evidence

    def build_conditions(self, message, top_k=5, seed=42):
        """
        Construct controlled evidence conditions for research.

        These are experimental perturbations of the retrieved
        evidence, not claims about the true status of a message.
        """

        original = self.collect(message, top_k=top_k)

        if not original:
            raise ValueError(
                "No evidence retrieved for this message."
            )

        # Preserve the original evidence snapshot.
        clean = list(original)

        # INCOMPLETE: Withhold the highest-ranked passage.
        # This is a controlled removal, not a guarantee
        # that the remaining evidence is insufficient.
        incomplete = list(original[1:])

        # NOISY: Add an actual KB passage outside the
        # original top-k results.
        original_keys = {
            (item.source_url, item.content)
            for item in original
        }

        noise_candidates = [
            chunk
            for chunk in self.chunks
            if (chunk.source_url, chunk.text)
            not in original_keys
        ]

        rng = random.Random(seed)

        noisy = list(original)

        if noise_candidates:
            noise_chunk = rng.choice(noise_candidates)

            noisy.append(
                Evidence(
                    evidence_id="NOISE-1",
                    content=noise_chunk.text,
                    source=noise_chunk.title,
                    source_url=noise_chunk.source_url,
                    organization=noise_chunk.organization,
                    authority=noise_chunk.authority,
                    reranker_score=0.0,
                )
            )

        # CONFLICTING: Add an explicitly identified
        # experimental counterclaim.
        #
        # This is not attributed to a real organization
        # and must not be interpreted as verified evidence.
        conflicting = list(original)

        conflicting.append(
            Evidence(
                evidence_id="SIM-CONFLICT-1",
                content=(
                    "[CONTROLLED EXPERIMENTAL INJECTION — "
                    "NOT VERIFIED EXTERNAL EVIDENCE]\n"
                    "A simulated assessment asserts that "
                    "the message's suspicious indicators "
                    "are harmless and that the sender "
                    "is legitimate. This assertion has "
                    "not been independently verified."
                ),
                source="Controlled experimental injection",
                source_url="",
                organization="Research simulation",
                authority=0.0,
                reranker_score=0.0,
            )
        )

        return {
            "clean": clean,
            "noisy": noisy,
            "incomplete": incomplete,
            "conflicting": conflicting,
        }

    @staticmethod
    def serialize_evidence(evidence):
        return [
            asdict(item)
            for item in evidence
        ]


if __name__ == "__main__":

    collector = EvidenceCollector()

    message = """
    From: Microsoft IT Support
    support@micros0ft-security.com

    URGENT: Your Microsoft account will be
    suspended today.

    Verify your account immediately:
    https://microsoft-login.example.com

    Enter your username and password.
    """

    conditions = collector.build_conditions(message)

    for condition, evidence in conditions.items():

        print(f"\n========== {condition.upper()} ==========")
        print(f"Evidence items: {len(evidence)}")

        for item in evidence:
            print(
                f"{item.evidence_id}: "
                f"{item.source}"
            )
