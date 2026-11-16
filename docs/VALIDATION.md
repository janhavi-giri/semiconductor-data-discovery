# Validation receipt

Executed during preparation:

- Real source parsing: 1,567 samples, 590 observed measurement columns, 104 failures.
- Label mapping and sample join cardinality checked in the original PoC.
- Real ML baseline with chronological holdout and training-only preprocessing completed; `outputs/ml_result.json` records the result.
- Generated 100 payload assets with metadata sidecars; real and synthetic populations remain separate.
- Standard-library automated tests exercise filtered discovery, missing real context, linked test cardinality, checksum-verified consumption, rejected mixed cohorts, invalid selections and traversal boundaries.
- Local HTTP routes and browser script syntax checked before delivery.
- `verify.py` checks row counts, label mapping, join cardinality and target exclusion on the real data (see README, Rebuild and validate).
- `python poc.py train-from-handoff` trains from a checksum-verified discovery contract and matches the SQLite-path result (average precision 0.1697).
- A fresh clone starts without a manual unzip: `bootstrap.py` unpacks `data.zip`, covered by a unit test.

Not exercised by the author locally: Docker builds (the CI workflow builds the image and polls `/api/health`), live model inference, authentication/RBAC, enterprise storage, MES/FDC ingestion, production-scale latency, causal or yield effects. The GitHub Actions configuration is `.github/workflows/ci.yml`; remote CI success requires a run on GitHub.

The three-query filename/context comparison in `outputs/discovery_comparison.json` is an authored mechanism test. It is not an independently evaluated retrieval benchmark. Synthetic trace queries exercise generated metadata; they do not validate a physical process model.

Filename-only search is compared with metadata search in `ablations` on each search response. It separates metadata filters from keyword and synonym ranking, but it is still a mechanism demonstration on 100 generated assets, not a benchmark.
