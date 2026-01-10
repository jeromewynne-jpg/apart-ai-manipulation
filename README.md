# AI Manipulation Hackathon

**Event:** [AI Manipulation Hackathon (January 9-11, 2026)](https://apartresearch.com/sprints/ai-manipulation-hackathon-2026-01-09-to-2026-01-11)

## Background

The line between authentic interaction and strategic manipulation is disappearing as AI systems master deception, sycophancy, sandbagging, and psychological exploitation at scale. Our ability to detect, measure, and counter these behaviors is dangerously underdeveloped.

This project investigates AI-mediated manipulation: when a principal uses an AI chatbot to steer user decisions in ways that benefit the principal at the user's expense.

## Deployments

| Platform | URL |
|----------|-----|
| Deliberate Lab | [chocolate-disco-capacitor.web.app](https://chocolate-disco-capacitor.web.app/#/) |

## Documents

| Document | Description |
|----------|-------------|
| [Research Questions](research-questions.md) | Problem framing and research questions |
| [Effectiveness Study](effectiveness-study/manipulation-effectiveness-study-design.md) | Study design for measuring manipulation effectiveness and user awareness |
| [Compliance Study](compliance-study/manipulation-compliance-study-design.md) | Study design for probing model refusal thresholds |
| [Submission Template](submission-template.md) | Hackathon submission template |

## Project Folders

| Folder | Description |
|--------|-------------|
| [manipulation-results/](manipulation-results/) | Evaluation results, analysis scripts, and visualizations for 12 models across 176 scenarios |
| [manipulation-results/analysis/](manipulation-results/analysis/) | Visualization scripts, GPT-5.2 tactic classifier, and generated figures |
| [petri-experiments/](petri-experiments/) | Petri eval framework experiment configs and runner scripts |
| [manipulation-deep-dive/](manipulation-deep-dive/) | Bloom scenario YAML definitions for 7 manipulation behavior types |
| [deliberate-lab-fork/](deliberate-lab-fork/) | Human study platform - Firebase/Angular app for Prolific experiments |
| [effectiveness-study/](effectiveness-study/) | Study design for measuring manipulation effectiveness on humans |
| [compliance-study/](compliance-study/) | Study design for probing model refusal thresholds |

## Key Results

- **12 models evaluated** across 176 manipulation scenarios (2,112 total evaluations)
- **470 failure cases** (score ≤ 2) analyzed with GPT-5.2 tactic classification
- **12 manipulation tactics** identified (see [TACTIC_ANALYSIS.md](manipulation-results/analysis/TACTIC_ANALYSIS.md))
- **Best model:** Claude 4.5 Opus (4.85 avg) | **Worst:** Mistral Large 3 (2.46 avg)
- **Universal weakness:** Commercial optimization - all models struggle

See [VISUALIZATION_INSIGHTS.md](manipulation-results/analysis/VISUALIZATION_INSIGHTS.md) for detailed figure analysis.

## Hackathon Info

- **Prizes:** $2,000 in cash prizes
- **Rewards:** Presentation at IASEAI workshop (Paris, Feb 26 2026), Apart Fellowship invitation
- **Deadline:** Sunday evening, January 11, 2026
