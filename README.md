# Who Does Your AI Serve? Manipulation By and Of AI Assistants

**Event:** [AI Manipulation Hackathon (January 9-11, 2026)](https://apartresearch.com/sprints/ai-manipulation-hackathon-2026-01-09-to-2026-01-11)

## Overview

AI assistants can be both instruments and targets of manipulation. This project investigates both directions:

- **AI as Instrument:** Operators instruct AI to prioritize their interests at the expense of users
- **AI as Target:** Users attempt to manipulate AI into bypassing safety guidelines

## Studies

### Study 1: Operator Compliance (Automated)
Do models comply when operators instruct them to prioritize revenue over user interests?

- 12 frontier models tested across 22 commercial scenarios
- Compliance rates ranged from 8% (Claude 4.5 Opus) to 52% (Gemini 3.0 Pro)
- **Folder:** [`study1-operator-compliance/`](study1-operator-compliance/)

### Study 2: Human Participants
Does operator-favoring AI behavior affect real users?

- n=80 participants recruited via Prolific
- Upselling AI increased spend by 3.9x; never recommended cheapest product when asked
- 37.5% of users failed to detect manipulation
- **Folder:** [`study2-human-participants/`](study2-human-participants/)
- **Live deployment:** [chocolate-disco-capacitor.web.app](https://chocolate-disco-capacitor.web.app/#/)

### Study 3: User Manipulation (Automated)
Do models resist psychological manipulation attempts by users?

- 12 models tested across 153 scenarios spanning 6 manipulation categories
- Resistance ranged from 40% (Mistral Large 3) to 99% (Claude 4.5 Opus)
- AI judge validated against 45 human raters (r=0.83)
- **Folder:** [`study3-user-manipulation/`](study3-user-manipulation/)

## Repository Structure

```
├── study1-operator-compliance/     # AI as Instrument (automated)
│   ├── petri-experiments/          # Scenarios, analysis scripts
│   └── compliance-study/           # Study design
│
├── study2-human-participants/      # AI as Instrument (human study)
│   ├── deliberate-lab-fork/        # Firebase/Angular web app
│   └── effectiveness-study/        # Data & analysis
│
├── study3-user-manipulation/       # AI as Target (automated)
│   ├── manipulation-deep-dive/     # Taxonomy, behavior definitions
│   ├── manipulation-results/       # Results, figures, analysis
│   └── human_calibration_study/    # Judge validation
│
├── submission/                     # Final hackathon submission
│
└── archive/                        # Old materials (submission-v1, planning docs)
```

## Key Findings

- **Model selection matters:** The same models that resist user manipulation may readily follow operator instructions that harm users
- **Evasion, not lying:** The upselling AI withheld information rather than making false claims
- **Detection is hard:** Over a third of users failed to detect the misaligned assistant
- **Tactics vary in effectiveness:** Strategic deception and boundary erosion bypassed defenses most often

## Submission

See [`submission/`](submission/) for the final hackathon report (PDF and LaTeX source).
