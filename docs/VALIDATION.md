# Validation receipt

Executed during preparation:

- Real source parsing: 1,567 samples, 590 observed measurement columns, 104 failures.
- Label mapping and sample join cardinality checked in the original PoC.
- Real ML baseline with chronological holdout and training-only preprocessing completed; `outputs/ml_result.json` records the result.
- Generated 100 payload assets with metadata sidecars; real and synthetic populations remain separate.
- Standard-library automated tests exercise filtered discovery, missing real context, linked test cardinality, checksum-verified consumption, rejected mixed cohorts, invalid selections and traversal boundaries.
- Local HTTP routes and browser script syntax checked before delivery.

Not exercised: Docker builds, live model inference, authentication/RBAC, enterprise storage, MES/FDC ingestion, production-scale latency, causal or yield effects. GitHub Actions configuration is included; remote CI success requires a run on GitHub.

The three-query filename/context comparison in `outputs/discovery_comparison.json` is an authored mechanism test. It is not an independently evaluated retrieval benchmark. Synthetic trace queries exercise generated metadata; they do not validate a physical process model.
