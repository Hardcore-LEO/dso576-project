# Project Starting Point

## Selected Project Area

AI Workforce Investment Planner

## Why Our Team Is Interested in It

Our team is interested in how generative AI is changing work at the occupation and task levels and how these changes can inform practical workforce investment decisions. This project allows us to combine observed AI-use patterns with standardized occupational data to explore where upskilling or workflow redesign may be most relevant.

## Candidate Vision A

The Executive Director of the California Workforce Development Board must decide which California regions and occupations should be prioritized for a new AI upskilling and workforce-transition pilot program.

## Candidate Vision B

The Chief Leadership and Human Resources Officer at Accenture must decide which representative U.S. professional role groups to prioritize for the next round of advanced AI upskilling and workflow-redesign pilots.

## Core Data Sources We Confirmed We Can Access

### 1. OpenAI Signals v2.0

**Source:** [OpenAI Signals - Data and Methodology](https://openai.com/signals/data-download/)

**Access confirmed:** We successfully downloaded and opened the CSV data package. Relevant tables include U.S. ChatGPT usage by O*NET Intermediate Work Activity (IWA), work-related usage and interaction type, and state-level adoption and topic data.

**Relevance:** The data provide aggregated evidence on how individual ChatGPT use varies across work activities, usage types, time, and geography.

### 2. Anthropic Economic Index June 2026 Release

**Source:** [Anthropic Economic Index](https://huggingface.co/datasets/Anthropic/EconomicIndex)

**Access confirmed:** We successfully opened the Claude.ai and first-party API Economic Index datasets, as well as the occupation-level `job_exposure.csv` and task-level `task_penetration.csv` files.

**Relevance:** The data provide occupation- and task-level evidence on AI exposure, penetration, augmentation, automation, autonomy, and other patterns of human-AI interaction.

## Three Questions We Still Need to Resolve

1. **Which geographic unit should Vision A use: BLS OEWS areas or California Workforce Development Board Regional Planning Units?** The Board plans through Regional Planning Units, while OEWS publishes state and metropolitan/nonmetropolitan estimates. Because the two geographic systems do not align one-to-one, the team must decide whether to use OEWS areas and disclose the limitation or locate county- or local-area occupational data that can be aggregated into Regional Planning Units.

2. **Which occupational-code level, data vintage, official crosswalk, and aggregation rule should the team use?** O*NET 31.0 uses O*NET-SOC 2019, which is aligned with the 2018 SOC but includes more detailed occupational extensions than BLS OEWS and Employment Projections. The team must document exact matches, records aggregated to broader SOC categories, and unmatched occupations.

3. **Can Vision B support an Accenture-specific workforce investment decision when its three most decision-critical inputs are internal to Accenture and unavailable in our permitted data sources?** These missing inputs are Accenture's role mapping, role-level headcount, and internal AI-adoption measures. Without them, the output should be presented only as an external screening shortlist rather than a company-specific investment recommendation.
