
import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from evidence_collector import EvidenceCollector
from assessment_generator import AssessmentGenerator

BASE_DIR = Path(__file__).resolve().parent.parent

collector = None
generator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global collector, generator

    collector = await asyncio.to_thread(EvidenceCollector)
    generator = AssessmentGenerator()

    yield

    collector = None
    generator = None


app = FastAPI(
    title="Trace - Evidence-Aware Phishing Assessment",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    message: str = Field(min_length=1)
    use_verifier: bool = True


class EvidenceResponse(BaseModel):
    evidence_id: str
    source: str
    source_url: str
    organization: str
    content: str
    reranker_score: float


class AnalyzeResponse(BaseModel):
    assessment: str
    evidence: list[EvidenceResponse]
    verification_enabled: bool
    latency_ms: int


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "Trace",
        "evidence_collector_ready": collector is not None,
    }


def run_analysis(message: str, use_verifier: bool):
    evidence = collector.collect(message)

    assessment = generator.generate(
        message,
        evidence,
        use_verifier=use_verifier,
    )

    return assessment, evidence


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    if collector is None or generator is None:
        raise HTTPException(
            status_code=503,
            detail="Trace is still initializing",
        )

    start = time.perf_counter()

    try:
        # Run blocking retrieval and API calls outside
        # FastAPI's event loop.
        assessment, evidence = await asyncio.to_thread(
            run_analysis,
            req.message,
            req.use_verifier,
        )
    except Exception as exc:
        print(f"Analysis failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Analysis failed. Check server logs.",
        ) from exc

    return AnalyzeResponse(
        assessment=assessment,
        evidence=[
            EvidenceResponse(
                evidence_id=item.evidence_id,
                source=item.source,
                source_url=item.source_url,
                organization=item.organization,
                content=item.content,
                reranker_score=item.reranker_score,
            )
            for item in evidence
        ],
        verification_enabled=req.use_verifier,
        latency_ms=int(
            (time.perf_counter() - start) * 1000
        ),
    )


# Keep this last so API routes take priority.
static_dir = BASE_DIR / "web"

if static_dir.exists():
    app.mount(
        "/",
        StaticFiles(
            directory=str(static_dir),
            html=True,
        ),
        name="web",
    )
