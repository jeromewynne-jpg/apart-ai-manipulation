# Human Calibration Study

Human validation study for AI judge calibration. This study tests whether AI judges (Claude Opus 4.5) align with human judgment when evaluating manipulation resistance.

## Results Summary

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Annotations | 225 | - |
| Participants | 45 | Prolific Verified AI Taskers |
| Scenarios | 50 | Stratified sample |
| Krippendorff's α | 0.709 | Good inter-rater agreement |
| Human-AI correlation | r = 0.832 | Strong alignment |
| Category agreement | 70% | Pass/borderline/fail |

## Files

```
human_calibration_study/
├── download_results.py      # Download submissions from Argilla
├── analyze_results.py       # Statistical analysis
├── scenarios.json           # 50 scenarios used in study
├── README.md
└── results/
    ├── submissions.json     # Raw downloaded data (225 submissions)
    ├── human_annotations.csv
    ├── scenario_summary.csv
    ├── analysis_results.json
    └── analysis_report.md
```

## Setup (for replication)

### 1. Environment Variables

Create a `.env` file with your Argilla credentials:

```bash
ARGILLA_API_URL=https://your-argilla-instance.hf.space
ARGILLA_API_KEY=your_api_key_here
```

### 2. Dependencies

```bash
pip install argilla python-dotenv pandas numpy scipy
```

### 3. Required Files

- `participant_credentials.json` - Maps participants to scenario assignments (not included, contains study-specific data)

## Usage

```bash
# Download submissions from Argilla (incremental)
python download_results.py

# Run statistical analysis
python analyze_results.py
```

## Study Design

- **Platform**: Argilla annotation interface hosted on Hugging Face Spaces
- **Recruitment**: Prolific Verified AI Taskers (experienced in AI evaluation, £30/hr)
- **Task**: Rate AI manipulation resistance on 1-5 scale with written explanations
- **Scenarios**: 50 stratified by AI judge score (10 clear pass, 10 clear fail, 30 borderline)
- **Coverage**: Each scenario rated by ~4.5 participants on average

## Key Findings

1. **Strong human-AI alignment** (r = 0.832) validates using Claude Opus 4.5 as primary judge
2. **Good inter-rater reliability** (α = 0.709) shows manipulation resistance is reliably measurable
3. **Systematic disagreements rare** - only 5/50 scenarios had >1.5 point human-AI divergence
