
import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from assessment_generator import AssessmentGenerator
from evidence_collector import EvidenceCollector
from evidence_verifier import MODEL


DATASET = ROOT / "data" / "evaluation" / "evaluation_messages.csv"
OUTPUT_DIR = ROOT / "data" / "evaluation" / "results"

EXPERIMENT_VERSION = "v2"
VERIFICATION_METHOD = "batch_claim_verification"

RESULTS_FILE = OUTPUT_DIR / "experiment_results_v2.jsonl"
ERRORS_FILE = OUTPUT_DIR / "experiment_errors_v2.jsonl"

CONDITIONS = ("clean", "noisy", "incomplete", "conflicting")

# Temporary test limit. Set to None for the full experiment.
TEST_LIMIT = 2


def append_jsonl(path, record):
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
        file.flush()


def load_completed():
    completed = set()

    if not RESULTS_FILE.exists():
        return completed

    with RESULTS_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)

            if record.get("experiment_version") != EXPERIMENT_VERSION:
                raise ValueError(
                    "Results file contains a different experiment version."
                )

            completed.add(
                (record["message_id"], record["condition"])
            )

    return completed


def load_messages():
    if not DATASET.exists():
        raise FileNotFoundError(
            f"Evaluation dataset not found: {DATASET}"
        )

    with DATASET.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        messages = list(csv.DictReader(file))

    required = {
        "message_id",
        "source",
        "channel",
        "message_text",
        "normalized_label",
    }

    if not messages:
        raise ValueError("Evaluation dataset is empty.")

    missing = required - set(messages[0])

    if missing:
        raise ValueError(
            f"Missing dataset columns: {sorted(missing)}"
        )

    return messages


def format_message(row):
    parts = []

    sender = row.get("sender", "")
    subject = row.get("subject", "")
    body = row.get("message_text", "")

    if sender and sender.lower() != "nan":
        parts.append(f"From: {sender}")

    if subject and subject.lower() != "nan":
        parts.append(f"Subject: {subject}")

    parts.append(body)

    return "\n".join(parts)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    messages = load_messages()
    completed = load_completed()

    total_pairs = len(messages) * len(CONDITIONS)

    print(f"Experiment version: {EXPERIMENT_VERSION}")
    print(f"Verification method: {VERIFICATION_METHOD}")
    print(f"Loaded {len(messages)} messages.")
    print(f"Completed V2 pairs: {len(completed)}")
    print(f"Remaining pairs: {total_pairs - len(completed)}")
    print(f"Total planned pairs: {total_pairs}")

    if TEST_LIMIT is not None and len(completed) >= TEST_LIMIT:
        print("\nTest limit already reached.")
        return

    collector = EvidenceCollector()
    generator = AssessmentGenerator()

    for message_number, row in enumerate(messages, start=1):
        message_id = row["message_id"]
        message = format_message(row)

        pending = [
            condition
            for condition in CONDITIONS
            if (message_id, condition) not in completed
        ]

        if not pending:
            continue

        print(
            f"\nMessage {message_number}/{len(messages)} "
            f"({message_id})"
        )

        try:
            evidence_conditions = collector.build_conditions(
                message,
                top_k=5,
                seed=42,
            )

        except Exception as exc:
            append_jsonl(
                ERRORS_FILE,
                {
                    "experiment_version": EXPERIMENT_VERSION,
                    "message_id": message_id,
                    "stage": "evidence_collection",
                    "error": str(exc),
                },
            )

            print(f"Evidence collection failed: {exc}")
            continue

        for condition in pending:
            evidence = evidence_conditions[condition]

            if not evidence:
                print(f"Skipping empty condition: {condition}")
                continue

            print(f"  Running: {condition}")

            start = time.perf_counter()

            try:
                # Generate one shared draft for the paired comparison.
                draft = generator.generate_draft(
                    message,
                    evidence,
                )

                # Batch-verify the claims and revise the same draft.
                verified = generator.verify_draft(
                    message,
                    evidence,
                    draft,
                )

                elapsed = time.perf_counter() - start

                record = {
                    "experiment_version": EXPERIMENT_VERSION,
                    "verification_method": VERIFICATION_METHOD,
                    "message_id": message_id,
                    "source": row["source"],
                    "channel": row["channel"],
                    "original_label": row.get("original_label"),
                    "normalized_label": row["normalized_label"],
                    "condition": condition,
                    "model": MODEL,
                    "message": message,
                    "evidence": collector.serialize_evidence(
                        evidence
                    ),
                    "baseline_assessment": draft,
                    "verified_assessment": verified[
                        "final_assessment"
                    ],
                    "claims": verified["claims"],
                    "verification_results": verified[
                        "verification_results"
                    ],
                    "elapsed_seconds": round(elapsed, 2),
                }

                append_jsonl(RESULTS_FILE, record)
                completed.add((message_id, condition))

                print(
                    f"  Saved pair "
                    f"({elapsed:.1f} seconds)"
                )

                if (
                    TEST_LIMIT is not None
                    and len(completed) >= TEST_LIMIT
                ):
                    print(
                        "\nTest limit reached. "
                        "Stopping successfully."
                    )
                    print(f"Saved V2 pairs: {len(completed)}")
                    print(f"Results: {RESULTS_FILE}")
                    return

            except Exception as exc:
                append_jsonl(
                    ERRORS_FILE,
                    {
                        "experiment_version": EXPERIMENT_VERSION,
                        "message_id": message_id,
                        "condition": condition,
                        "stage": "assessment",
                        "error": str(exc),
                    },
                )

                print(f"  Failed: {exc}")

                if "429" in str(exc):
                    print(
                        "\nOpenRouter rate limit reached. "
                        "Stopping the experiment."
                    )
                    print(f"Completed V2 pairs: {len(completed)}")
                    print(f"Results saved to: {RESULTS_FILE}")
                    return

    print("\nExperiment run finished.")
    print(f"Saved V2 pairs: {len(completed)}")
    print(f"Results: {RESULTS_FILE}")
    print(f"Errors: {ERRORS_FILE}")


if __name__ == "__main__":
    main()
