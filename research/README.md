# Trace — Research Paper

**Trace: Claim-Level Evidence Verification in Retrieval-Augmented Phishing Assessments**
Fiyinfoluwa Osifala · Department of Computer Science, Southeastern Louisiana University
Independent Research · October 2026

📄 **Paper:** [Trace_IEEE_Style_October_2026.pdf](Trace_IEEE_Style_October_2026.pdf)
🔗 **DOI:** [10.5281/zenodo.24074579](https://doi.org/10.5281/zenodo.24074579) — permanent record on Zenodo

## What this study asks

Retrieval-augmented generation (RAG) can assess suspicious messages, but retrieving evidence does not guarantee that the generated explanation is actually supported by it. This study asks:

> *Does claim-level evidence verification improve the reliability of retrieval-augmented phishing assessments compared with the same system without verification?*

It evaluates reliability on two dimensions: phishing classification performance, and what happens to individual claims the verifier flags as insufficiently supported.

## Method in brief

- **Paired design:** every message was assessed twice — a baseline condition and a verified condition — sharing the same input, retrieved evidence, and initial assessment, so the verification stage is the only difference.
- **Dataset:** 200 messages (100 phishing / 100 legitimate) drawn from the Nazario phishing corpus, the SMS Phishing dataset, and the Phishing Validation dataset; 197 completed both conditions (98.5%).
- **System:** `openai/gpt-4.1-mini` via OpenRouter; five retrieved evidence passages per message; fixed random seed (42) for sampling.
- **Verifier:** each claim in the initial assessment was judged **Supported**, **Contradicted**, or **Insufficient**, and a revised assessment was generated from those judgments.
- **Statistics:** paired outcomes compared with McNemar's exact test.

## Key results

| Metric | Baseline | Verified |
|---|---|---|
| Accuracy | 69.04% | 70.56% |
| Precision | 97.80% | 98.91% |
| Recall | 90.82% | 92.86% |
| F1-score | 94.18% | 95.79% |
| Abstentions | 59 | 57 |

- The accuracy gain (+1.52 points) was **not statistically significant** (McNemar's exact test, p = 0.453); verification changed only 8 of 197 classification decisions.
- Of **654 claims** evaluated, the verifier flagged **64 (9.79%)** as having insufficient evidence; none were contradicted.
- An exploratory review of those 64 claims found **27 removed** and **14 qualified** in the final assessments — but **23 retained without adequate qualification**.

## The main takeaway

Detecting an evidence gap is not the same as enforcing it. The verifier reliably *found* insufficiently supported claims, but the final generator still let about a third of them through. That gap — between verification and enforcement — is the paper's central finding, and it points to the next research step: mechanisms that explicitly control whether a claim may appear in a final assessment based on its verification status, validated against independently annotated claims.

## Limitations (from the paper)

Single language model; 197-message evaluation, so results may not generalize; claim judgments produced by the system's own verifier and not yet independently validated; the review of flagged claims was exploratory; verification roughly tripled processing time (3.17s → 10.22s average).

## Relationship to this repository

The code in this repo is the Trace system evaluated in the paper: retrieval (hybrid BM25 + sentence-transformer search with reciprocal-rank fusion), cross-encoder reranking, assessment generation, and the claim-verification stage described above.

## Citation

```bibtex
@misc{osifala2026trace,
  author       = {Fiyinfoluwa Osifala},
  title        = {Trace: Claim-Level Evidence Verification in
                  Retrieval-Augmented Phishing Assessments},
  year         = {2026},
  month        = oct,
  note         = {Independent Research, Department of Computer Science,
                  Southeastern Louisiana University},
  doi          = {10.5281/zenodo.24074579},
  url          = {https://doi.org/10.5281/zenodo.24074579}
}
```
