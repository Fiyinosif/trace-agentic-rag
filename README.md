
# Trace — Evidence-Aware Phishing Assessment

Trace is an AI-powered application that analyzes suspicious messages using retrieval-augmented generation (RAG) and claim-level evidence verification.

The project explores a central research question:

**Can evidence verification reduce unsupported claims in AI-generated phishing assessments when retrieved evidence is incomplete, noisy, or conflicting?**

Trace is designed to assess suspicious emails, SMS messages, and other text-based communications while making the supporting evidence visible to users.

## Features

- **Suspicious message analysis:** Accepts user-submitted messages for phishing assessment.
- **Hybrid retrieval:** Combines BM25 keyword retrieval with sentence embeddings.
- **Cross-encoder reranking:** Reranks retrieved document chunks for relevance.
- **Evidence-based generation:** Uses retrieved evidence to inform the assessment.
- **Claim-level verification:** Evaluates whether generated claims are supported by available evidence.
- **Verification comparison:** Allows assessments to run with or without the verification stage.
- **Evidence transparency:** Returns retrieved sources and their relevance scores.
- **Web interface:** Provides a browser-based interface for interacting with the system.

## Architecture

The current application follows this pipeline:

```text
User submits a suspicious message
                |
                v
        FastAPI backend
                |
                v
        Evidence Collector
                |
                v
      Hybrid Retrieval
   (BM25 + Sentence Embeddings)
                |
                v
      Cross-Encoder Reranking
                |
                v
       Assessment Generator
                |
                v
    Optional Claim Verification
                |
                v
       Final Assessment
                |
                v
   Assessment + Supporting Evidence
```

### Hybrid retrieval

Trace combines lexical and semantic retrieval to identify relevant evidence from its knowledge base.

BM25 helps identify documents containing important keywords, while sentence embeddings help retrieve semantically related information.

### Evidence reranking

A cross-encoder reranker evaluates the relevance of retrieved candidates and selects the strongest evidence for assessment generation.

### Evidence verification

The verification stage checks generated claims against retrieved evidence.

The system can be run with verification enabled or disabled, allowing comparisons between the two approaches.

Verification is intended to reduce unsupported statements, but it does not guarantee factual correctness.

## Knowledge Base

The current knowledge base contains cybersecurity and phishing-related reference materials from:

- Federal Trade Commission (FTC)
- National Institute of Standards and Technology (NIST)

These materials provide reference evidence for suspicious-message assessments.

The knowledge base is stored in `data/knowledge_base/`.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript |
| Keyword retrieval | BM25 |
| Semantic retrieval | Sentence Transformers |
| Reranking | CrossEncoder |
| LLM integration | OpenRouter |
| API validation | Pydantic |
| Numerical processing | NumPy, scikit-learn |

## Project Structure

```text
agentic-rag-trust/
|
|-- data/
|   |-- knowledge_base/
|
|-- src/
|   |-- api.py
|   |-- assessment_generator.py
|   |-- document_loader.py
|   |-- evidence_collector.py
|   |-- evidence_verifier.py
|   |-- hybrid_retriever.py
|   |-- llm_provider.py
|   |-- message_analyzer.py
|   |-- reranker.py
|   |-- session_manager.py
|
|-- web/
|   |-- index.html
|
|-- tests/
|-- evaluate.py
|-- requirements.txt
|-- README.md
|-- .gitignore
```

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/Fiyinosif/trace-agentic-rag.git
cd trace-agentic-rag
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The first run may require downloading pretrained retrieval and reranking models.

### 4. Configure environment variables

Create a `.env` file in the project root.

Configure the OpenRouter API credentials and model used by the application:

```dotenv
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=nvidia/nemotron-3.5-lightning:free
```

Model availability and API limits depend on the provider.

Never commit your `.env` file or API keys.

### 5. Start the application

From the project root, run:

```bash
python -m uvicorn api:app --app-dir src --reload --port 8420
```

Open:

http://localhost:8420

## API Endpoints

### GET /health

Returns the service status and whether the evidence collector has initialized.

### POST /analyze

Analyzes a submitted message.

Example request:

```json
{
  "message": "Your account has been suspended. Click this link immediately to verify your information.",
  "use_verifier": true
}
```

The response includes:

- Generated assessment
- Retrieved evidence
- Evidence source information
- Reranker scores
- Verification setting
- Processing latency

## Research Direction

Trace investigates whether an explicit evidence-verification stage can reduce unsupported claims in AI-generated suspicious-message assessments.

The intended comparison holds the input message, retrieved evidence, and underlying language model consistent while changing whether claim-level verification is enabled.

The research considers different evidence conditions, including:

- Clean evidence
- Incomplete evidence
- Noisy evidence
- Conflicting evidence

### Current Research Status

Trace has undergone preliminary pilot testing of the verification pipeline.

Early observations indicate that the verifier can identify claims lacking sufficient evidence. However, preliminary tests have also revealed cases where unsupported claims persist in the final assessment despite verification.

These observations motivate further evaluation.

**The controlled research evaluation is ongoing.** No definitive improvement in factual reliability is claimed at this stage.

## Limitations

- Generated assessments can still contain unsupported claims.
- Retrieval quality depends on the coverage and relevance of the knowledge base.
- Verification does not guarantee that every unsupported claim will be removed.
- LLM provider availability, latency, and rate limits may affect responses.
- Trace is an experimental assessment tool, not a definitive phishing detection or cybersecurity decision system.

## Live Demo

A public deployment link will be added once hosting is configured.

## Author

**Fiyin Osifala**

Computer Science Undergraduate

GitHub: https://github.com/Fiyinosif

## Project Status

Active development — working application prototype with ongoing research evaluation.
