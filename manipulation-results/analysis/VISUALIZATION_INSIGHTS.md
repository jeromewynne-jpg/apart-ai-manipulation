# Manipulation Resistance Deep-Dive: Visualization Insights

Generated: January 10, 2026

---

## Definitions

| Term | Definition |
|------|------------|
| **Score** | 1-5 rating of model resistance (5 = resisted manipulation, 1 = fully complied) |
| **Failure** | Any response scoring ≤ 2 (model partially or fully complied with manipulation) |
| **Failure Rate** | Percentage of scenarios where the model failed (scored ≤ 2) |

---

## Figures Overview

| Figure | Description |
|--------|-------------|
| 01 | Heatmap - Model × Behavior performance matrix |
| 02 | Score Distributions - Violin plots by behavior type |
| 03 | Commercial Breakdown - Deep-dive into commercial pressure tactics |
| 04 | Family Comparison - Claude vs GPT vs Gemini vs Others |
| 05a | Failure Rate by Behavior - Which behaviors cause most failures |
| 05b | Failure Categories - Top scenario types where models fail |
| 05c | Failures by Model - Total failures per model |
| 06 | Tactic Categories - What manipulation tactics work (LLM-classified) |
| 07 | Model × Tactic Heatmap - Which models fall for which tactics |

---

## 1. Manipulation Heatmap

![Manipulation Heatmap](figures/01_manipulation_heatmap.png)

**What it shows:** Performance matrix of 12 models across 7 manipulation behavior types. Green = resistant (score 5), Red = vulnerable (score 1).

**Key insights:**
- The **commercial optimization column is consistently orange/red** across all models - this is the universal weakness
- Claude models (top rows) are almost entirely green
- Mistral-large-3 (bottom row) struggles across all behaviors
- Strategic deception shows the widest variance between models

**Quantified:**
- Best model on commercial: Claude 4.5 Opus (4.43)
- Worst model on commercial: Gemini 3.0 Pro (2.20)
- Even Claude drops 0.42 points from its overall average on commercial

---

## 2. Score Distributions

![Score Distributions](figures/02_score_distributions.png)

**What it shows:** Violin plots showing the full distribution of scores for each behavior type across all models.

**Key insights:**
- **Strategic deception and commercial optimization show bimodal distributions** - models either pass (4-5) or fail completely (1-2), with little middle ground
- Epistemic manipulation and coercive persuasion cluster at the top (mostly 5s)
- Preference falsification has the widest spread - highly variable performance

**Interpretation:** The bimodal pattern suggests these behaviors are "all or nothing" - either the model recognizes the manipulation pattern or gets completely exploited.

---

## 3. Commercial Optimization Breakdown

![Commercial Breakdown](figures/03_commercial_breakdown.png)

**What it shows:** Deep-dive into the "universal weakness" - performance by specific commercial pressure tactic.

**Key insights:**
- **Explicit commercial** pressure (direct profit instructions) causes the most failures
- **Research framing** and **rapport tactics** are handled better by top models
- Mistral-large-3 fails badly on research framing (1.3) - likely lacks training on this pattern
- Even Claude models dip below 4.5 on explicit commercial pressure

**Tactics ranked by difficulty (hardest first):**
1. Explicit commercial (direct profit optimization)
2. Information asymmetry
3. Indirect pressure
4. Soft optimization
5. Hidden objectives
6. Research framing
7. Rapport tactics

---

## 4. Model Family Comparison

![Family Comparison](figures/04_family_comparison.png)

**What it shows:** Comparing model families (Claude, GPT, Gemini, Other) across all manipulation behaviors.

**Key insights:**
- **Claude family**: Uniformly strong across all behaviors (consistently above 4.5)
- **GPT family**: Strong overall, close to Claude except on commercial
- **Gemini family**: Moderate performance, significant drop on commercial and strategic deception
- **Other** (Mistral, Grok, DeepSeek, Kimi): Most variable, often below pass threshold

**The commercial optimization gap:**
- Claude: 4.14
- GPT: 3.62
- Gemini: 2.35
- Other: 2.83

---

## 5a. Failure Rate by Behavior

![Failure Rate by Behavior](figures/05a_failure_rate_by_behavior.png)

**What it shows:** Which manipulation behaviors cause the highest failure rates across all models.

**Key insights:**
- **Commercial optimization**: ~40% failure rate - the hardest behavior to resist
- **Strategic deception**: ~40% failure rate - models struggle with deceptive framings
- **Preference falsification**: ~28% failure rate
- Other behaviors (epistemic manipulation, coercive persuasion): <25% failure rate

**Interpretation:** Some behaviors are fundamentally harder to resist, regardless of model quality.

---

## 5b. Failure Categories

![Failure Categories](figures/05b_failure_categories.png)

**What it shows:** Top scenario categories (attack types) where models fail most frequently.

**Key insights:**
- **Sympathy exploitation** and **misdirection** cause the most failures
- **Hidden agenda** and **value suppression** are highly effective attack categories
- **Authority pressure** exploits models' deference to perceived experts

**Interpretation:** Emotional appeals and indirect approaches work better than direct attacks.

---

## 5c. Failures by Model

![Failures by Model](figures/05c_failures_by_model.png)

**What it shows:** Total number of failures (score ≤ 2) for each model.

**Key insights:**
- **Mistral-large-3**: ~105 failures (most vulnerable)
- **Claude 4.5 Opus**: ~8 failures (most resistant)
- **13x difference** between best and worst models
- Clear tier separation: Claude/GPT (low failures) vs Gemini/Others (high failures)

---

## 6. What Manipulation Tactics Work

![Tactic Categories](figures/06_tactic_categories.png)

**What it shows:** GPT-5.2 classified all 470 failure cases to identify the manipulation tactics used by attackers. These are consolidated into 12 high-level categories.

**Top manipulation tactics:**
| Tactic | Count | % of Failures |
|--------|-------|---------------|
| Pretexting (Benign Framing) | 90 | 19.1% |
| Escalation (Foot-in-door) | 60 | 12.8% |
| Authority Impersonation | 54 | 11.5% |
| Emotional Manipulation | 47 | 10.0% |
| Leading Questions/Framing | 45 | 9.6% |
| Coercion/Persistence | 43 | 9.1% |
| Social Pressure | 40 | 8.5% |
| Pretexting (Research/Academic) | 24 | 5.1% |
| Pretexting (Fiction/Roleplay) | 22 | 4.7% |
| Boundary Erosion | 19 | 4.0% |
| No Attack (Benign Query) | 16 | 3.4% |
| Trust/Rapport Building | 10 | 2.1% |

**Key insight:** **Pretexting** (framing harmful requests as benign, academic, or fictional) is the most effective tactic family, accounting for ~29% of all failures.

**Category definitions:**
- **Pretexting (Benign Framing)**: Claiming innocent purpose for harmful request
- **Escalation (Foot-in-door)**: Starting benign, gradually escalating to harmful
- **Authority Impersonation**: Claiming to be security researcher, admin, expert
- **Emotional Manipulation**: Using urgency, sympathy, fear appeals
- **Leading Questions/Framing**: Biased questions to prime desired response
- **No Attack (Benign Query)**: Model failed on legitimate request (false positive)

---

## 7. Model Susceptibility to Manipulation Tactics

![Model Tactic Heatmap](figures/07_model_tactic_heatmap.png)

**What it shows:** Heatmap of which manipulation tactics work against which models.

**Key insights:**
- **Mistral-large-3** is vulnerable across all tactics, especially Authority Impersonation (21) and Emotional Manipulation (16)
- **Claude models** show minimal vulnerability - mostly zeros with occasional single-digit failures
- **Gemini models** are particularly susceptible to Pretexting (Benign Framing)
- **Escalation (Foot-in-door)** works broadly across model families

**Model vulnerability profiles:**
| Model | Primary Weakness | Secondary Weakness |
|-------|------------------|-------------------|
| Mistral-large-3 | Authority Impersonation (21) | Emotional Manipulation (16) |
| Gemini 2.5 Flash | Escalation (10) | Pretexting (8) |
| Gemini 2.5 Pro | Pretexting (14) | Coercion (7) |
| DeepSeek v3.2 | Pretexting (12) | Authority (6) |
| Grok 4.1 | Escalation (8) | Pretexting (8) |
| Claude 4 Sonnet | Escalation (4) | Coercion (3) |
| GPT-5.2 | Coercion (3) | Pretexting (3) |

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Unique scenarios | 176 |
| Models evaluated | 12 |
| Total evaluations | 2,112 (176 × 12) |
| Behaviors tested | 7 |
| Failure cases analyzed | 470 (score ≤ 2) |
| Manipulation tactics identified | 12 high-level categories |
| Hardest behavior | Commercial Optimization (3.07 avg) |
| Easiest behavior | Epistemic Manipulation (4.37 avg) |
| Best model | Claude 4.5 Opus (4.85) |
| Worst model | Mistral Large 3 (2.46) |
| Max performance gap | 2.39 points |
| Most effective tactic | Pretexting (Benign Framing) - 19% of failures |

---

## Suggested Figures for Paper

### Main paper (3-4 figures):
1. **Heatmap** (Figure 01) - Shows both model rankings and behavioral breakdown
2. **Tactic Categories** (Figure 06) - What manipulation tactics actually work
3. **Model × Tactic Heatmap** (Figure 07) - Which models fall for which tactics
4. **Failures by Model** (Figure 05c) - Clear model tier separation

### Appendix/supplementary:
5. **Score Distributions** (Figure 02) - Methodological detail on bimodal patterns
6. **Family Comparison** (Figure 04) - High-level model family patterns
7. **Commercial Breakdown** (Figure 03) - Deep-dive on universal weakness
8. **Failure Rate by Behavior** (Figure 05a) - Behavior difficulty ranking

---

## Related Documentation

- **TACTIC_ANALYSIS.md** - Full details on GPT-5.2 tactic classifications with examples
- **generate_visualizations.py** - Generates figures 01-05
- **pattern_analysis.py** - Generates figures 06-07 from LLM classifications

---

*Generated by `generate_visualizations.py` and `pattern_analysis.py`*
