# Data Fit

## Selected Project Area

AI Workforce Investment

## Candidate Vision A

The Executive Director of the California Workforce Development Board must decide which California regions and occupations should be prioritized for a new AI upskilling and workforce-transition pilot program.

## Candidate Vision B

The Chief Leadership and Human Resources Officer at Accenture must decide which representative U.S. professional role groups to prioritize for the next round of advanced AI upskilling and workflow-redesign pilots.

---

## 1. Core Data Overview

### OpenAI Signals

OpenAI Signals provides aggregated statistics on consumer ChatGPT usage from July 2024 to June 2026. The release contains 25 CSV files covering dimensions such as work-related usage, interaction intent, topic, geography, plan type, demographics, and O*NET Intermediate Work Activities (IWAs).

Each row is an aggregated observation for a specific combination of time and grouping variables, such as month × work activity or month × interaction type. Most tables report the share of messages within that group, while some geographic adoption tables report relative rankings.

The most relevant data for our project include:

| Table | Columns | Description |
|---|---|---|
| `usa_share_of_work_related_messages_`<br>`by_onet_iwa_month.csv` | `month`, `iwa_cleaned`, `share_of_messages` | Monthly share of work-related U.S. ChatGPT messages by O*NET IWA; useful for identifying AI-relevant work activities and trends. |
| `usa_share_of_messages_`<br>`by_onet_iwa_month.csv` | `month`, `iwa_cleaned`, `share_of_messages` | Monthly distribution of all U.S. ChatGPT messages across O*NET IWAs. |
| `share_of_messages_by_work_related_`<br>`ask_do_express_month.csv` | `month`, `work_related`, `ask_do_express`, `share_of_messages` | Distinguishes work-related and non-work-related messages and classifies them as Asking, Doing, or Expressing. |
| `usa_share_of_messages_`<br>`by_state_2025_rank.csv` | `year`, `state_code`, `state_name`, `rank` | Provides the relative ranking of U.S. states in ChatGPT adoption in 2025. |
| `usa_share_of_messages_`<br>`by_topic_state_2025.csv` | `year`, `state_code`, `state_name`, `topic`, `share_of_messages` | Shows how ChatGPT usage is distributed across topics within each U.S. state in 2025. |

The O*NET IWA tables are especially relevant because they connect observed ChatGPT usage with standardized work activities that can later be linked to occupations. The state-level tables provide geographic context for Vision A, while the Asking/Doing/Expressing table helps distinguish different patterns of AI use. However, these data describe aggregated consumer ChatGPT activity rather than individual workers or firms, and they do not directly observe organization-specific AI use.

### Anthropic Economic Index

Each row in the Economic Index files represents one metric value for a specific combination of time period, geography, analysis category, hierarchy node, and metric.

The Anthropic datasets most relevant to our project are:

| Table | Columns | Description |
|---|---|---|
| `aei_claude_ai_2026-06-26.csv` | `date_start`, `date_end`, `geo_id`, `geo_level`, `category_name`, `hierarchy_level`, `metric_id`, `value`, `node_name`, `node_external_id` | Contains Claude.ai usage aggregated for April and May 2026 across global, country, and subregion levels. Relevant categories include `onet` for tasks and work activities and `soc_occupation` for occupations. Useful metrics include AI autonomy, human and AI-assisted task time, automation, augmentation, and work-related use. |
| `aei_1p_api_2026-06-26.csv` | `date_start`, `date_end`, `geo_id`, `geo_level`, `category_name`, `hierarchy_level`, `metric_id`, `value`, `node_name`, `node_external_id` | Contains first-party API usage for the same release period at the global level. It provides comparable task-, occupation-, and collaboration-related metrics for API-based AI use. |
| `job_exposure.csv` | `occ_code`, `title`, `observed_exposure` | Provides one row per occupation with an occupation code, occupation title, and observed AI exposure measure. Useful for comparing AI exposure across occupations. |
| `task_penetration.csv` | `task`, `penetration` | Provides one row per work task with a task-level AI penetration measure. Useful for identifying which specific work tasks show greater observed AI use. |

The June 2026 Economic Index files are especially useful because they provide task- and occupation-level evidence on how AI is used, including whether human-AI interaction is more consistent with augmentation or automation. The `job_exposure` and `task_penetration` tables provide additional occupation- and task-level measures that can support prioritization in both candidate Visions.

---

## 2. Vision A: Data Fit

### Candidate Vision A

The Executive Director of the California Workforce Development Board must decide which California regions and occupations should be prioritized for a new AI upskilling and workforce-transition pilot program.

### What the Core Data Can Support

The core data can provide useful evidence on which occupations and work activities appear more affected by or engaged with generative AI.

OpenAI Signals provides observed ChatGPT usage across O*NET Intermediate Work Activities (IWAs). This can help identify which types of work activities are more represented in work-related AI use and how those patterns change over time.

Anthropic adds more detailed occupation- and task-level evidence. `job_exposure.csv` allows occupations to be compared by observed AI exposure, while `task_penetration.csv` identifies specific tasks with greater AI penetration. The June 2026 Economic Index also provides measures such as augmentation, automation, and AI autonomy, which can help distinguish different types of AI impact.

For Vision A, these measures could help identify occupations that warrant further evaluation for AI upskilling or workforce-transition planning. For example:

- Higher AI exposure combined with higher augmentation may suggest stronger potential for AI upskilling.
- Higher AI exposure combined with stronger automation signals may suggest a greater need to evaluate workflow changes or workforce-transition risks.

The OpenAI state-level tables can also provide general context on AI adoption and usage patterns in California relative to other U.S. states.

### What Is Only Partly Supported

The main limitation is the regional component of the Vision.

The core data can provide occupation- and task-level AI signals, but they do not directly observe AI use for specific occupations within individual California regions. For example, the data cannot directly compare AI usage among Financial Analysts in Los Angeles with Financial Analysts in Sacramento.

Therefore, the core data alone cannot directly identify the highest-priority California region × occupation combinations.

### Important Information Not Observed

Although the core data provide useful occupation- and task-level AI signals, several additional data elements are needed to translate those signals into California-specific workforce investment priorities.

| Decision Need | Missing Data Element | Why It Matters for Vision A |
|---|---|---|
| Identify where affected workers are concentrated | `regional_occupation_employment` | Vision A requires prioritizing region × occupation combinations. A highly AI-exposed occupation may deserve more attention in regions where it employs a large number of workers. |
| Assess the economic importance of affected occupations | `regional_occupation_wage` | Wage levels help distinguish occupations with different economic significance and potential workforce impact when allocating limited pilot resources. |
| Understand future workforce demand | `regional_employment_growth` | A growing occupation with increasing AI exposure may require a different workforce response from an occupation that is already declining. |
| Determine who actually needs upskilling | `worker_ai_skill_level` | High AI exposure does not necessarily mean workers lack AI skills. Current skill levels are needed to determine whether additional training is actually necessary. |
| Match training with labor-market demand | `employer_ai_skill_demand` | Training is more valuable when the skills being taught match real employer demand for AI capabilities in the regional labor market. |
| Evaluate pilot feasibility | `training_availability_cost` | Even if a region has strong workforce needs, limited training capacity or high implementation costs may affect whether it is practical for the pilot. |
| Evaluate potential benefits | `productivity_change` | Higher AI use does not necessarily imply higher productivity. Productivity outcomes are needed to assess whether upskilling could generate meaningful economic benefits. |
| Evaluate workforce-transition risk | `worker_displacement` | AI exposure or automation signals do not show whether workers are actually losing jobs or experiencing job restructuring. This matters because Vision A includes workforce transition, not only upskilling. |

The most important gap for Vision A is `regional_occupation_employment`, because the core data do not directly identify where highly AI-exposed occupations are concentrated within California. `worker_ai_skill_level` and `employer_ai_skill_demand` are also important because high AI exposure alone does not indicate whether workers actually need additional training.

### Association vs. Causation

The core data mainly support descriptive comparisons and associations.

The data can support claims such as:

- Some occupations show higher observed AI exposure than others.
- Some work activities appear more frequently in observed AI usage.
- Some occupations show stronger augmentation or automation patterns.

With additional regional labor-market data, the analysis could also identify California regions with larger concentrations of workers in highly AI-exposed occupations.

However, the data cannot establish that:

- AI exposure causes job displacement.
- AI training causes higher productivity or wages.
- A region with more AI-exposed workers will benefit more from an upskilling program.
- Higher automation signals mean that a task should actually be automated.

These outcomes are not directly observed in the core data.

### Preliminary Data-Fit Assessment

**Supported**
- Comparing occupations by observed AI exposure
- Identifying AI-relevant work activities and tasks
- Distinguishing augmentation-oriented and automation-oriented AI use
- Providing broad California-level AI adoption context

**Partly Supported**
- Prioritizing California regions
- Estimating which regional workforces may face greater AI-related change

These require additional regional occupation and labor-market data.

**Outside the Core Data's Scope**
- Predicting the causal impact of AI on employment
- Estimating the actual effect of an AI training program
- Measuring worker-level AI skills or readiness
- Determining the exact return on investment of a workforce-transition pilot

### Overall Assessment

Vision A has a relatively strong fit with the core data at the occupation and work-activity level. The main gap is geographic: the core data do not directly measure AI use by occupation within California regions. Additional regional labor-market data would therefore be needed to convert occupation-level AI signals into region-specific workforce investment priorities.

---

## 3. Vision B: Data Fit

### Candidate Vision B

The Chief Leadership and Human Resources Officer at Accenture must decide which representative U.S. professional role groups to prioritize for the next round of advanced AI upskilling and workflow-redesign pilots.

### What the Core Data Can Support

The core data can provide external evidence on which professional roles and work activities are most affected by generative AI and how AI is changing the way those tasks are performed.

OpenAI Signals shows how U.S. ChatGPT usage is distributed across O*NET Intermediate Work Activities (IWAs), helping identify professional activities in which generative AI is already used more frequently.

Anthropic provides more detailed occupation- and task-level evidence. `job_exposure.csv` can identify role groups with higher observed AI exposure, while `task_penetration.csv` can reveal which specific tasks within those roles show stronger AI penetration. Measures of augmentation, automation, and AI autonomy can further indicate whether AI is being used mainly to assist workers or to perform larger portions of a task.

For Vision B, these signals are especially useful for distinguishing between two possible investment needs:

- Roles with high AI exposure and strong augmentation patterns may be stronger candidates for advanced AI upskilling.
- Roles containing tasks with stronger automation or autonomy signals may be stronger candidates for workflow-redesign analysis.
- Task-level evidence can help identify which parts of a professional role should be examined, rather than assuming that an entire occupation should receive the same intervention.

### What Is Only Partly Supported

The main limitation is the Accenture-specific component of the Vision.

The core data can identify occupations and tasks that appear more exposed to or engaged with AI in the broader economy, but they do not directly observe Accenture's internal workforce, job families, workflows, or AI adoption.

For example, the data may indicate that a particular O*NET occupation has relatively high AI exposure, but they cannot show:

- how many Accenture employees perform similar work;
- how that occupation maps to Accenture's internal job families;
- whether those employees already use AI extensively;
- which business units or teams would benefit most from additional training or workflow redesign.

Therefore, the core data can help generate and compare candidate professional role groups, but they cannot directly determine Accenture's final internal investment priorities.

### Important Information Not Observed

Although the core data provide useful occupation- and task-level AI signals, additional organization-specific data would be needed to translate those signals into Accenture workforce investment priorities.

| Decision Need | Missing Data Element | Why It Matters for Vision B |
|---|---|---|
| Identify which roles matter most within Accenture | `internal_role_headcount` | A highly AI-exposed occupation may not be a major workforce segment at Accenture. Role-group size is needed to understand the scale of the potential training or redesign opportunity. |
| Map external occupations to Accenture roles | `internal_role_mapping` | O*NET occupations do not directly correspond to Accenture's internal job families. A mapping is needed before occupation-level AI signals can be applied to Accenture roles. |
| Determine current AI adoption | `internal_ai_usage_by_role` | High external AI exposure does not show whether Accenture employees in that role already use AI extensively or still have substantial adoption gaps. |
| Identify actual training needs | `employee_ai_skill_level` | Employees in a highly exposed role may already have advanced AI skills. Current skill levels are needed to determine whether additional upskilling is necessary. |
| Identify workflows suitable for redesign | `internal_workflow_task_data` | External task-level signals do not show how work is actually organized inside Accenture. Internal workflow data are needed to identify which processes could realistically be redesigned. |
| Evaluate business impact | `internal_productivity_outcomes` | AI exposure, autonomy, and task-time metrics do not directly measure productivity gains within Accenture. Internal outcomes are needed to estimate the value of an intervention. |
| Evaluate governance constraints | `workflow_risk_requirements` | Some tasks may involve client confidentiality, compliance, or human-review requirements that limit how far automation can be applied. |
| Evaluate pilot feasibility | `training_and_implementation_cost` | Training capacity, implementation cost, and organizational readiness affect whether a role group is practical for the next pilot round. |

The most important gaps for Vision B are `internal_role_mapping`, `internal_role_headcount`, and `internal_ai_usage_by_role`. Without these, the core data can identify externally promising occupations and tasks but cannot determine which role groups should actually be prioritized inside Accenture.

### Association vs. Causation

The core data mainly support descriptive comparisons and associations.

The data can support claims such as:

- Some occupations show higher observed AI exposure than others.
- Some professional work activities appear more frequently in observed AI usage.
- Some occupations and tasks show stronger augmentation or automation patterns.
- Certain role groups may therefore warrant further evaluation for training or workflow redesign.

However, the data cannot establish that:

- Higher AI exposure causes higher productivity.
- Advanced AI training will improve employee performance.
- Stronger automation signals mean that Accenture should automate a task.
- A role with higher external AI exposure will generate greater returns from an Accenture pilot.
- Workflow redesign will reduce costs or improve client outcomes.

These outcomes are not directly observed in the core data and would require organization-specific outcome data or a stronger causal research design.

### Preliminary Data-Fit Assessment

**Supported**
- Comparing occupations and work activities by observed AI exposure
- Identifying tasks with higher AI penetration
- Distinguishing augmentation-oriented and automation-oriented AI-use patterns
- Using external occupational evidence to identify candidate professional role groups

**Partly Supported**
- Prioritizing representative U.S. professional role groups for Accenture
- Identifying workflows that may be suitable for redesign
- Estimating which role groups may have greater upskilling needs

These require additional mapping between external occupation data and Accenture's internal workforce and workflows.

**Outside the Core Data's Scope**
- Determining actual AI skill gaps among Accenture employees
- Measuring the causal effect of AI training on employee productivity
- Estimating the ROI of an Accenture training or workflow-redesign pilot
- Determining whether specific Accenture tasks should be automated
- Measuring organization-specific client, productivity, or workforce outcomes

### Overall Assessment

Vision B has a strong fit with the core data for identifying externally observed occupation- and task-level AI patterns. The main limitation is organization specificity: the core data do not directly observe Accenture's employees, job families, workflows, or internal AI adoption. Therefore, the data are well suited for generating and comparing candidate role groups, but additional Accenture-specific information would be required for final investment prioritization.

---

## 4. Data-Fit Comparison

| Dimension | Vision A | Vision B |
|---|---|---|
| Decision focus | Prioritize California regions and occupations for AI upskilling and workforce transition | Prioritize representative U.S. professional role groups for advanced AI upskilling and workflow redesign |
| Strongest fit with core data | Occupation- and task-level AI exposure, usage, augmentation, and automation patterns | Occupation- and task-level AI exposure, augmentation, automation, and workflow-related signals |
| Main data gap | The core data do not directly observe AI exposure by occupation within individual California regions | The core data do not directly observe Accenture's workforce, internal job families, workflows, or AI adoption |
| Most important additional data | Regional occupation employment and labor-market data | Accenture role mapping, role headcount, and internal AI-use or skill data |
| What the core data can support | Identifying occupations and tasks that may deserve greater workforce attention | Identifying professional role groups and tasks that may deserve further upskilling or workflow-redesign analysis |
| What the core data cannot determine | Which California region × occupation combinations will benefit most from a pilot | Which Accenture role groups will actually generate the greatest benefit from training or workflow redesign |

Based on the current data fit, Vision A appears more directly feasible because its main geographic gap could potentially be addressed with public regional labor-market data. Vision B is also well aligned with the occupation- and task-level AI data, but final prioritization would depend more heavily on organization-specific information that is not contained in the core datasets.