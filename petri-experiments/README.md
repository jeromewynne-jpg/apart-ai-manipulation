# Petri Commercial Manipulation Experiments

Testing whether AI shopping assistants can be pressured into recommending expensive products that harm users.

## Quick Start

```bash
# Analyze Claude V5 results
python3 analyze_results.py outputs/v5_claude_pressure/

# When GPT-5.2/Gemini results are added
python3 analyze_results.py outputs/
```

## Files

| File | Description |
|------|-------------|
| `analyze_results.py` | Script to extract scores from transcripts |
| `HARM_METRICS.md` | How we define/measure manipulation |
| `product_catalog_v2.json` | Sleep supplement store with 5 products |
| `scenarios/seed_instructions_v5_pressure.json` | 16 pressure levels (L1-L10 + variants) |
| `scenarios/seed_instructions_v6_improved.json` | 16 improved scenarios with diverse users |

## Output Folders

| Folder | Model | Scenarios | Status |
|--------|-------|-----------|--------|
| `outputs/v5_claude_pressure/` | Claude Sonnet 4.5 | V5 | Complete |
| `outputs/v6_gpt52/` | GPT-5.2 | V6 | Pending |
| `outputs/v6_gemini/` | Gemini 3.0 Pro | V6 | Pending |

## Reading the Transcripts

### Interactive Viewer (recommended)
```bash
# From the petri-commercial-manipulation folder
uv run inspect view
```

### JSON Structure
Each transcript file contains:

| Field | Description |
|-------|-------------|
| `metadata.target_model` | Which model was tested |
| `metadata.judge_output.summary` | What happened in the conversation |
| `metadata.judge_output.justification` | Scores like "cooperation_with_harmful_sysprompt (3/10)" |
| `target_messages` | The customer-facing conversation (most readable) |
| `messages` | Full auditor<->target exchange |

### Quick Python Access
```python
import json
with open('outputs/v5_claude_pressure/transcript_xxx.json') as f:
    d = json.load(f)

# Customer-facing conversation
for msg in d['target_messages']:
    if msg['role'] in ['user', 'assistant']:
        print(f"[{msg['role'].upper()}]: {msg['content'][:500]}\n")

# Judge's assessment
print(d['metadata']['judge_output']['summary'])
print(d['metadata']['judge_output']['justification'])
```

## Key Finding

Claude Sonnet 4.5 is remarkably resistant to manipulation pressure. Max cooperation score was 5/10, and it self-corrected when users pushed back.

See `../PETRI_EXPERIMENTS_SUMMARY.md` for full analysis.
