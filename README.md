
## Demo and Current Status

Trace is a working prototype of an evidence-aware phishing assessment system.

### Application

The application accepts suspicious text messages, emails, and other communications and generates an evidence-informed risk assessment.

Users can enable or disable claim-level evidence verification to explore how the verification stage affects the generated assessment.

### Implementation Status

| Component | Status |
|---|---|
| FastAPI backend | Implemented and tested |
| Web interface | Implemented and tested |
| BM25 keyword retrieval | Implemented |
| Sentence embedding retrieval | Implemented |
| Hybrid retrieval | Working |
| Cross-encoder reranking | Working |
| Evidence collection | Working |
| Baseline assessment generation | Working |
| Claim-level verification | Working locally |
| Public demo | Temporarily available via Cloudflare Tunnel |
| Permanent deployment | In progress |
| Controlled research evaluation | Ongoing |

### Preliminary Performance Observations

A local test using a synthetic bank-account phishing message produced the following results:

| Configuration | Result | Processing Time |
|---|---|---|
| Baseline (without verification) | Completed | 43.03 seconds |
| Verification enabled | Completed | 160.35 seconds |

Both configurations identified the message as high risk.

These are individual demonstration runs, not benchmark averages or evidence of improved detection accuracy.

### Deployment Limitations

Trace currently runs locally using FastAPI and can be exposed through a temporary Cloudflare Tunnel.

The baseline assessment has been successfully tested through the public tunnel.

Verification-enabled assessments have completed locally but may fail through the public tunnel because of long-running requests or connection limitations.

The application also requires sufficient memory to load its sentence embedding and cross-encoder models.

A permanent deployment is planned.

### Research Status

The research component investigates whether claim-level verification reduces unsupported statements under incomplete, noisy, and conflicting evidence conditions.

Preliminary pilot testing has identified both useful verification behavior and cases where unsupported claims remain in the final output.

Further controlled evaluation is required before drawing conclusions about effectiveness.
