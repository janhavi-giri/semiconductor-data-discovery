# Architecture and contracts

| Component | Reads | Produces | Boundary |
|---|---|---|---|
| Real-data builder | Unchanged UCI source ZIP | Normalized SQLite, provenance, profiles | Preserves row alignment and unknown physical meanings |
| Demo file builder | Normalized SQLite + deterministic generator | CSV payloads + sidecars + catalog | Never assigns synthetic fab IDs to real SECOM observations |
| Vocabulary | Curated ontology.json | Terms, synonyms and relationship descriptions | Human authored; no claim of automatic certification |
| Discovery | Catalog + known filters | Ranked asset references + match evidence | Lexical/synonym matching; limited explicit filter parsing |
| Inspector | Asset manifest + source file | Preview, checksum verification, related assets | Source paths come from the known catalog |
| Handoff | Explicit in-scope selection | JSON application contract | Checksums checked before export |
| Consumer | Contract + local source files | Verified load summary | Rejects path traversal and mixed real/synthetic populations |

Metadata is stored alongside data as JSON sidecars and a searchable manifest. Rebuilding `data/catalog.json` is the only refresh mechanism in this PoC. There is no live file watcher, distributed index, policy engine or access-control service.

Synthetic trace and test files have a one-to-one relation through the metadata wafer ID. Trace payload rows are time points; test rows are wafer-level. Never directly join trace time points to labels and interpret those rows as independent wafers. SECOM sample IDs represent source-row alignment, not wafer identity. Feature profiles join by feature ID and do not share sample grain.

## API

All routes are read-only GET requests; server listens on loopback by default.

| Route | Result |
|---|---|
| `/api/health` | Readiness, engine and asset count |
| `/api/catalog` | Registered asset metadata |
| `/api/search?q=...` | Filename baseline, contextual results, explanations, warnings |
| `/api/asset?id=...` | Verified source preview + metadata + linked assets |
| `/api/handoff?q=...&id=...` | Selected assets' consumer contract |
| `/api/ontology` | Curated terms and relationship definitions |
| `/api/results` | Included original run receipts |

Search filters: source, process_step, chamber_id, test_outcome, role, lot_id, max_missing. The UI exposes the first five. Explicit filters override inferred filters. Use the inspector's match explanation to verify effective context. Inferred filters support known etch/deposition terms, C1/C2, explicit fail terms and sensor/trace roles. This is not arbitrary natural-language interpretation. Causal vocabulary produces a warning, not a diagnosis.

Missingness in the synthetic trace sidecar is null cells divided by all numeric cells (60 rows × 3 columns), including elapsed time. Real asset-level missingness is unknown here; channel-level profiles are available separately. ML feature selection recomputes on training rows.
