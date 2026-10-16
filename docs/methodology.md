# Simulation methodology

## Current contract

One Boro season accepts exactly six decisions:

1. Farm size in bigha
2. Seed quality (`local` or `brri_certified`)
3. Fertilizer (`organic` or `chemical`)
4. Labor/automation (`seasonal_workers` or `power_tiller`)
5. Irrigation (`rainfed` or `pump`)
6. Sale timing (`sell` or `store`)

Farm size must be exactly 1 or 3 bigha, as specified by the PRD. Decision names
and choice values are validated before the engine checks whether production
data is ready. The API accepts an optional unsigned 64-bit integer `seed`. With
the same decisions, model version, data version, and seed, the simulation is
reproducible.

## Calculation flow

The engine keeps the following calculations separate and testable:

- Weather: one scenario is sampled using configured probabilities.
- Yield: farm size × BBS base yield per bigha × seed × fertilizer × weather
  multipliers.
- Costs: farm size × the sum of selected seed, fertilizer, labor, and irrigation
  cost per bigha in the current code.
- Market: selected producer-side paddy price × the selected market multiplier.
  A historical price series and seasonal price movement are not implemented;
  the FPMU observations and a defensible sampling method are missing.
- Storage: a seeded spoilage event can reduce saleable yield by the configured
  fraction of harvest lost.
- Revenue: saleable tonnes × 25 units of 40 kg per tonne × price per 40 kg.
- Profit/loss: revenue − total costs.
- Diagnostic: returns the actual yield, cost, revenue, weather, and storage
  components used in those calculations. It does not infer an optimal path or
  make unsupported causal claims.

The calculation methods are implemented, but the production path remains
unavailable until required inputs have complete source provenance. See
[`../data/README.md`](../data/README.md) and
[`../data/production_model.json`](../data/production_model.json).

### Production-cost scope decision

On 2026-10-04, the product owner selected **full economic production cost**,
including all supported production-cost categories. The current code still
calculates only seed, fertilizer, labor, and irrigation costs; it must not be
described as a complete economic cost or profit calculation.

The official [BRRI Annual Research Review Workshop 2023–24 page](https://brri.gov.bd/pages/static-pages/6922dc83933eb65569e10c1a)
links the [Agricultural Economics Division report (PDF)](https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-brri/2024/12/ac52a0ebd9f34aad80b0fd9d5f2dd9dd.pdf).
The PDF was inspected. Its pages 40–42 include “Estimation of Costs and
Return of MV Rice Cultivation at the Farm Level.” The study describes a
multi-stage random sample from all 14 agricultural regions, with 356 surveyed
farmers across Aus, T. Aman and Boro seasons, including 162 Boro respondents.
It reports 2023–24 survey averages, not costs for the simulator's alternative
decision choices.

For Boro, Table 31 reports per-hectare cost rows for seed, seedling
development, land preparation, human labour, fertilizer, irrigation, pesticide,
herbicide, insecticide/fungicide and power thresher. Table 32 adds interest on
operating capital and land rent. Table 30 reports input quantities; Table 32
reports profitability using these relationships: total cost = variable cost +
fixed cost; gross benefit = paddy value + straw value; gross margin = gross
benefit − variable cost; net return = gross benefit − total cost; full-cost
BCR = gross benefit / total cost; cash-cost BCR = gross benefit / variable
cost. The reported unit is Tk/ha for costs and kg/ha for yield.

These tables are not internally reconcilable from the published values and
method description. For Boro, the printed top-level Table 31 rows sum to Tk
107,788/ha, not the reported variable-cost total Tk 114,114/ha. The displayed
human-labour total equals its listed components; the pesticide row is also
approximately the sum of its herbicide and insecticide/fungicide rows, so
adding parent and subrows would double-count. Table 32's listed interest and
land-rent values total Tk 36,713/ha, not the reported fixed-cost total Tk
37,520/ha. The reported variable and fixed totals sum to Tk 151,634/ha, one
taka more than the reported total cost Tk 151,633/ha. Table 32's stated Boro
BCR formulas produce about 1.17 (full cost) and 1.56 (variable/cash cost)
from its reported gross benefit and cost totals, rather than its listed 1.26
and 1.67. Whether these differences reflect unreported components,
aggregation, or transcription is not explained; do not balance them with an
invented category or substitute the published totals into the simulator.

The report is evidence that these cost categories and a full-cost BCR
calculation are used in a BRRI survey; it is not yet a usable parameter set.
It does not disaggregate local versus BRRI-certified seed, organic versus
chemical fertilizer, seasonal workers versus power-tiller operation, or
rainfed versus pump irrigation. Its aggregate labour, land-preparation,
irrigation and input costs therefore cannot parameterize those choice
contrasts. The Boro yield and selling-price observations are BRRI survey
averages in hectare/kg units, not replacements for the specified BBS yield
series or FPMU market series. Obtain clarification or corrected detailed
worksheets, decision-specific evidence, and a reviewed hectare-to-bigha
conversion before changing the cost model or populating production data.
The product owner confirms no corrected worksheet/erratum is currently
available and directs that these Boro cost/BCR values remain blocked; do not
substitute another source or infer corrected values. The official
[2022–23 programme page](https://brri.gov.bd/pages/static-pages/6922e051933eb65569e267ef)
and [BRRI Internal Review portal](https://ir.brri.gov.bd/) were also inspected.
The portal's [13 February Day 3 page](https://ir.brri.gov.bd/day3.php) lists
Agricultural Economics (XV) in the Socio-Economics and Policy session at
11:35–12:05, presented by Mr. Md Saiful Islam, but exposes no Agricultural
Economics report/table; its linked presentation is for Farm Mechanization and
Post-harvest Technology. The product owner confirms that a direct official URL
for the underlying Agricultural Economics material cannot be verified and
directs that the programme page not be used as cost/BCR evidence and that no
unverified file be substituted. This programme evidence does not verify or
correct the disputed cost/BCR values.

The current engine cost model sums only the selected seed, fertilizer,
labour/automation, and irrigation inputs. It does not represent seedling
development, land preparation, pesticide/herbicide/insecticide/fungicide,
power-thresher, operating-capital interest, or land-rent rows, and the source
does not map these costs to all six simulator decisions. Production therefore
has a code-level full-economic-cost readiness gate. Even if the currently
declared numeric fields were populated, the production engine must continue
returning 503 until the full category hierarchy, decision mapping, units,
conversions, and calculations are source-supported and implemented. Synthetic
test fixtures do not enable this production capability.

## Data integrity and documented rules

The project requires verified Bangladesh agricultural data and rejects
estimates or invented figures. Every production input must identify its source
institution, source document, source year, geographic scope, unit, methodology,
and provenance. A value without complete provenance is unusable.

The project documentation records weather scenario proportions of 40% ideal,
35% mild stress, and 25% severe event. These are retained as a documented
project rule in the data manifest, not treated as verified BWDB data: the
underlying BWDB source, year, geographic scope, and scenario yield effects are
not included. Consequently, production weather probabilities and effects remain
unconfigured.

The data README lists the exact missing yield, cost, market, weather, and
storage inputs. Test-only synthetic parameters exercise calculations but are
never used by the application configuration.

## Early-access signup data

`POST /early-access` accepts a syntactically valid email address, trims and
normalizes it to lowercase, and stores it in a private SQLite database with a
unique constraint. The endpoint returns only a status and message, never the
stored address, and offers no subscriber-list endpoint. Duplicate normalized
addresses receive HTTP 409; malformed addresses receive 400; storage failures
return a generic 500 and are logged without the submitted address. The form
uses a honeypot, request bodies are bounded, and signup POSTs are limited to ten
per minute per directly connected client address in the current process. This
best-effort limiter does not coordinate across multiple application workers;
forwarded proxy addresses are deliberately not trusted. No third-party mailing
service, email-delivery, or mailbox-ownership verification is configured.

By default the database is `backend/instance/early_access.sqlite3`. Set
`VIRTUAL_FARM_EARLY_ACCESS_DB` to a persistent, access-controlled path outside
local development; the hosting filesystem must retain the file across
restarts. The SQLite file is excluded from version control. Address validation
checks syntax only and does not establish that a mailbox exists.
Production hosting also needs HTTPS, protected persistent storage, and a
deployment-appropriate shared abuse-control strategy if it runs multiple
workers or sits behind a reverse proxy.

## Production parameter inventory

“Current production value” below means the value loaded by
`backend/simulation/config.py` from `data/production_model.json`, or a default
explicitly constructed there. “Verified” means an actual source document and
supporting provenance are present in this repository. A named required source
is not evidence that the source was consulted.

| Parameter | Current production value | Unit | Where used | Verification/status | Intended source | Test-only value? | Evidence still required |
|---|---:|---|---|---|---|---|---|
| Boro base yield | `null` | tonnes of paddy/bigha | Yield calculation | Missing for the configured BBS contract. BRRI report also gives a 2023–24 Boro MV survey mean of 5,949 kg/ha, not the configured BBS series or simulator decision baseline | BBS | Yes: `2.0` | BBS Boro yield table, season/year, geographic scope, paddy-vs-rice basis and conversion to bigha |
| Local seed cost | `null` | BDT/bigha | Costs | Missing for the local-seed choice. BRRI Table 31 reports a Boro MV survey average of Tk 5,045/ha, not a local-seed cost | DAE | Yes: `13.0` | Source, year, locality, seed quantity/rate and cost basis; distinguish local seed from the survey's MV average |
| BRRI-certified seed cost | `null` | BDT/bigha | Costs | Missing for the certified-seed choice. BRRI Table 31 does not separate seed class/variety | DAE | Yes: `17.0` | Same evidence, for certified seed |
| Local seed yield effect | `null` | ratio multiplier | Yield | Missing; not verified | BBS/BRRI | Yes: `1.0` | Boro trial evidence defining comparator, seed class, geography and method |
| BRRI-certified seed yield effect | `null` | ratio multiplier | Yield | Missing; not verified | BBS/BRRI | Yes: `1.2` | Comparable evidence relative to the base-yield population |
| Organic fertilizer cost | `null` | BDT/bigha | Costs | Missing for the organic-fertilizer choice. BRRI Table 31 reports only aggregate Boro fertilizer cost of Tk 11,065/ha; Table 30 lists nutrient inputs, not an organic/chemical cost comparison | DAE | Yes: `19.0` | Input source, application rate, season, geography and cost basis |
| Chemical fertilizer cost | `null` | BDT/bigha | Costs | Missing for the chemical-fertilizer choice. BRRI Tables 30–31 do not provide a chemical-versus-organic cost or treatment comparison | DAE | Yes: `23.0` | Same evidence, specifying fertilizer composition/rate |
| Organic fertilizer yield effect | `null` | ratio multiplier | Yield | Missing; not verified | BBS/BRRI | Yes: `1.1` | Boro evidence for defined treatment, control and application rate |
| Chemical fertilizer yield effect | `null` | ratio multiplier | Yield | Missing; not verified | BBS/BRRI | Yes: `1.3` | Comparable evidence for the specified treatment |
| Chemical soil-degradation probability | Not represented in production model | probability per defined exposure period | No current use | Not implemented. Earlier prototype text mentions 15%; unverified, not a production value | DAE/BRRI soil evidence | No fixture field | Study population, event definition, timeframe, geography and source |
| Chemical soil-degradation yield effect | Not represented in production model | yield reduction fraction and time horizon | No current use | Not implemented. Earlier prototype text mentions 10% next-season yield reduction; unverified | DAE/BRRI longitudinal soil and crop evidence | No fixture field | Evidence for effect size, duration, affected crop/soil and methodology |
| Seasonal-worker cost | `null` | BDT/bigha | Costs | Missing. BRRI Table 31 reports average human labour Tk 49,332/ha for Boro, split into hired, family and hired-contract labour; it does not isolate the simulator's seasonal-worker option | DAE | Yes: `29.0` | Wage/rate, task scope, season/year and geographic basis; map survey labour categories to the modeled choice |
| Power-tiller cost | `null` | BDT/bigha | Costs | Missing. BRRI reports land-preparation cost and power-thresher cost, not a distinct power-tiller option cost | DAE | Yes: `31.0` | Rental/ownership and operating-cost basis, tasks, season/year and geography |
| Seedling-development cost | Not represented in current model | Tk/ha in source; model unit pending | No current use | BRRI Table 31 reports Tk 3,930/ha for Boro MV survey farms; not separated by seed choice | BRRI Agricultural Economics Division report, Table 31 | No fixture field | Cost definition, whether it overlaps seed/labour, decision dependence and conversion |
| Land-preparation cost | Not represented as a separate current cost | Tk/ha in source; model unit pending | No current use | BRRI Table 31 reports Tk 12,565/ha for Boro MV farms (“ploughing and laddering”); not split by method or power-tiller choice | BRRI Agricultural Economics Division report, Table 31 | No fixture field | Resource/task definition, whether it overlaps labour/machinery, decision dependence and conversion |
| Pesticide cost | Not represented in current model | Tk/ha in source; model unit pending | No current use | BRRI Table 31 reports Tk 4,447/ha for Boro; parent/subcategory relationship to herbicide and insecticide/fungicide is unclear and overall variable costs do not reconcile | BRRI Agricultural Economics Division report, Table 31 | No fixture field | Clarify category hierarchy, omitted/unreported components, decision dependence and conversion |
| Herbicide cost | Not represented in current model | Tk/ha in source; model unit pending | No current use | BRRI Table 31 reports Tk 1,192/ha for Boro, apparently a pesticide subrow; not a separate decision input | BRRI Agricultural Economics Division report, Table 31 | No fixture field | Clarify whether included within the pesticide row; establish decision dependence and conversion |
| Threshing cost | Not represented in current model | Tk/ha in source; model unit pending | No current use | BRRI Table 31 reports power-thresher cost of Tk 4,449/ha for Boro; it does not define all threshing cost or a simulator choice | BRRI Agricultural Economics Division report, Table 31 | No fixture field | Category coverage, decision dependence, denominator and conversion |
| Interest / financing cost | Not represented in current model | Tk/ha in source; model unit pending | No current use | BRRI Table 32 reports Tk 1,823/ha as interest on operating capital; rate/base/timing are not specified in the inspected pages and fixed-cost total does not reconcile | BRRI Agricultural Economics Division report, Table 32 | No fixture field | Principal, rate, period, cost base, decision dependence, denominator and calculation method |
| Land rent / land-use cost | Not represented in current model | Tk/ha in source; model unit pending | No current use | BRRI Table 32 reports Tk 34,890/ha for land rent; rental/imputed definition and treatment are not supplied in the inspected pages | BRRI Agricultural Economics Division report, Table 32 | No fixture field | Rental vs imputed land cost definition, season, geography, denominator and treatment |
| Other production costs | No explicit “other” category identified in BRRI Tables 30–32 | Not defined | No current use | Not a model parameter. Reported cost totals do not reconcile with visible components; this gap is not evidence for a catch-all cost | BRRI Agricultural Economics Division report, Tables 30–32 | No fixture field | Obtain corrected breakdown; only add separately defined, evidenced categories |
| Power-tiller breakdown probability | Not represented in production model | probability per defined operating period | No current use | Not implemented. Earlier project context stated 12%; source document absent | DAE machinery records/farmer interviews | No fixture field | Operating hours/period, event definition, machine/population and geography |
| Power-tiller breakdown effect | Not represented in production model | repair cost, downtime or yield effect with units | No current use | Not implemented; no supported effect is specified | DAE machinery records/farmer interviews | No fixture field | Repair/downtime observations and model interpretation |
| Rainfed cost | `null` | BDT/bigha | Costs | Missing. BRRI Table 31 gives an aggregate Boro irrigation cost of Tk 16,955/ha, with no rainfed/pump split | DAE | Yes: `0.0` | Confirm cost boundary and any excluded land/water/labor charges; distinguish irrigation alternatives |
| Rainfed drought probability | Not represented in production model | probability per Boro season/region | No current use | Not implemented. Earlier project context stated 35%; source evidence absent | BWDB/DAE | No fixture field | Boro drought definition, regional/temporal basis and probability derivation |
| Rainfed drought effect | Not represented in production model | crop/yield effect with defined unit and duration | No current use | Not implemented; no effect is supported | BWDB/DAE/BBS | No fixture field | Event-linked crop impact data and methodology |
| Pump irrigation cost | `null` | BDT/bigha | Costs | Missing for the pump choice. BRRI Table 31 reports only aggregate Boro irrigation cost of Tk 16,955/ha | DAE | Yes: `37.0` | Water charge, fuel/electricity, irrigation quantity, year/season and geography; distinguish irrigation alternatives |
| Ideal weather probability | `null` | probability per simulated season | Weather sampling | 40% is specified in methodology but unverified and not loaded in production | BWDB | Yes: `0.25` | BWDB source, season/region, event definition and derivation |
| Mild-stress weather probability | `null` | probability per simulated season | Weather sampling | 35% is specified in methodology but unverified and not loaded in production | BWDB | Yes: `0.35` | Same as above |
| Severe-event weather probability | `null` | probability per simulated season | Weather sampling | 25% is specified in methodology but unverified and not loaded in production | BWDB | Yes: `0.40` | Same as above |
| Ideal weather yield effect | `null` | ratio multiplier | Yield | Missing; not verified | BWDB/BBS | Yes: `1.0` | Event definition and observed impact for the relevant Boro population |
| Mild-stress weather yield effect | `null` | ratio multiplier | Yield | Missing; not verified | BWDB/BBS | Yes: `0.8` | Same as above |
| Severe-event weather yield effect | `null` | ratio multiplier | Yield | Missing; not verified | BWDB/BBS | Yes: `0.5` | Same as above |
| Producer-side paddy base price | `null` | BDT/40 kg paddy | Market price and revenue | Missing for the configured FPMU contract. BRRI Table 32 reports a 2023–24 Boro survey selling-price average of Tk 28/kg, not the required FPMU series | FPMU | Yes: `20.0` | FPMU observations with market, geography, dates, commodity/quality basis and units; reconcile BRRI's aggregate price/value reporting |
| Sell price multiplier | `1.0` (code default) | ratio | Market price | Identity default; not separately source-verified | FPMU, if timing effect is intended | Yes: fixture also uses `1.0` | Confirm immediate sale has no timing adjustment or source the rule |
| Store price multiplier | `null` | ratio | Market price | Missing; not verified. Earlier project context stated 15% upside, without source/time-series evidence | FPMU | Yes: `1.25` (synthetic, not the earlier project figure) | Three-year producer-price series and defensible storage period/price movement method |
| Producer-side historical market price series | Not represented in current manifest | BDT/40 kg paddy by market/date/region | Not currently sampled | Required by project documentation for market movement; missing | FPMU | No fixture series | Three-year observations, market/geography/date/quality basis and defensible sampling method |
| Sell spoilage probability | `0.0` (code default) | probability | Storage calculation | Structural immediate-sale default, not source evidence | Only non-applicable if immediate-sale boundary is confirmed | Yes: `0.0` | Confirm decision interpretation and model boundary |
| Sell spoilage fraction | `0.0` (code default) | fraction of harvest lost | Saleable yield | Structural immediate-sale default, not source evidence | Only non-applicable if immediate-sale boundary is confirmed | Yes: `0.0` | Confirm decision interpretation and model boundary |
| Store spoilage probability | `null` | probability per storage period | Seeded storage event | Missing; not verified. Earlier project context stated 10%, without source or period | DAE/farmer interviews | Yes: `1.0` (synthetic) | Storage duration/method/location and observed rate/method |
| Store spoilage fraction | `null` | fraction of harvest lost if event occurs | Saleable yield/revenue | Missing; not verified | DAE/farmer interviews | Yes: `0.5` (synthetic) | Loss severity evidence or defensible conditional effect |
| Tonnes-to-40-kg conversion | `25` | units of 40 kg/tonne | Revenue conversion in `engine.py` | Exact unit conversion, not an agricultural input | Metric units | No | No agricultural evidence required |

The earlier prototype/project-context numbers are not active production
values. Fertilizer prototype values were explicitly identified as requiring
agricultural validation; other figures had been attributed to a Master
Reference that is not present in the repository. Those attributions cannot be
checked here. Treat such values as **specified/prototype-only and unverified**,
never as production evidence. The checked-in repository has no root README,
PRD, or Master Reference; the methodology and data README are the available
project documentation.

Historical figures that appeared in earlier prototype/configuration material
are included here only to distinguish them from current production values:

| Historical figure | Where it appeared / status | Verification and evidence still required |
|---|---|---|
| Local/certified seed cost: BDT 800/2,200 per bigha | Earlier configuration attributed these to an unavailable “Master Reference, Phase 01” | Unverified; retrieve source/year, location, rate and cost basis |
| Organic/chemical fertilizer cost: BDT 1,200/2,800 per bigha; yield uplift 8%/15% | Frontend prototype; earlier configuration explicitly required agricultural validation | Unverified; DAE costs and BBS/BRRI trial evidence |
| Chemical fertilizer risk: 15% chance of 10% yield reduction next season | Frontend prototype / earlier configuration; no source record | Unverified; event definition, longitudinal study, timeframe and geography |
| Power-tiller breakdown probability: 12% | Earlier configuration attributed to unavailable Master Reference; breakdown effect not defined | Unverified; event probability and repair/downtime evidence |
| Rainfed risk probability: 35% | Earlier configuration attributed to unavailable Master Reference; drought event not defined | Unverified; BWDB/DAE regional Boro drought and yield evidence |
| Pump irrigation cost: BDT 1,800 per bigha | Earlier configuration attributed to unavailable Master Reference | Unverified; DAE rate, year, quantity and geographic scope |
| Store upside: 15%; spoilage probability: 10% | Earlier configuration attributed to unavailable Master Reference; no price series or storage period | Unverified; FPMU price data and measured spoilage evidence |
| Storage loss fraction: `1.0` | Earlier configuration code, not accompanied by a source; means entire crop is lost conditional on spoilage | Unsupported; not an established project rule |
| Weather yield multipliers: `1.0` for all events | Earlier configuration used neutral placeholders while effects were unspecified | Not observed effects; BWDB/BBS event-linked yield evidence required |

These figures are historical project-context claims, not current values,
verified inputs, or guaranteed PRD requirements. The root PRD and Master
Reference are not present in the checked-in repository, so their original
wording and source citations cannot be independently audited.

The complete current synthetic test fixture uses base yield `2.0`; seed costs
`13.0`/`17.0` and effects `1.0`/`1.2`; fertilizer costs `19.0`/`23.0` and
effects `1.1`/`1.3`; labor costs `29.0`/`31.0`; irrigation costs `0.0`/`37.0`;
weather probabilities `0.25`/`0.35`/`0.40` and effects `1.0`/`0.8`/`0.5`;
market price `20.0`, store multiplier `1.25`, spoilage probability `1.0`, and
loss fraction `0.5`. These numbers exist only to test arithmetic and seeded
execution. They are not agricultural estimates, PRD values, or production
defaults.

## Risk and limits

No chemical-fertilizer degradation, power-tiller breakdown, rainfed drought,
pest, or other unsupported risk is simulated. A rule can be enabled only after
its probability, effect, unit, source, and interpretation are defensible.

## API behavior

`POST /simulate` accepts:

```json
{
  "decisions": {
    "farm_size_bigha": 1,
    "seed_quality": "local",
    "fertilizer_type": "organic",
    "labor_choice": "seasonal_workers",
    "irrigation_choice": "rainfed",
    "sell_or_store": "sell"
  },
  "seed": 42
}
```

The seed is optional. The API returns 400 for malformed requests or invalid
decisions, 503 when required production inputs are missing or unusable, and a
generic 500 response for unexpected failures (with details logged server-side).
Successful results include model and data versions, event outcomes, financial
components, and a structured diagnostic.

Run tests from the repository root with `pytest`.
