import re
import numpy as np

from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from document_loader import (
    DocumentChunk,
    load_and_chunk_documents,
)


EMBEDDING_MODEL = "all-MiniLM-L6-v2"

BM25_TOP_K = 10
SEMANTIC_TOP_K = 10

RRF_K = 60


class HybridRetriever:

    def __init__(self, chunks):
        self.chunks = chunks

        print("Building BM25 index...")

        self.tokenized_chunks = [
            self._tokenize(chunk.text)
            for chunk in chunks
        ]

        self.bm25 = BM25Okapi(
            self.tokenized_chunks
        )

        print("Loading embedding model...")

        self.embedding_model = SentenceTransformer(
            EMBEDDING_MODEL
        )

        print("Creating chunk embeddings...")

        chunk_texts = [
            chunk.text
            for chunk in chunks
        ]

        self.chunk_embeddings = (
            self.embedding_model.encode(
                chunk_texts,
                normalize_embeddings=True,
                show_progress_bar=True,
            )
        )

        print("Hybrid retriever ready.")


    def _tokenize(self, text):
        return re.findall(
            r"\b\w+\b",
            text.lower()
        )


    def bm25_search(self, query, top_k=BM25_TOP_K):

        query_tokens = self._tokenize(query)

        scores = self.bm25.get_scores(
            query_tokens
        )

        ranked_indices = np.argsort(scores)[::-1]

        results = []

        for index in ranked_indices[:top_k]:

            results.append(
                {
                    "index": int(index),
                    "score": float(scores[index]),
                }
            )

        return results


    def semantic_search(
        self,
        query,
        top_k=SEMANTIC_TOP_K
    ):

        query_embedding = (
            self.embedding_model.encode(
                query,
                normalize_embeddings=True,
            )
        )

        # Because the vectors are normalized,
        # dot product gives cosine similarity.
        scores = np.dot(
            self.chunk_embeddings,
            query_embedding
        )

        ranked_indices = np.argsort(scores)[::-1]

        results = []

        for index in ranked_indices[:top_k]:

            results.append(
                {
                    "index": int(index),
                    "score": float(scores[index]),
                }
            )

        return results


    def reciprocal_rank_fusion(
        self,
        bm25_results,
        semantic_results
    ):

        rrf_scores = {}

        for rank, result in enumerate(
            bm25_results,
            start=1
        ):
            index = result["index"]

            rrf_scores[index] = (
                rrf_scores.get(index, 0)
                + 1 / (RRF_K + rank)
            )

        for rank, result in enumerate(
            semantic_results,
            start=1
        ):
            index = result["index"]

            rrf_scores[index] = (
                rrf_scores.get(index, 0)
                + 1 / (RRF_K + rank)
            )

        ranked_results = sorted(
            rrf_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        return ranked_results


    def search(self, query, top_k=5):

        bm25_results = self.bm25_search(query)

        semantic_results = self.semantic_search(
            query
        )

        fused_results = (
            self.reciprocal_rank_fusion(
                bm25_results,
                semantic_results,
            )
        )

        results = []

        for index, rrf_score in fused_results[:top_k]:

            chunk = self.chunks[index]

            results.append(
                {
                    "chunk": chunk,
                    "rrf_score": rrf_score,
                }
            )

        return results


if __name__ == "__main__":

    chunks = load_and_chunk_documents()

    print(
        f"Loaded {len(chunks)} chunks"
    )

    retriever = HybridRetriever(chunks)

    query = (
        "Someone sent me an email pretending "
        "to be my boss and asking me to send money."
    )

    print(f"\nQuery:\n{query}")

    results = retriever.search(
        query,
        top_k=5
    )

    print("\nHybrid Results:")

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
            f"Organization: "
            f"{chunk.organization}"
        )
        print(
            f"Topic: {chunk.topic}"
        )
        print(
            f"Title: {chunk.title}"
        )
        print(
            f"Source: {chunk.source_url}"
        )

        print("\nText:")
        print(chunk.text[:700])