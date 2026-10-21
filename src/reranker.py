from sentence_transformers import CrossEncoder

from document_loader import load_and_chunk_documents
from hybrid_retriever import HybridRetriever


RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"

RETRIEVAL_CANDIDATES = 10
FINAL_TOP_K = 5


class Reranker:

    def __init__(self):

        print("Loading reranker model...")

        self.model = CrossEncoder(
            RERANKER_MODEL
        )

        print("Reranker ready.")


    def rerank(
        self,
        query,
        candidates,
        top_k=FINAL_TOP_K
    ):

        if not candidates:
            return []

        pairs = []

        for candidate in candidates:

            chunk = candidate["chunk"]

            pairs.append(
                [query, chunk.text]
            )

        scores = self.model.predict(pairs)

        reranked_results = []

        for candidate, score in zip(
            candidates,
            scores
        ):
            reranked_results.append(
                {
                    "chunk": candidate["chunk"],
                    "rrf_score": candidate["rrf_score"],
                    "reranker_score": float(score),
                }
            )

        reranked_results.sort(
            key=lambda result: result["reranker_score"],
            reverse=True,
        )

        return reranked_results[:top_k]


if __name__ == "__main__":

    chunks = load_and_chunk_documents()

    print(
        f"Loaded {len(chunks)} chunks"
    )

    retriever = HybridRetriever(chunks)

    reranker = Reranker()

    query = (
        "Someone sent me an email pretending "
        "to be my boss and asking me to send money."
    )

    print(f"\nQuery:\n{query}")

    candidates = retriever.search(
        query,
        top_k=RETRIEVAL_CANDIDATES
    )

    print(
        f"\nRetrieved "
        f"{len(candidates)} candidates"
    )

    results = reranker.rerank(
        query,
        candidates,
        top_k=FINAL_TOP_K
    )

    print("\nReranked Results:")

    for rank, result in enumerate(
        results,
        start=1
    ):

        chunk = result["chunk"]

        print("\n" + "=" * 60)

        print(f"Rank: {rank}")

        print(
            f"RRF Score: "
            f"{result['rrf_score']:.6f}"
        )

        print(
            f"Reranker Score: "
            f"{result['reranker_score']:.6f}"
        )

        print(
            f"Organization: "
            f"{chunk.organization}"
        )

        print(
            f"Topic: "
            f"{chunk.topic}"
        )

        print(
            f"Title: "
            f"{chunk.title}"
        )

        print(
            f"Source: "
            f"{chunk.source_url}"
        )

        print("\nText:")

        print(
            chunk.text[:700]
        )