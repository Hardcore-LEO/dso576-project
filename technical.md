# Technical Path

## Selected Project Area

**Project 7: AI Workforce Investment Planner**  


## Candidate Vision A

The Executive Director of the California Workforce Development Board must decide which combinations of California regions and occupations should be prioritized for a proposed AI upskilling and workforce-transition pilot program.

## Candidate Vision B

The Chief Leadership and Human Resources Officer at Accenture must decide which representative U.S. professional role groups should be prioritized for a proposed round of advanced AI upskilling and workflow-redesign pilots.

## Technical Investigation Scope

This investigation checks whether the recommended public data can support the two candidate decisions. It focuses on data access, file formats, scale, join keys, minimum access tests, technical blockers, and a feasible first implementation. It does not assume that observed AI use causes job loss or that a high AI-use measure automatically supports automation.

Access checks in this document were completed on September 12, 2026.

## Verified Data Source Summary

| Source | Access and format | Verified content | Likely project use | Important limitation |
|---|---|---|---|---|
| [Anthropic Economic Index](https://huggingface.co/datasets/Anthropic/EconomicIndex) | Public Hugging Face repository; multiple CSV releases | The repository is approximately 664 MB in total. The smaller `labor_market_impacts` folder is approximately 1.93 MB and contains `job_exposure.csv` and `task_penetration.csv`. The initial 2025 release also contains O*NET task mappings and statements. | Occupation-level observed exposure, task penetration, and task-level AI-use patterns | Measures Claude use rather than all AI use. Releases differ, so the team must select and pin one release. |
| [OpenAI Signals](https://openai.com/signals/data-download/) | Public downloadable CSV package plus a 40-page data dictionary | The current package contains 25 CSV files. It includes monthly U.S. O*NET Intermediate Work Activity shares, state-level usage rankings, and state-level topic shares. | Cross-check work-activity patterns and broader ChatGPT usage | Consumer ChatGPT data excludes enterprise messages and Codex. Public files do not provide a direct California-region-by-occupation table. |
| [O*NET Database](https://www.onetcenter.org/database.html) | Public Excel, CSV, JSON, SQL, RDF, and web-service options | O*NET 31.0 describes occupations, tasks, Detailed Work Activities, skills, knowledge, work context, and related job characteristics. | Connect occupations to tasks, work activities, and training needs | O*NET-SOC and BLS SOC versions may not match perfectly; crosswalk checks are required. |
| [BLS OEWS](https://www.bls.gov/oes/tables.htm) | Public XLSX and text downloads | May 2025 files are available at national, state, metropolitan/nonmetropolitan, and industry levels. | Employment and wage weights for occupation prioritization | OEWS areas are not automatically identical to California Workforce Development Board regions. |
| [BLS Employment Projections](https://www.bls.gov/emp/) | Public national projection tables | BLS provides national 2025-2035 employment projections and occupational characteristics. | Add expected growth, openings, education, and training context | National projections do not directly provide California regional forecasts. |
| [Census BTOS](https://www.census.gov/hfp/btos/data_downloads) | Public download page, but the page requires JavaScript in the tested browser | Download page was located but individual files were not inspected in this first access test. | Possible business AI-adoption context by geography or industry | Join value and relevant fields remain unverified; treat this source as optional. |

## Licensing and Use Conditions

- **Anthropic Economic Index:** The repository documentation states that released data use a CC BY license and code uses the MIT License. Attribution is required for reused data.
- **OpenAI Signals:** The data download page states that Signals data use the Creative Commons Attribution 4.0 license. Attribution is required.
- **O*NET:** The O*NET license page states that most O*NET information uses CC BY 4.0. The team should check listed exceptions before redistribution.
- **BLS and Census:** The files are publicly accessible government data, but the team should still preserve source names, release dates, and links in the final project.
- No login was required to inspect the public source pages and file previews used for this investigation.

## First Access Tests

### Anthropic Economic Index

**Verified test:** The repository, release folders, and individual CSV previews opened successfully in a browser.

- `labor_market_impacts/job_exposure.csv` opened successfully.
- The file is approximately 37.2 KB.
- The preview showed the columns `occ_code`, `title`, and `observed_exposure`.
- Example occupation records included Financial Managers, Human Resources Specialists, Management Analysts, Accountants and Auditors, Computer Programmers, and Data Scientists.
- `labor_market_impacts/task_penetration.csv` is approximately 1.89 MB.
- The 2025-02-10 release is approximately 5.24 MB and contains `SOC_Structure.csv`, `onet_task_mappings.csv`, `onet_task_statements.csv`, BLS employment data, and wage data.
- `onet_task_mappings.csv` is approximately 461 KB and uses the columns `task_name` and `pct`.
- `onet_task_statements.csv` is approximately 3.59 MB.

**Technical conclusion:** The relevant subsets are small enough for pandas on a normal laptop. The full 664 MB repository is not necessary for the first prototype.

**Observed access issue:** The Hugging Face dataset viewer reported a configuration error involving a missing referenced file, although individual file pages and previews remained accessible. The team should use explicit file paths or download a selected release instead of relying on the automatic dataset viewer.

### OpenAI Signals

**Verified test:** The data download page and data dictionary opened successfully.

- The data dictionary describes 25 CSV files.
- Each row is a unique combination of time and grouping fields for a table.
- Metrics are generally `share_of_messages` or `rank`.
- The current methodology uses classifications of 300,000 consumer ChatGPT messages per month from July 2024 through June 2026.
- Relevant files include monthly U.S. O*NET IWA shares, monthly work-related O*NET IWA shares, state usage rankings, and 2025 state-level topic shares.
- O*NET IWA and other behavioral categories are model-inferred classifications, not self-reported attributes.
- The statistics use differential privacy and rounding.

**Technical conclusion:** The CSV package should be directly readable with pandas. However, its public aggregations do not directly connect a California region to a specific occupation, and they do not describe Accenture employees.

### O*NET and BLS

**Verified test:** O*NET tabular download options and current BLS OEWS tables opened successfully.

- O*NET offers CSV and Excel files suitable for pandas, as well as database and API options that are not necessary for the first prototype.
- BLS OEWS provides May 2025 state and metropolitan/nonmetropolitan XLSX files.
- BLS Employment Projections provides national 2025-2035 occupational projections.

**Technical conclusion:** CSV and XLSX files are sufficient. PostgreSQL, Supabase, cloud services, and a production API are not required at this stage.

## Candidate Vision A Technical Path

### Decision to Support

Prioritize combinations of California regions and occupations for a proposed AI upskilling and workforce-transition pilot.

### Recommended Starting Data

1. **Anthropic `job_exposure.csv`:** occupation-level observed AI exposure.
2. **Anthropic `task_penetration.csv` or task mappings:** evidence about work activities receiving AI use.
3. **O*NET task and work-activity files:** occupation-to-task structure and skill requirements.
4. **BLS OEWS California and metropolitan/nonmetropolitan files:** regional employment and wage measures.
5. **BLS Employment Projections:** national growth and openings as contextual indicators.
6. **OpenAI Signals:** supporting evidence for U.S. work-activity use and California-level topic patterns, not a direct region-occupation measure.

### Proposed Join Path

```text
Anthropic occupation code
        -> SOC or O*NET-SOC crosswalk
        -> O*NET occupation and task records
        -> BLS OEWS occupation code and California area
        -> occupation-region prioritization table
```

The main intended join key is the SOC occupation code. Before merging, the team must standardize code formatting, confirm the taxonomy year, identify detailed versus broad occupation levels, and document any many-to-one crosswalks.

### Proposed Unit of Analysis

One row in the analytical table should represent:

> One occupation in one defined California geographic area.

Possible columns include:

- `area_code` and `area_name`
- `soc_code` and `occupation_title`
- employment level
- mean or median wage
- observed AI exposure
- task penetration or work-activity indicator
- projected growth or openings, if a compatible measure is available
- final priority score and component scores

### Feasibility

**Initial assessment: feasible with conditions.** The occupation-level and California area-level files are public and small enough for pandas. The main technical work is taxonomy alignment and the definition of a California region.

### Blockers and Next Checks

- The team must define whether “California regions” means metropolitan/nonmetropolitan OEWS areas, counties, Local Workforce Development Areas, or another CWDB regional structure.
- If CWDB regions are used, a defensible geographic crosswalk from each region to counties or BLS areas is required.
- National BLS projections should not be presented as California regional forecasts.
- OpenAI Signals does not directly provide a region-by-occupation measure.
- A priority score requires team-approved weights; technical convenience should not determine policy weights.
- High exposure may support training or redesign, but does not by itself justify automation.

### Initial Recommendation for Vision A

Build the first prototype with Anthropic occupation exposure, O*NET tasks, and BLS California employment and wage data. Use metropolitan/nonmetropolitan OEWS areas as the initial geographic unit unless the team finds a reliable CWDB-to-county crosswalk. Add OpenAI Signals as supporting context rather than the primary ranking variable.

## Candidate Vision B Technical Path

### Decision to Support

Prioritize representative U.S. professional role groups for advanced AI upskilling and workflow-redesign pilots at Accenture.

### Recommended Starting Data

1. **Anthropic occupation exposure and task penetration:** identify professional occupations and tasks with observed Claude use.
2. **OpenAI Signals O*NET IWA files:** identify work activities appearing in U.S. work-related ChatGPT use.
3. **O*NET occupations, tasks, skills, and work activities:** describe the work content and possible training needs of selected professional roles.
4. **BLS national employment, wages, and projections:** provide external labor-market importance and growth context.

### Proposed Join Path

```text
Selected professional SOC groups
        -> O*NET occupations, tasks, and skills
        -> Anthropic exposure and task-use measures
        -> OpenAI O*NET IWA trends
        -> BLS national employment, wages, and projections
        -> external screening table for pilot candidates
```

### Proposed Unit of Analysis

One row in the first public-data prototype should represent:

> One representative U.S. professional occupation or role group.

Possible columns include:

- SOC or O*NET-SOC code
- occupation or role-group name
- observed AI exposure
- task penetration or IWA share
- important tasks and skills
- national employment and wage measures
- projected growth or openings
- proposed intervention category: training, workflow redesign, further review, or no current recommendation

### Feasibility

**Initial assessment: feasible only as an external prototype.** Public data can rank representative U.S. occupations, but it cannot determine actual Accenture pilot priorities without internal workforce and process information.

### Additional Internal Data Needed

- Accenture role taxonomy and mapping to SOC or O*NET occupations
- U.S. employee headcount by role group
- current AI proficiency and training completion
- task frequency and time allocation
- current tool access and adoption
- workflow quality, error, and rework measures
- client confidentiality and regulatory risk levels
- training cost, implementation cost, and expected benefit
- employee and manager feedback

### Blockers and Next Checks

- Public occupational categories may not align with Accenture job families.
- OpenAI Signals excludes enterprise messages and therefore does not measure Accenture usage.
- Anthropic data measures Claude usage and may not represent all tools used by Accenture employees.
- The public data cannot estimate company-specific ROI, readiness, risk, or implementation cost.
- Workflow redesign and automation require task-level risk review, not only occupation-level exposure.
- Any real deployment recommendation would require internal approval, privacy review, and human oversight criteria.

### Initial Recommendation for Vision B

Present the public-data output as an external screening tool that identifies role groups for further internal assessment. Do not describe the result as a final Accenture investment recommendation. If internal data cannot be obtained, label all Accenture-specific conclusions as hypotheses.

## Comparison of the Two Technical Paths

| Criterion | Vision A | Vision B |
|---|---|---|
| Public-data coverage | Stronger | Moderate |
| Geographic requirement | California region plus occupation | U.S. role group |
| Main technical challenge | Geographic and occupational crosswalks | Mapping public occupations to Accenture roles |
| Need for private data | Helpful but not essential for a prototype | Essential for a real company recommendation |
| Suitable first output | California occupation-region priority table | External professional-role screening table |
| Initial technical recommendation | Preferred for the semester prototype | Keep as a comparison vision or clearly labeled prototype |

## Recommended Minimum Viable Technical Stack

- Python
- pandas
- Jupyter Notebook or VS Code
- CSV and XLSX source files
- Optional visualization with matplotlib, seaborn, or Plotly
- GitHub for code and Markdown only

The first prototype does not require PostgreSQL, Supabase, cloud deployment, a live API, or a machine-learning model.

## Proposed Small Local Validation

After downloading only the selected small files, the team can run a basic pandas check:

```python
import pandas as pd

job_exposure = pd.read_csv("job_exposure.csv", dtype={"occ_code": "string"})

print(job_exposure.shape)
print(job_exposure.columns.tolist())
print(job_exposure.head())
print(job_exposure["occ_code"].str.len().value_counts(dropna=False))
print(job_exposure["occ_code"].duplicated().sum())
print(job_exposure["observed_exposure"].describe())
```

The same validation should be repeated for each selected O*NET and BLS file before any merge. The team should preserve occupation codes as strings so leading zeros and formatting are not lost.

## Verified Facts, Hypotheses, and Unresolved Questions

### Verified Facts

- The recommended Anthropic, OpenAI, O*NET, and BLS source pages are publicly accessible.
- Anthropic provides occupation- and task-related CSV files.
- OpenAI Signals provides 25 aggregated CSV files and includes U.S. O*NET IWA measures.
- O*NET provides occupation, task, skill, and work-activity data in several downloadable formats.
- BLS OEWS provides state and metropolitan/nonmetropolitan employment and wage files.
- The selected data subsets are compatible with a pandas-based prototype.

### Hypotheses to Test

- Occupations with higher observed AI exposure and larger employment may be stronger candidates for AI training investment.
- Tasks associated with iterative or collaborative AI use may be better candidates for workflow redesign than full automation.
- Combining exposure, employment, wages, growth, and task characteristics may produce a more useful screening tool than ranking by exposure alone.
- These hypotheses are not causal conclusions and require stakeholder-approved definitions and weights.

### Unresolved Questions

1. What exact geographic definition should Vision A use for a California region?
2. Which Anthropic release should be frozen for the project, and which exposure measure best matches the decision?
3. How will the team reconcile O*NET-SOC and BLS SOC taxonomy differences?
4. What weighting method will convert the indicators into a transparent priority score?
5. Can any credible Accenture-specific workforce data be obtained, or must Vision B remain an external prototype?
6. What human-review and risk criteria should prevent the tool from recommending inappropriate automation?

## Overall Technical Recommendation

Vision A is the stronger starting point because the public sources can support an occupation-by-California-area prototype without private employer data. Vision B is still useful for comparison, but it should be framed as an external screening exercise unless the team obtains Accenture role, workforce, workflow, and cost data. The team should begin with small CSV and XLSX files, validate join keys in pandas, document unmatched records, and delay database or deployment decisions until the merged prototype is proven.

## Source Links

- [Anthropic Economic Index repository](https://huggingface.co/datasets/Anthropic/EconomicIndex)
- [Anthropic labor market impacts folder](https://huggingface.co/datasets/Anthropic/EconomicIndex/tree/main/labor_market_impacts)
- [Anthropic initial O*NET-linked release](https://huggingface.co/datasets/Anthropic/EconomicIndex/tree/main/release_2025_02_10)
- [OpenAI Signals data download and license](https://openai.com/signals/data-download/)
- [OpenAI Signals data dictionary](https://cdn.openai.com/signals/data-dictionary.pdf)
- [O*NET Database](https://www.onetcenter.org/database.html)
- [O*NET License Agreements](https://www.onetcenter.org/license_agreements.html)
- [BLS OEWS tables](https://www.bls.gov/oes/tables.htm)
- [BLS Employment Projections](https://www.bls.gov/emp/)
- [Census BTOS downloads](https://www.census.gov/hfp/btos/data_downloads)
