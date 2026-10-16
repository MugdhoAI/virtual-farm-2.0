# Virtual Farm model data

`production_model.json` is the versioned input manifest read by the backend. It
is deliberately unconfigured: every agricultural or economic production value
is `null` until its provenance is entered and reviewed. The production
simulation returns HTTP 503 while required inputs are unavailable.
The response data version combines the declared manifest version with a
SHA-256 fingerprint of the records, so different manifest contents identify
different input configurations.

## Required provenance for every populated input

Each record must include:

- source institution
- source document and reference or URL
- source year
- geographic scope
- value and unit
- methodology/interpretation

The `required_source_institution` field identifies the expected source; it does
not claim that the value has been obtained or verified. A value without all
provenance fields is unusable and fails validation. Do not promote frontend
prototype values or test fixture values into this manifest.

## Missing production inputs

The current manifest has no verified production values for:

- BBS Boro paddy base yield in tonnes per bigha
- DAE costs per bigha for both seed choices, both fertilizer choices, both
  labor/automation choices, and both irrigation choices
- Decision-specific costs for each seed, fertilizer, labour/automation and
  irrigation choice. The official [BRRI Annual Research Review Workshop
  2023–24 page](https://brri.gov.bd/pages/static-pages/6922dc83933eb65569e10c1a)
  links the [Agricultural Economics Division report
  (PDF)](https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-brri/2024/12/ac52a0ebd9f34aad80b0fd9d5f2dd9dd.pdf),
  inspected at pages 40–42. Its 2023–24 survey covers 162 Boro farmers from a
  sample across 14 agricultural regions and reports average MV Boro inputs,
  costs and returns in per-hectare units. It documents cost categories used in
  a farm-level study, including seed, seedlings, land preparation, labour,
  fertilizer, irrigation, pesticide/herbicide/insecticide/fungicide, power
  thresher, operating-capital interest and land rent. It does not separate the
  six simulator alternatives, and its published variable/fixed totals and BCR
  calculations do not reconcile from the displayed rows/formulas. Treat the
  report as evidence for candidate categories and model scope only; do not
  load its averages as simulator inputs or invent a balancing `other` cost.
  Obtain clarification/corrected worksheets, decision-specific evidence and a
  reviewed hectare-to-bigha conversion first. The product owner confirms no
  corrected worksheet/erratum is currently available and directs that the
  disputed Boro cost/BCR values remain blocked; do not substitute another
  source or infer corrections. The official
  [2022–23 programme page](https://brri.gov.bd/pages/static-pages/6922e051933eb65569e267ef)
  and [Internal Review portal](https://ir.brri.gov.bd/) confirm the Agricultural
  Economics (XV) presentation in the 13 February 2024 Socio-Economics and
  Policy session. The [Day 3 page](https://ir.brri.gov.bd/day3.php) does not
  expose an Agricultural Economics report/table; its linked PDF is for Farm
  Mechanization and Post-harvest Technology. No 2022–23 cost table was used
  to resolve or replace the disputed 2023–24 figures. The product owner cannot
  verify a direct official URL for that underlying 2022–23 material and
  directs that the programme page not be treated as cost/BCR evidence and no
  unverified file be substituted.
- A BBS Boro yield series in the required production-model definition. The
  BRRI report separately reports a 2023–24 Boro MV survey mean of 5,949 kg/ha;
  this is not the configured BBS yield input or the simulator's
  decision-specific yield baseline.
- BBS/BRRI seed and fertilizer yield multipliers
- BWDB ideal/mild/severe event probabilities and BWDB/BBS yield effects
- FPMU producer-side paddy price per 40 kg, three-year observations, and a
  defensible method for seasonal market-price movement
- FPMU-backed storage price multiplier
- DAE/farmer-interview storage spoilage probability and conditional loss
  fraction, including storage period and method

The production cost contract is explicitly **full economic production cost**.
The current engine adds only seed, fertilizer, labour/automation, and
irrigation; it omits BRRI report categories including seedling development,
land preparation, pesticide/herbicide/insecticide/fungicide, power-thresher,
operating-capital interest, and land rent. The official 2023–24 report does
not reconcile its published Boro totals/BCR and does not map its aggregate
cost rows to all six simulator decisions; the 2022–23 Agricultural Economics
table could not be directly inspected. Accordingly a code-level production
readiness gate also requires full-cost category coverage and six-decision
mapping. Populating the currently declared fields alone cannot enable a
production result. Do not add a catch-all or calculate full costs from
unreconciled survey totals.

Chemical soil-degradation risk, power-tiller breakdown risk, and rainfed
drought risk are not represented in the production manifest or simulation.
They require defensible event definitions, probabilities, effect sizes/units,
time horizons and source evidence before they can be modeled.

The methodology document records project-specified weather proportions of
40%/35%/25%. They are preserved under `documented_rules` for traceability, but
the BWDB record, year, and geographic scope are absent. They are not loaded as
production weather probabilities.

Risk rules such as fertilizer degradation, machinery breakdown, and
rainfed-drought exposure are not enabled. Their probabilities, effects, units,
sources, and interpretation are not sufficiently documented for a
single-season model.

The code's sell-scenario multiplier `1.0` and sell spoilage values `0.0` are
implementation defaults, not source-backed agricultural data. The test-only
synthetic values are documented in the [methodology parameter inventory](../docs/methodology.md#production-parameter-inventory).
Do not copy those test values or the prototype/project-context percentages
into this file as production data.
