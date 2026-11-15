# Fab Context — Semiconductor Data Discovery

**A runnable demonstration of how manufacturing metadata makes files discoverable and usable by downstream AI/ML applications.**

Ask: **“Find etch sensor traces for failed wafers in chamber C2.”** Compare filename-only search with contextual discovery, inspect linked test outcomes and provenance, then export a machine-readable handoff for a consuming application.

> Uses public SECOM data and a labeled synthetic fab scenario.

Repository publishing instructions: [docs/PUBLISH.md](docs/PUBLISH.md). The clone URL below is the intended remote name; if using the supplied ZIP, extract it and start from `python server.py`.

## Demo video

The 40-second Fab Context walkthrough [Fab_Context_Demo.mp4) shows how to find etch traces for wafers processed in chamber C2 that later failed test. On the same synthetic files, filename search returns zero matches, while a search using manufacturing metadata finds five traces and shows how a trace links to its test result. A second example uses public SECOM data to show how the tool flags missing chamber IDs.

## Start the visual demo

Python 3.10+ is enough to run the included visual demo. **No install, API key or network connection is required after cloning.**

```bash
git clone https://github.com/janhavi-giri/semiconductor-data-discovery.git
cd semiconductor-data-discovery
python server.py
```

Open **http://127.0.0.1:8501**. Windows users may use `py server.py`.

Alternative, with Docker:

```bash
docker compose up --build
```

The Docker path is supplied but was not executed during preparation. The Python server and HTTP APIs were tested.

## What the demo would show

| Demo moment | What the audience sees | Why it matters |
|---|---|---|
| Discover data | Filename-only search versus contextual results | Meaning makes opaque files findable |
| Inspect context | Purpose, units, grain, source, wafer/lot/chamber and recipe (synthetic) | Context makes selection explainable |
| Follow relationships | Trace → synthetic wafer → quality-test file | Relationships connect isolated data |
| Check limits | Real SECOM returns no chamber-specific match | Missing identities remain unknown |
| Export handoff | Paths, checksums, roles, join keys and limitations | Applications receive an explicit data contract |
| Consume selection | Verify checksums and load selected files | Discovery connects to an actual downstream operation |

## Two honest data populations

| Population | Contents | Known context | Unknown / limits |
|---|---|---|---|
| **Real SECOM** | 1,567 samples, 590 observed measurement columns, 104 failures | Source timestamps, outcomes, profiles, generated sample IDs | Physical sensor names, units, wafer/lot/tool/chamber/recipe and process steps |
| **Synthetic fab scenario** | 48 wafer examples; 48 trace CSVs and 48 test CSVs | Illustrative lot, wafer, tool, chamber, step, recipe, units and outcome links | Every identity, signal and outcome is generated; no causal/physical validity claimed |

Four real-data CSV exports plus 96 synthetic files give **100 discoverable assets**. Each has a JSON sidecar in `data/metadata/`; the searchable manifest is `data/catalog.json`. Raw payloads remain separate from metadata. The synthetic trace's wafer identity is in the sidecar, not repeated in every time-point row.

The UCI prose reports 591 features; the actual source measurement matrix contains 590. This is recorded in the provenance receipt rather than silently filling a column. Sample failure fraction is not die yield.

## How it works

1. **Register:** assign an asset ID and locate the original CSV or source database.
2. **Describe:** attach purpose, provenance, row grain, role, quality and limitations.
3. **Connect:** record evidence-backed relationships and a controlled vocabulary.
4. **Discover:** rank contextual matches, apply structured filters and explain matches.
5. **Handoff:** export selected file pointers, SHA-256 checksums, relationships and consumer rules.
6. **Consume:** verify the contract and load only selected data.

The visual demo uses **deterministic keyword and curated ontology-synonym matching**, with explicit extraction of a small set of known filters. The filename baseline does not have metadata filters; comparisons illustrate the mechanism, not an unbiased retrieval benchmark. Known supported questions are in the walkthrough; arbitrary natural-language understanding is not claimed.

## Downstream application example

In the UI, select a trace and choose **Export agent handoff**, then download `discovery-handoff.json`. Save it beside the scripts and run:

```bash
python consume_handoff.py discovery-handoff.json
```

The consumer verifies checksums, rejects paths outside the repository, refuses mixed real/synthetic cohorts and loads selected CSVs. Target files remain explicitly labeled; a model builder must enforce feature/target separation. The consumer is not an autonomous training agent.

A ready-made example is also included:

```bash
python consume_handoff.py examples/synthetic-trace-handoff.json
```

For the separate **real SECOM ML baseline** (requires the optional dependencies):

```bash
pip install -r requirements.txt
python poc.py train
```

This baseline resolves its feature asset through the original local catalog, joins normalized samples and labels, excludes outcomes and IDs from inputs, then performs a time-based holdout. It does not train from the exported file-selection contract. Included run: 1,253 train / 314 test samples, 444 predictors, average precision 0.170 versus test prevalence 0.054; one historical split, not a production result.

## Rebuild and validate

Included data permits an offline customer demo. To reproduce all data:

```bash
pip install -r requirements.txt
python poc.py build       # normalizes real source ZIP; downloads only if absent
python poc.py demo        # original three-query smoke comparison
python poc.py train       # refreshes real-data ML results
python build_demo.py      # generates public exports, synthetic files and metadata
python -m unittest discover -s tests -v
```

For the existing assets, tests need only Python's standard library. GitHub Actions runs them on push/PR. They check provenance separation, explicit filters, unknown context, linked test cardinality, handoff consumption and invalid selections/paths. [docs/VALIDATION.md](docs/VALIDATION.md) records what was actually exercised.
# Architecture

See [Fab_Context_Architecture.md](docs/Fab_Context_Architecture.md) for the data flow diagram, datasets, Python search logic, API outputs, and how downstream tools verify and load the selected files.

## Repository map

| Path | Purpose |
|---|---|
| `server.py`, `web/index.html` | Local demo UI and read-only APIs |
| `discovery.py`, `ontology.json` | Metadata discovery, explanations and relationships |
| `build_demo.py` | Reproducible file/sidecar generation |
| `consume_handoff.py`, `examples/` | Downstream contract consumer and example |
| `poc.py` | Real-data normalization and ML baseline |
| `data/raw/`, `data/real/`, `data/synthetic/` | Public original data and clearly separated derived/demo payloads |
| `data/metadata/`, `data/catalog.json` | Context sidecars and discoverable asset manifest |
| `outputs/` | Original provenance, discovery and ML receipts |
| `docs/` | Customer walkthrough, architecture, integration and validation |
| `tests/`, `.github/workflows/` | Automated checks |
| `Dockerfile`, `compose.yaml` | Optional container startup |

## Discussion for a manufacturing pilot

Start with a small trace + metrology/test cohort. Agree on authoritative identities and joins across MES, FDC and quality systems. Attach unit, recipe revision, grain, lineage, access policy and freshness. Use the same query set and retrieval engine before/after enrichment to measure discovery success, correct cohort construction, unsupported-question handling and engineer time-to-data. Any ROI or manufacturing outcome needs that customer-specific measurement.

This demo is local and unauthenticated; keep the server bound to loopback. It implements no enterprise authorization, live MES/FDC connector, storage-vendor integration, file watcher, governed catalog publication or causal diagnosis.

## Attribution

SECOM: Michael McCann and Adrian Johnston (2008), [UCI Machine Learning Repository](https://doi.org/10.24432/C54305), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Original ZIP is unchanged; CSV exports, normalization and profiles are derived transformations. Original PoC code and synthetic data: MIT, see [LICENSE](LICENSE).
