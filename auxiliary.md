# Auxiliary Data

## Selected Project Area

Topic 7 — AI Workforce Investment (AI / labor economics)

## Candidate Vision A

The Executive Director of the California Workforce Development Board must decide which California regions and occupations should be prioritized for a new AI upskilling and workforce-transition pilot program.

## Candidate Vision B

The Chief Leadership and Human Resources Officer at Accenture must decide which representative U.S. professional role groups to prioritize for the next round of advanced AI upskilling and workflow-redesign pilots.

*Vision statements copied verbatim from `data-fit.md` (Role 3) so all five role files describe the same two candidates.*

---

## The question this file answers

For each candidate Vision: **what one decision-important input is missing from our core data, where can we obtain it, what is one row of it, how would it connect, and what could fail?** Two additions total — not a long list.

**Source budget.** Topic 7 permits six sources: the two core sources (Anthropic Economic Index, OpenAI Signals) and four public additions (`O*NET database`, `BLS employment and wages`, `BLS employment projections`, `Census BTOS`). This file spends **two of the four** additions — one per candidate Vision. Nothing outside that list is proposed.

---

## 0. How this file sits next to Role 3 and Role 5

The three roles overlap by design, so the boundary is stated here rather than left implicit:

| Role | Owns | This file's relationship to it |
|---|---|---|
| **Role 3 — `data-fit.md`** | Draws the honest boundary: what the core data can support, partly support, and cannot reach; names the **missing data elements**. | This file takes Role 3's missing-element tables as its worklist and answers them source by source. Section 1 below is that mapping. |
| **Role 5 — `technical.md`** | Validates **access, format, scale, join keys, and blockers** for the recommended path. | Role 5 answered "can we open it?" This file answers "what is a row, how does it attach to *our* rows, and what breaks?" Where Role 5 and I recommend the same source, Section 2 says so explicitly instead of re-discovering it. |
| **Role 4 — this file** | Supplies the **specific missing input**, its grain, its join, its failure modes, and a labelled synthetic fallback if the real input never arrives. | — |

One checkable number, then the substance. Role 3 listed **8** missing decision elements for Vision A and **8** for Vision B — 16 in total. Section 1 asks, element by element, whether **any permitted source** contains it.

---

## 1. Start from the gap, in Role 3's own words

### 1.1 Vision A — the gap is geographic, and one permitted source closes most of it

| Role 3's missing element (verbatim) | Does any permitted source contain it? | Verdict |
|---|---|---|
| `regional_occupation_employment` — Role 3 calls this **"the most important gap for Vision A"** | **Yes.** BLS OEWS publishes employment by occupation for California and for California's metropolitan / nonmetropolitan areas. | **Fill it — this is Vision A's addition.** |
| `regional_occupation_wage` | **Yes.** Same file, same rows. | Filled by the same addition, at no extra cost. |
| `regional_employment_growth` | **Partly.** BLS Employment Projections gives national growth only; OEWS publishes no projections at all. | Not fillable at regional level from the permitted list. Recorded as a limit. |
| `worker_ai_skill_level` | **No.** No permitted source measures individual worker AI skill. | Unfillable. Must be a stated boundary. |
| `employer_ai_skill_demand` | **Partly.** Census BTOS observes AI use by business function and whether firms trained staff vs hired AI-trained staff. | Partly fillable — see Section 3. |
| `training_availability_cost` | **No.** | Unfillable. Must be a stated boundary. |
| `productivity_change` | **No.** | Unfillable. Must be a stated boundary. |
| `worker_displacement` | **Partly.** BTOS asks how AI use affected total employment over six months. | Partly fillable — see Section 3. |

**Two of Role 3's eight Vision-A elements — including the one Role 3 ranked first — are cleanly fillable from the permitted list, and one more is a bonus.** That is a strong result and it is the reason Vision A's addition is OEWS.

### 1.2 Vision B — the gap is organisational, and the permitted list cannot close it

| Role 3's missing element (verbatim) | Does any permitted source contain it? | Verdict |
|---|---|---|
| `internal_role_mapping` (Role 3: among "most important gaps for Vision B") | **No.** Mapping external SOC occupations to Accenture job families is by definition internal. | Unfillable. |
| `internal_role_headcount` (same) | **No.** No permitted source reports employment inside one firm. | Unfillable. |
| `internal_ai_usage_by_role` (same) | **No occupied-level substitute exists**, but BTOS is the only permitted source that observes **AI use by employers at all** rather than by individual chat users. | **Partial substitute — this is Vision B's addition.** |
| `employee_ai_skill_level` | No. | Unfillable. |
| `internal_workflow_task_data` | Partly — BTOS Q10 reports which **task categories** employees used generative AI to assist with. | Partly fillable via the same addition. |
| `internal_productivity_outcomes` | No. | Unfillable. |
| `workflow_risk_requirements` | No. | Unfillable. |
| `training_and_implementation_cost` | No. | Unfillable. |

**This is a finding worth stating plainly in `project-start.md`: Role 3's three most important Vision-B elements are all internal to Accenture, and no source in the permitted list contains any of them.** So Vision B's addition cannot be "the missing input." It has to be the **closest permitted stand-in for the adoption half of the gap** — the only permitted source that shows what employers actually *do* with AI once they have it. That is Census BTOS.

### 1.3 What one row is in the core data — the fact that makes both gaps concrete

| Source | One row is | Grain | Keys |
|---|---|---|---|
| Anthropic `labor_market_impacts/job_exposure.csv` | one occupation with an observed AI-exposure score | occupation | `occ_code` (SOC), `title`, `observed_exposure` |
| Anthropic `labor_market_impacts/task_penetration.csv` | one task with a penetration score | task | `task` (free-text O*NET task string), `penetration` |
| Anthropic `release_2026_06_26/aei_claude_ai_<date>.csv` | one metric value for one geography × one category node | geography × node × month | `geo_id`, `node_external_id` ("O*NET element ID, SOC code, or topic UUID"), `metric_id` |
| OpenAI Signals (`*.csv`, 25 files) | one share of messages for one grouping key | month × (state / topic / work_related / IWA / …) | `month`, `state_code`, `iwa_cleaned` (O*NET Intermediate Work Activity), `topic` |

**The honest boundary this exposes:** both core sources observe **AI requests and messages**. Neither one contains a **worker count**, a **wage**, or **what an employer did**. So the core data answers *"where is AI being used on tasks?"* — it cannot answer *"how many workers, in which places, at what cost, and did the firm retrain them or replace them?"* Those are precisely the two questions the two Visions have to answer.

---

## 2. Vision A addition — **BLS Occupational Employment and Wage Statistics (OEWS), May 2025**

### 2.1 The one decision-important fact that is missing

**How many people in California — and in which California places — actually work in each AI-exposed occupation, and what does that labour cost.**

Vision A has to rank **region × occupation** combinations. The core data ranks occupations by AI exposure but carries **no denominator**. Without a worker count, "high exposure" is not yet a priority: an exposed occupation employing 400 people in a region is a different decision from the same occupation employing 90,000 there. Adding employment and wages converts an exposure list into a sizeable, costed target list.

### 2.2 Source and who collects it

- **Source:** BLS Occupational Employment and Wage Statistics (OEWS), May 2025 release — <https://www.bls.gov/oes/tables.htm>
- **Collector:** U.S. Bureau of Labor Statistics (BLS), in cooperation with State Workforce Agencies. Government statistical product — no login, no cost.
- **Access note (sourced, and a real finding):** the tables page loads and lists the May 2025 files (National, State, Metropolitan and nonmetropolitan area, National industry-specific and by ownership, All data) as HTML and XLSX, but **automated requests to the download paths returned `HTTP 403 Forbidden`** when I probed them. Downloads should be done from a normal browser session, and the files should not be committed to the repo (topic 7's access note).
- *Sourced fact:* OEWS "produces employment and wage estimates annually for approximately **830 occupations**… available for the nation as a whole, for individual states, and for metropolitan and nonmetropolitan areas; national occupational estimates for specific industries are also available."

### 2.3 What one row is

**One row = one occupation within one area** (area being a state, a metropolitan area, or a nonmetropolitan area). Typical fields — *expected layout, to be confirmed on first open* (I could not retrieve the file body: BLS returned 403):

| Field (expected) | Meaning |
|---|---|
| `AREA`, `AREA_TITLE`, `AREA_TYPE` | which geography the row describes, and its type (state / metro / nonmetro) |
| `OCC_CODE`, `OCC_TITLE`, `O_GROUP` | SOC occupation code, title, and whether the row is a detailed occupation, a broad group, a major group, or the "all occupations" total |
| `TOT_EMP`, `EMP_PRSE` | estimated employment and its relative standard error |
| `JOBS_1000`, `LOC_QUOTIENT` | employment per 1,000 jobs in the area; concentration relative to the nation |
| `H_MEAN`, `A_MEAN`, `H_MEDIAN`, `A_MEDIAN`, `H_PCT10…H_PCT90` | hourly / annual mean, median and percentile wages |

*Sourced facts:* mean and percentile/median wages are defined in OEWS's own FAQ; the FAQ also documents why **the sum of areas within a state does not equal the statewide total** (rounding, items not released separately, cross-state metropolitan areas, and establishments that report a state but no metro area).

### 2.4 How it connects to our data — and the result's grain

```text
core data: occ_code (SOC)  →  OEWS OCC_CODE (SOC), filtered to California areas
                             ↓
        one row per  (California area × SOC occupation)
        carrying TOT_EMP, wages, LOC_QUOTIENT   +   observed AI exposure from the core data
```

- **Join key:** SOC code — the same key the core data already uses, and the same key Role 5's proposed path uses. Role 5 flagged that this join needs a taxonomy check; Section 2.6 item 4 says what specifically to check.
- **Filter:** California = the CA statewide row, plus CA metropolitan and nonmetropolitan area rows.
- **Output grain becomes** *one occupation in one California area* — which is **exactly the unit Role 5 proposed for the Vision A table**. OEWS is what supplies the row's size and wage columns.
- **Convergence with Role 5:** `technical.md` independently recommends BLS OEWS California files for Vision A. I am not claiming a new discovery — I am supplying the grain, the join, and the failure modes that Role 5's access test did not cover.

### 2.5 What new question it makes answerable

> Which California area × occupation cells combine **high observed AI exposure** with **enough affected workers and wage mass to matter** — i.e. where would a pilot reach the most people, and where does the same exposure signal describe a rounding error rather than a workforce?

And, with the 5th-percentile-to-95th-percentile wage spread in the same row:

> For an exposed occupation, is this a low-wage group where retraining is the only mobility path, or a high-wage group where the risk is displaced earnings rather than displaced employment?

### 2.6 What could fail

1. **The geography does not nest.** OEWS areas are state and metropolitan/nonmetropolitan areas built on OMB delineations. CWDB funds and plans through **Regional Planning Units built from county groupings**. Metropolitan areas are not unions of CWDB regions — a metropolitan area can span counties that sit in different Regional Planning Units. **Until a defensible county → RPU crosswalk exists, the tool cannot speak CWDB's own geography**, and any RPU-level total would be an apportionment we invented. This is the single hardest blocker in Vision A and it must be named in `project-start.md`, not smoothed over.
2. **Levels, not direction.** OEWS is listed by BLS under "Data we do not have" for occupational employment projections and occupational outlook. OEWS therefore cannot answer "is this occupation growing?" — a growing and a shrinking exposed occupation produce identical OEWS rows. Direction requires BLS Employment Projections, which is national only (Section 4.2).
3. **Aggregate rows masquerade as occupations.** OEWS files mix detailed occupations with broad groups, major groups, and an "all occupations" total, distinguished by `O_GROUP`. Sorting on employment without filtering `O_GROUP` puts major-group rows at the top of the table and silently corrupts any ranking.
4. **Taxonomy vintage.** The core data's SOC codes come from Anthropic/OpenAI's mapping; OEWS May 2025 uses the 2018 SOC; O*NET 31.0 (which both core sources reference for tasks) uses O*NET-SOC 2019. Before merging, confirm the SOC year on **both** sides and record which occupations the crosswalk merges or drops.
5. **Suppression and non-release.** OEWS does not publish every occupation × area cell. Small areas will have missing employment or missing wage estimates; the FAQ documents that major-group totals do not equal the sum of detailed occupations. Every publication must count and report unmatched cells rather than dropping them quietly.
6. **Vintage mismatch with the AI signal.** OEWS is a May 2025 employment snapshot; the AI-usage data spans 2024–2026. We will be weighting a 2026 activity signal by a 2025 employment level — acceptable, but it must be stated.
7. **Wages are not total labour cost.** OEWS excludes benefits, and excludes the self-employed. For a "cost of the workforce affected" framing, both exclusions bias the number.
8. **No skill or training information.** OEWS cannot say whether the exposed workers are trainable, already skilled, or unionised — which is why Role 3's `worker_ai_skill_level` and `training_availability_cost` stay unfilled even after this addition.

### 2.7 Synthetic fallback *(labelled — demonstrates a mechanism, provides no evidence)*

The real OEWS file exists; the piece that does not exist anywhere in the permitted list is the **county → Regional Planning Unit crosswalk**. So the synthetic artefact targets exactly that:

A **hand-built 2-row × 2-Regional-Planning-Unit crosswalk** (`county_fips, county_name, rpu_code, rpu_name`) covering four illustrative California counties across two illustrative RPUs, joined to a **6-row** synthetic `area × occupation` table carrying `soc_code, occupation, area_name, tot_emp, a_median, loc_quotient, observed_exposure, redesign_priority`.

- The **join mechanism is real** (county → RPU → aggregated employment), so the sample genuinely demonstrates the shape of the final table.
- The **crosswalk rows are invented** and marked `SYNTHETIC — illustrative only`.
- No number in the sample may be quoted as evidence. Its only job is to show the team — and the reader — that the blocker is a mapping problem, not a data-availability problem, and that solving the mapping produces one clean row per *RPU × occupation*.

---

## 3. Vision B addition — **Census Business Trends and Outlook Survey (BTOS), AI Supplement, 11/17/2025 – 02/08/2026**

### 3.1 The one decision-important fact that is missing

**What firms actually do with AI once they have it.** The core data counts AI requests. It cannot say whether AI **supplements an employee's task or performs a task that an employee used to do**, whether firms respond by **retraining existing staff or hiring AI-trained staff**, or whether AI use **changed total employment**. Vision B's whole decision — advanced AI upskilling *and* workflow redesign — is a decision about exactly those three behaviours.

### 3.2 Source and who collects it

- **Source:** U.S. Census Bureau, Business Trends and Outlook Survey (BTOS), AI Supplement Table 2026 — <https://www.census.gov/hfp/btos/data_downloads>
- **Collector:** U.S. Census Bureau. Continuous **biweekly** survey; approximately **1.2 million businesses** in the sample across **6 panels** of ~200,000 cases; each panel reports once every 12 weeks.
- **Access (verified, not assumed):** I downloaded `AI_Supplement_Table_2026.xlsx` (**578,790 bytes**) and opened it with pandas. It loads cleanly. No login required. Licence: U.S. federal statistical product; topic 7's access note still bars committing it to the repo.
- **Why the supplement and not the core series:** *sourced* — BTOS replaced the phrase "producing goods or services" with "**any of its business functions**" in the AI core question **starting with the 11/17/2025 collection**. The AI supplement runs from exactly that date, so the supplement is both the richer product and the consistent-vintage one.

### 3.3 What one row is — read off the actual file

The workbook has **9 sheets**: `National Response Estimates` (88 estimate rows), `National Standard Errors`, `Sector Response Estimates` (1,704), `Sector Standard Errors`, `State Response Estimates` (4,509), `State Standard Errors`, `Employment Response Estimates` (599), `Employment Standard Errors`, and a `Data Dictionary`.

**One row = one answer-category estimate for one (scope × breakdown × question) cell.** Columns: `Scope (see data dictionary)`, `Question ID`, `Question`, `Answer ID`, `Answer`, `Estimate`, `Estimate - Yes`, `Estimate - No`, `Estimate - Don't know`, plus the sheet's own breakdown column (`State` / `Sector` / `Empsize`).

Three dimensions, all sourced from the file itself:

**Breaks (the breakdown column):**
- `Sector` — 2-digit NAICS sectors (11, 21, 22, 23, 31, 42, 44, 48, 51, 52, 53, **54**, 55, 56, 61, 62, 71, 72, 81) **plus `XX`**
- `State` — 50 states + DC + PR + **`XX`**
- `Empsize` — buckets A–G, where **G = "250 or more employees"** is the largest available bucket

**`Scope` (this is the most analytically interesting dimension in the file):**
| Scope | Rows are representative of |
|---|---|
| 1 | all companies in the target population |
| 2 | companies that reported using AI in any business function |
| 3 | companies that reported using AI to perform tasks previously done by employees |
| 4 | companies that reported using genAI to assist in work-related tasks |
| 5 | companies planning to use AI in any business function in the next six months |
| 6 | companies **not** planning to use AI in any business function in the next six months |

`Scope` turns the table into conditional distributions — e.g. *among firms that replaced employee tasks with AI, what did they change?* — which is a stronger instrument than a single headline adoption rate.

**Questions** — 13 of them (Q1–Q13). The four that bear directly on Vision B:

| Q | Question (abridged) | National estimate |
|---|---|---|
| Q1 | In the last two weeks, did this business use AI in any of its business functions? | **Yes 17.9%** · No 71.3% · Don't know 10.8% |
| Q3 | In the last six months, did this business use AI to do any of the following? | **Supplement or enhance a task performed by an employee 43.7%** · Perform a task previously done by an employee **10.1%** · Introduce a new task not previously done 10.6% · None of the above 51.5% |
| Q6 | How did the use of AI affect this business's total employment? | **No change 95.7%** · Increased 2.3% · Decreased 2.0% |
| Q7 | To use AI, what changes did this business make? | **Developed new workflows 15.4%** · **Trained current staff to use AI 15.0%** · Cloud services 8.5% · Computing power / specialised equipment 8.2% · Changed data practices 6.8% · Used vendors or consulting to install/integrate 3.8% · **Hired staff trained in AI 1.3%** · No changes 64.3% |

And Q2 / Q12 — AI use **by business function** (15 options) — national "Yes" shares: **Sales and marketing 14.3%**, Strategy and business development 12.4%, Information technology 11.4%, Research and development 11.2%, Public relations and communication 9.3%, Management and administration 8.1%, Customer service 7.6%, Legal and compliance 7.1%, Finance and accounting 6.6%, Provision of services/products/merchandise 6.4%, Human resources 4.2%, Quality management and control 2.8%, Sourcing/supply chains/purchasing 2.6%, Production of goods 1.7%, Distribution 0.9%.

Q10 — **which work-related tasks employees used generative AI to assist with** (10 options): Writing or editing documents, emails, or communications **85.4%** · Searching for information or technical help 49.9% · Interpreting, analysing, translating, or summarising documents 44.6% · Information processing, paperwork, or filing 34.7% · Developing or researching new projects or processes 30.0% · Data analysis or visualisation 19.1% · Tutoring, training, or learning 16.1% · Customer support 15.5% · Software coding or debugging 12.7% · Other 6.1%.

### 3.4 Two numbers that matter for Vision B specifically

- **Sector 54 — Professional, Scientific, and Technical Services**, the NAICS sector Accenture sits in: **AI use 34.2%**, versus **17.9% nationally** — roughly **1.9×**. So "employers are not really using AI yet" is *not* available as an argument to defer Vision B. The binding question becomes *within-sector: which function*.
- **Within sector 54, AI use by function:** Research and development **24.0%**, Information technology **21.9%**, Strategy and business development **21.3%**, Provision of services **18.2%**, Sales and marketing **17.7%**, Legal and compliance 13.4%, Public relations and communication 13.1%, Management and administration 12.9%, Finance and accounting 11.7%, Customer service 10.0%, Human resources 5.8%.

### 3.5 How it connects to our data — and this is where honesty is required

**BTOS contains no occupation column. There is no SOC key, and no row-level join to the core data is possible.** The connection is a two-step, analyst-constructed bridge:

```text
step 1 (the decision's own vocabulary):
   BTOS business-function taxonomy (Q2/Q12, 15 functions)
        → Accenture service lines / role families            [analyst-built mapping, not a published crosswalk]

step 2 (the task layer):
   BTOS task categories (Q10, 10 categories)
        → O*NET IWA / task families used by the core data    [analyst-built mapping]
```

The consequence must be stated rather than hidden:

- A BTOS figure has **variance across sectors, states, firm-size buckets, and business functions**.
- It has **zero variance across occupations**. After any merge with an occupation-level table, its value is a constant repeated down every row — **and a constant cannot order rows.**
- Therefore BTOS **cannot rank role groups**, and it must never appear as a ranking column in the Vision-B shortlist.

What it *can* legitimately do for Vision B, and why it is still the right addition:

1. **Rank business functions — which is one level above role groups and is how Accenture actually organises its service lines.** The sector-54 function ranking in 3.4 is a defensible coarse prior for which *families* of roles deserve attention, even though it cannot resolve a specific occupation.
2. **Supply the employer-side counterpart to the core data's augmentation/automation measures.** Q3 splits "supplement or enhance an employee's task" (43.7%) from "perform a task previously done by an employee" (10.1%) — the same distinction the team's third open question asks about, observed from the employer's side rather than the assistant's.
3. **Supply the only permitted evidence on retraining behaviour and on employment effects** (Q7, Q6) — i.e. the only permitted source that can speak to what an "AI upskilling" investment actually is in practice.
4. **Function as a calibration and falsification layer:** if the shortlist claims professional-services roles are ripe for advanced upskilling, BTOS is the check that says whether firms in that sector are in fact using AI, in which functions, and whether they respond by training.

### 3.6 What new question it makes answerable

> Among U.S. employers that already use AI, do they augment employee tasks or replace them, do they retrain the staff they have or hire AI-trained staff, and did AI use change their headcount? — i.e. **what is the externally observed norm that an "advanced AI upskilling and workflow-redesign" pilot at Accenture would be an instance of?**

### 3.7 What could fail

1. **No occupation dimension at all.** Stated above; the single most important limitation. Any occupation-level claim drawn from BTOS would be an ecological inference from an industry statistic to a job — invalid without further assumptions.
2. **`XX` absorbs exactly the firms Vision B is about.** *Sourced from the workbook's own Data Dictionary:* `XX` = "multi-unit companies that operate in multiple sectors or multiple states." BTOS is a firm-level survey, and the About page repeats that such firms are labelled `XX` in published outputs. There are **85 `XX` rows in the State sheet alone.** A multi-state professional-services firm is therefore **structurally invisible at state level** — which means the California figures in the State sheet describe single-state employers, not the population Vision A might picture.
3. **Business counts, not workers.** Every estimate is a **share of businesses**, not an employment-weighted share. A 3-person firm and a 250+-employee firm count equally. For a *workforce* decision this is a real distortion, and the available size buckets stop at "250 or more", so Accenture-like firms share their bucket with firms a thousand times smaller.
4. **Suppression.** **490 cells are marked `S` in the State sheet** (and smaller-count cells appear in the sector sheet too, e.g. sector 11, Q2). Small states and small functions are censored, so the geographic picture is incomplete by construction.
5. **A vintage break sits inside our window.** The AI core question's wording changed effective **11/17/2025** — precisely the supplement's start date. Any time series built across that date mixes two question wordings and is not comparable; the supplement is a single pooled snapshot, not a trend.
6. **A single 12-week window.** *Sourced:* supplements pool all 6 panels (12 weeks) into one set of estimates. There is **no seasonality control and no revision** — BTOS explicitly does not revise — so one release is one sample, and a second release would be a second independent snapshot rather than an update.
7. **Voluntary, qualitative, categorical, self-reported.** Questions ask about fixed answer categories, not measured usage. "Use of AI" is whatever the respondent believed it to be, and Q1's national "Don't know" is a non-trivial **10.8%**.
8. **Disclosure protection shapes the file.** The workbook carries a DRB approval number (CBDRB-FY26-0278) and the State sheet embeds source/disclosure footer rows inside the data column, which will appear as junk categories unless filtered on load — a small but real cleaning requirement.
9. **Our bridge is judgement, not a crosswalk.** Steps 1 and 2 in 3.5 are mappings the team would author. Two analysts could produce different mappings, so the mapping must be documented and reviewed, and its fragility stated wherever a BTOS-derived number appears.

### 3.8 Synthetic fallback *(labelled — demonstrates a mechanism, provides no evidence)*

The real BTOS file exists and is opened. The input that genuinely does not exist anywhere in the permitted list is the **internal** half of Role 3's gap. So the synthetic artefact is a **7-row** table, one row per representative U.S. professional role group, with mixed provenance — real and synthetic columns clearly separated:

| Column | Provenance |
|---|---|
| `soc_code`, `occupation_title`, `observed_ai_exposure`, `task_penetration` | from the core data |
| `function_family` (mapped from BTOS Q2/Q12) | mapped from real BTOS |
| `employer_ai_use_function_share` (from BTOS sector 54) | real |
| `internal_role_headcount` | **`SYNTHETIC`** — no permitted source contains it; stands in for the HRIS pull |
| `internal_ai_adoption_share` | **`SYNTHETIC`** — stands in for the internal adoption measure |
| `priority_score` | computed, `SYNTHETIC` weights |

Marked `SYNTHETIC — illustrative only`. It demonstrates the mechanism the team would need (rank role groups by exposure × scale × adoption gap) and simultaneously makes the boundary visible: two of the columns exist only because a real organisation would have to supply them.

---

## 4. Considered and set aside — so the reasoning is visible

### 4.1 O\*NET database — not rejected, *already claimed*

O\*NET is the vocabulary both core sources already speak (Anthropic's `node_external_id` is defined as "O\*NET element ID, SOC code, or topic UUID" and its `onet` category is structured Task → DWA → IWA → GWA; OpenAI Signals carries `iwa_cleaned`). `technical.md` makes O\*NET the connective tissue of **both** Vision join paths. It is therefore a **taxonomy spine**, present in the project regardless of Role 4's choice. Role 4's slot is for a **decision input**, and O\*NET contains no worker count, no wage, and no employer behaviour — so spending one of the two permitted slots on it would buy structure we already have, not a missing fact.

*Carried forward in case Phase I needs it:* O\*NET 31.0 uses the O\*NET-SOC 2019 taxonomy with 1,016 occupations; `Task Statements` holds 18,838 occupation–task pairs; `Work Activities` 74,702 records; `Tasks to DWAs` 24,087 mappings. Licence CC BY 4.0 with an attribution and "has modified… / USDOL/ETA has not approved" statement requirement, and O\*NET® written as an adjective.

*One concrete trap already observed in the core data:* the first two rows of `task_penetration.csv` are `"Accept and check containers of mail from large volume mailers, couriers, and contractors."` and `"Accept and check containers of mail **or parcels** from large volume mailers, couriers, and contractors."` — two rows a human reads as one task and a string join reads as two. Any task-level join must go through element IDs, not task text.

### 4.2 BLS Employment Projections (2025–35, incl. the AI exposure categories) — the right *next* addition, not one of these two

Attractive because it is the only permitted source giving **direction** (growth) rather than level, and because its AI exposure categories supply a cross-source theoretical-exposure benchmark. Set aside **for now** for three reasons:

1. **It cannot serve Vision A**, whose binding constraint is geographic: EP projections are **national**. Pairing national direction with OEWS's California levels would produce a table that looks regional and is not.
2. **OVEWS and EP are complements, not competitors** — BLS lists projections under OEWS's "Data we do not have". Once OEWS is in, EP is the obvious Phase-I extension for *both* Visions, so it is better held in reserve than spent now.
3. **It overlaps the core data by construction**, which weakens it as an independent addition: *sourced* — BLS built its AI exposure categories from five inputs, and **Anthropic's Claude-based observed-exposure measure is one of them**. So EP's category partly *contains* our core data and is **not independent corroboration**. Used as "a second source that agrees" it would be a methodological error; the defensible use is a **normalised cross-source benchmark** adding a theoretical-exposure dimension the core data lacks.

*Also carried forward:* 831 detailed occupations classified into Low / Moderate / High / Very high; **211 of 4,155 occupation-source cells are imputed, affecting 75 occupations**. BLS states explicitly that the categories are **not** a forecast of employment growth or decline, **not** a wage forecast, **not** an adoption probability, **not** a replacement estimate, and **not** a productivity forecast; they are **relative** to other occupations, and they **do not distinguish automation from augmentation**. Turning "Very high" into a layoff flag or a risk score would misuse a published measure against its own documented scope.

### 4.3 Why Vision A did not get BTOS, and Vision B did not get OEWS

- **Vision A:** BTOS has **no occupation dimension**, so it cannot touch Role 3's first-ranked Vision-A gap. California appears in BTOS (CA: AI use **19.1%**, vs 17.9% nationally; 67.9% no; 13.0% don't know), so BTOS is *useful context* for Vision A — but it cannot produce a region × occupation row, which is the decision's unit. It belongs in Phase I as interpretation, not as the Vision-A input.
- **Vision B:** OEWS *does* have an occupation dimension, so it is not useless — but national and state employment/wage levels add **size**, and Role 3 already concluded that Vision B's core data can compare role groups and that what it lacks is **adoption and behaviour**. Between the two, the adoption/behaviour gap is the one that changes the decision.

---

## 5. Sourced facts vs. AI hypotheses vs. open questions

### Sourced facts

Read directly from the sources cited above, or measured in a file I opened:

- **Files opened this round:** `AI_Supplement_Table_2026.xlsx` (578,790 bytes, 9 sheets, row counts as listed in 3.3) — downloaded and parsed; the OEWS and BTOS *pages* — loaded; the OEWS *download paths* — probed and **refused with HTTP 403**.
- **BTOS:** sample of ~1.2 million businesses in 6 panels of ~200,000; biweekly collection; no revisions; supplements pooled over 6 periods; published at national, state, 2- and 3-digit sector, employment size class, top-25 MSA, and sector-by-size; multi-unit multi-state/multi-sector firms labelled `XX`; core AI question wording changed to "any of its business functions" from the 11/17/2025 collection.
- **All BTOS estimates quoted in Sections 3.3–3.4 and 4.3**, the `Scope` code definitions 1–6, the size buckets A–G, the Q1–Q13 question count and answer-option counts, the `XX` definition, and the 490 `S` cells in the State sheet.
- **OEWS:** annual estimates for ~830 occupations at national, state, and metropolitan/nonmetropolitan level plus national industry detail; May 2025 is the current release; SOC classification with 23 major groups; OEWS lists occupational projections, demographics, establishment size, job vacancies and self-employment under data it does not have; benefits excluded; the reason area sums do not equal state totals.
- **From the team's own files:** the verbatim Vision statements and every missing-data-element name in Section 1 (from `data-fit.md`); O\*NET file counts and licence terms, the BLS AI exposure category construction, the 831/4,155/211 figures, and the two near-duplicate `task_penetration.csv` task strings (carried over from `technical.md` and from the previous round of this file).

### AI-generated hypotheses (mine — to be investigated, not quoted as fact)

1. That a county → Regional Planning Unit crosswalk can be built defensibly from public county lists — **untested**; I have not verified how any specific California RPU is composed.
2. That BTOS's 15 business functions map onto Accenture service lines into a useful prior — plausible from the names, **not verified against Accenture's actual job architecture**.
3. That BTOS Q10's 10 task categories can be mapped to O\*NET IWA families with acceptable reliability — **hypothesis**; the two taxonomies were designed for different purposes and I have not measured the mapping.
4. That "exposure × employment × wage" is the right Vision-A ranking, rather than payroll or business criticality — **a weighting choice for the team**, not a finding.
5. That an employer-side augmentation share (Q3, 43.7%) and the core data's augmentation/automation measures will broadly agree — **untested**; they measure different populations (U.S. establishments vs Claude/ChatGPT messages).
6. That OEWS suppression will not remove a material share of the exposed occupations we care about — **unmeasured**; only a download can settle it.
7. That the `O_GROUP` field carries the detailed/broad/major distinction in the May 2025 files — **expected, unconfirmed**, since I could not open the file.

### Open questions requiring a real stakeholder or a further check

1. **Which California geography does Vision A's Executive Director actually decide in?** If the answer is "our 15 Regional Planning Units", the county crosswalk is mandatory and the OEWS metropolitan areas become an intermediate step. If it is "wherever the workers are", OEWS areas can be the unit directly.
2. **Will Accenture's actual role groups be disclosed for mapping, or must Vision B remain purely external?** This single answer decides whether Vision B is a screening tool or an investment recommendation — and `technical.md` reached the same fork from a different direction.
3. **Do we accept a source that cannot rank rows (BTOS) as one of our two permitted additions — or would the team rather spend Vision B's slot on BLS Employment Projections for its row-level growth and exposure-category columns?** This is a genuine trade-off: BTOS buys employer-side behaviour that nothing else has; EP buys a row-level ranking variable that joins cleanly on SOC. My recommendation is BTOS + EP deferred to Phase I, but the team should decide it consciously.
4. **What happens to the tool's output when BTOS says 95.7% of firms reported no employment change and firms trained current staff ~11× more often than they hired AI-trained staff (15.0% vs 1.3%)?** If the external norm is "train the staff you have", does that strengthen or weaken an exposure-ranked shortlist?

---

## 6. Self-check (handout 3.12.6) and what remains uncertain

| Check | Status |
|---|---|
| The selected project area appears at the top | Yes — Topic 7 |
| The A and B candidate Vision statements appear at the top | Yes — **verbatim from `data-fit.md`** |
| Both candidate Visions are investigated | Yes — one addition each: OEWS (A), BTOS (B) |
| Sourced facts are separated from AI hypotheses | Yes — Section 5, in three blocks |
| The file records what was checked and what remains uncertain | Yes — Sections 5 and this table |
| No claim goes beyond the observed data or verified sources | Yes — Section 1.2 states that Vision B's three most important gaps are unfillable from the permitted list rather than implying they were solved; Section 3.5 states that BTOS cannot rank rows |
| Two additions, not a long list | Yes — two spent, two in Section 4 with reasons |

**Checked:** the four permitted addition sources and their download listings; the Anthropic Economic Index data documentation and the headers of `job_exposure.csv` and `task_penetration.csv` (earlier round); the OpenAI Signals data dictionary; the O\*NET 31.0 file descriptions and licence terms; the BLS AI exposure categories publication and its stated limits; the OEWS tables page, FAQ, and download paths; the BTOS About page, data-download listings, `AI_Supplement_Table_2026.xlsx` in full structure, and its embedded data dictionary.

**Not checked / uncertain:** the body of any OEWS file (download paths returned 403 to automated requests, so the field list in 2.3 is *expected*, not confirmed); how California's RPUs are actually composed; whether the BTOS function list maps to Accenture service lines; whether the `XX` share of professional-services firms is large enough to make the sector-54 figures unrepresentative of large multi-state firms; the second BTOS AI supplement or any fuller multi-period series; whether a usable county → RPU crosswalk exists publicly.

**No dataset in this file was committed to the repository.** The BTOS workbook was downloaded to a local working directory only, for inspection.
