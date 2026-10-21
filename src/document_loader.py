from dataclasses import dataclass
from pathlib import Path
import json
import re


KNOWLEDGE_BASE = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


@dataclass
class DocumentChunk:
    text: str
    source_file: str
    source_url: str
    title: str
    organization: str
    topic: str
    authority: float
    chunk_id: int


def clean_text(text):

    boilerplate_phrases = [
        "Skip to main content",
        "The .gov means it’s official.",
        "Federal government websites often end in .gov or .mil.",
        "Before sharing sensitive information, make sure you’re on a federalgovernment site.",
        "The site is secure.",
        "The https:// ensures that you are connecting to the official website and that any information you provide is encryptedand transmitted securely.",
        "Español",
        "Report Fraud",
        "Submit Public Comments",
        "Search the Legal Library",
        "Vea esta página en español",
    ]

    for phrase in boilerplate_phrases:
        text = text.replace(phrase, " ")

    # Remove HTML anchors if any remain
    text = re.sub(r"<a[^>]*></a>", "", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def load_documents():
    documents = []

    for text_path in KNOWLEDGE_BASE.glob("*.txt"):

        metadata_path = text_path.with_suffix(".json")

        if not metadata_path.exists():
            print(
                f"Skipping {text_path.name}: "
                f"metadata file not found."
            )
            continue

        text = text_path.read_text(
            encoding="utf-8"
        )

        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        text = clean_text(text)

        documents.append(
            {
                "text": text,
                "source_file": text_path.name,
                "source_url": metadata["source_url"],
                "title": metadata["title"],
                "organization": metadata["organization"],
                "topic": metadata["topic"],
                "authority": metadata["authority"],
            }
        )

    return documents


def chunk_text(text):
    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + CHUNK_SIZE

        chunk_words = words[start:end]

        chunk = " ".join(chunk_words)

        chunks.append(chunk)

        # Stop if this was the final chunk.
        if end >= len(words):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def create_chunks(documents):
    all_chunks = []

    for document in documents:

        chunks = chunk_text(
            document["text"]
        )

        for chunk_id, chunk in enumerate(chunks):

            document_chunk = DocumentChunk(
                text=chunk,
                source_file=document["source_file"],
                source_url=document["source_url"],
                title=document["title"],
                organization=document["organization"],
                topic=document["topic"],
                authority=document["authority"],
                chunk_id=chunk_id,
            )

            all_chunks.append(document_chunk)

    return all_chunks


def load_and_chunk_documents():
    documents = load_documents()

    chunks = create_chunks(documents)

    return chunks


if __name__ == "__main__":

    documents = load_documents()

    print(
        f"Loaded {len(documents)} documents"
    )

    chunks = create_chunks(documents)

    print(
        f"Created {len(chunks)} chunks"
    )

    if chunks:

        first_chunk = chunks[0]

        print("\nFirst chunk:")
        print("--------------------")
        print(first_chunk.text[:1000])
        print("--------------------")

        print("\nMetadata:")
        print(
            f"Source file: {first_chunk.source_file}"
        )
        print(
            f"Source URL: {first_chunk.source_url}"
        )
        print(
            f"Title: {first_chunk.title}"
        )
        print(
            f"Organization: {first_chunk.organization}"
        )
        print(
            f"Topic: {first_chunk.topic}"
        )
        print(
            f"Authority: {first_chunk.authority}"
        )
        print(
            f"Chunk ID: {first_chunk.chunk_id}"
        )