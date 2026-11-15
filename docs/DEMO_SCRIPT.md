# Customer demo: contextual manufacturing data discovery

Audience: manufacturing data, MES, FDC, AI/ML and data-platform teams. Duration: 8–10 minutes.

## Opening (30 seconds)

“An engineer knows what data they need: traces from a particular process, cohort and outcome. The files may exist, but filenames alone do not carry that meaning. This demo shows how metadata turns files into discoverable, connected inputs for AI applications.”

State up front: public SECOM plus a synthetic fab scenario, no customer data. The UI runs locally without an LLM.

## 1. The engineering question (2 minutes)

Open Discover data. Click **Failed-wafer etch traces**. The query asks for etch sensor traces for failed wafers in chamber C2. The source is explicitly synthetic.

Point to filename results: no matches. Compare context results: step, chamber, feature role and outcome match. Explain that the same unchanged trace files are found through their sidecars. The catalog was designed to illustrate this mechanism, so the result is not a general search benchmark.

Inspect `TRACE-DEMO-W001`. Show the source pointer, grain, recipe revision, synthetic wafer and lot IDs, units, checksum and linked test. The trace has 60 time-point rows. Its wafer identity lives in the sidecar; the test carries that same synthetic wafer ID. Association is not causation.

## 2. Real data and honest unknowns (2 minutes)

Click **Real quality measurements**. Inspect the real SECOM measurement export. It has 1,567 sample rows and generated source-alignment IDs. Sensor meanings and units remain unknown.

Click **Chamber context missing**. The source is real SECOM, but the question requires etch/chamber identities it does not contain. No assets match. Explain why a useful metadata layer must preserve missing context instead of manufacturing a plausible identity.

Click **Chronological validation** to show discovery of the timestamp asset by intended downstream purpose.

## 3. Application handoff (2 minutes)

Return to **Failed-wafer etch traces**, select one trace and export. In ML handoff, inspect:

- Source path + checksum: locate and verify the payload.
- Role + grain: know how to use the file.
- Join key + related asset: discover its outcome data.
- Provenance + synthetic flag: define the population honestly.
- Consumer rules: avoid mixing populations and exclude outcomes from predictors.

Download the JSON. Run `python consume_handoff.py discovery-handoff.json` after saving it in the repository. It verifies and loads the file. The example contract under `examples/` provides a fallback if the browser download location is inconvenient.

The real SECOM model baseline is separate application code. Show the included receipt; do not imply the UI just trained a model or that synthetic cohorts improved a real model.

## 4. Translate to a customer pilot (2 minutes)

Ask:

1. Which engineering question currently takes the most time to assemble data for?
2. Which system is authoritative for wafer/lot, tool/chamber, recipe revision and test mapping?
3. Can we select one cohort and agree on a validated trace-to-outcome join?
4. What access, freshness and lineage requirements must every returned asset satisfy?
5. How will we measure time-to-data, correct cohort construction and unsupported-query behavior?

Close: “The first outcome to measure is whether an application can locate the right data, explain its meaning and form the right cohort. That is the foundation for downstream modeling and agent workflows.”

## Questions you may get

**Where does the data come from?** Public SECOM and a labeled synthetic fab scenario.


**Does metadata improve model accuracy?** It can enable better selection and prevent invalid joins; this PoC does not measure a causal model-accuracy improvement from metadata.

**Are the chamber results a root-cause finding?** No. They are matches against generated illustrative context.

**Where is the business value?** The pilot should measure discovery time, cohort correctness, reuse and less repeated data assembly. Do not assign an unmeasured yield or ROI number.

## Preflight

Run unit tests, start `python server.py`, open localhost:8501, test all four query chips, inspect one asset and export a handoff. Rehearse consumer loading. Keep `examples/synthetic-trace-handoff.json` available. The local demo needs no network once cloned.
