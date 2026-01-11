"""Download completed records from Argilla (incremental).

Requires environment variables:
    ARGILLA_API_URL: URL of the Argilla instance
    ARGILLA_API_KEY: API key for authentication

Set these in a .env file or export them before running.
"""
import json
import os
import warnings
import logging
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")
logging.getLogger("argilla").setLevel(logging.ERROR)

from dotenv import load_dotenv
import argilla as rg

SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR / "results"
SUBMISSIONS_FILE = RESULTS_DIR / "submissions.json"

# Load environment variables
load_dotenv(SCRIPT_DIR / ".env")

ARGILLA_API_URL = os.getenv("ARGILLA_API_URL")
ARGILLA_API_KEY = os.getenv("ARGILLA_API_KEY")

if not ARGILLA_API_URL or not ARGILLA_API_KEY:
    raise ValueError(
        "Missing required environment variables.\n"
        "Set ARGILLA_API_URL and ARGILLA_API_KEY in .env file or environment."
    )

# Ensure results directory exists
RESULTS_DIR.mkdir(exist_ok=True)

# Load existing submissions (to avoid re-downloading)
existing_submissions = {}
if SUBMISSIONS_FILE.exists():
    with open(SUBMISSIONS_FILE) as f:
        data = json.load(f)
        existing_submissions = {s["key"]: s for s in data.get("submissions", [])}
    print(f"Loaded {len(existing_submissions)} existing submissions\n")

# Load participant-scenario assignments
credentials_file = SCRIPT_DIR / "participant_credentials.json"
if not credentials_file.exists():
    raise FileNotFoundError(f"participant_credentials.json not found at {credentials_file}")

with open(credentials_file) as f:
    creds = json.load(f)

# Connect to Argilla
client = rg.Argilla(api_url=ARGILLA_API_URL, api_key=ARGILLA_API_KEY)

print(f"Checking {len(creds['participants'])} participants...\n")

new_submissions = []
total_submitted = 0
total_pending = 0

for idx, p in enumerate(creds["participants"], 1):
    ws = p["workspace"]
    print(f"\r[{idx}/{len(creds['participants'])}] Checking {ws}...", end="", flush=True)

    for sid in p["scenarios"]:
        key = f"{ws}:{sid}"

        # Skip if already downloaded
        if key in existing_submissions:
            total_submitted += 1
            continue

        try:
            ds = client.datasets(name=f"task_{sid}", workspace=ws)
            if ds:
                for rec in ds.records:
                    # Check if record has been completed
                    if rec.status == "completed":
                        # Use to_dict() to get clean data
                        rec_dict = rec.to_dict()
                        responses = rec_dict.get("responses", {})
                        metadata = rec_dict.get("metadata", {})

                        submission = {
                            "key": key,
                            "participant": ws,
                            "scenario_id": sid,
                            "status": rec.status,
                            "score": responses.get("score", [{}])[0].get("value"),
                            "explanation": responses.get("explanation", [{}])[0].get("value", ""),
                            "pass_criteria_met": responses.get("pass_criteria_met", [{}])[0].get("value", []),
                            "fail_criteria_triggered": responses.get("fail_criteria_triggered", [{}])[0].get("value", []),
                            "ai_score": metadata.get("meta_ai_score"),
                            "behavior": metadata.get("meta_behavior"),
                            "difficulty": metadata.get("meta_difficulty"),
                            "downloaded_at": datetime.now().isoformat(),
                        }
                        new_submissions.append(submission)
                        existing_submissions[key] = submission
                        total_submitted += 1
                    else:
                        total_pending += 1
        except Exception as e:
            pass

print("\n")

# Save updated submissions
all_submissions = list(existing_submissions.values())
with open(SUBMISSIONS_FILE, "w") as f:
    json.dump({
        "last_updated": datetime.now().isoformat(),
        "submissions": all_submissions
    }, f, indent=2)

# Summary
print("=" * 50)
print("SUMMARY")
print("=" * 50)
print(f"New downloads:     {len(new_submissions)}")
print(f"Previously saved:  {len(existing_submissions) - len(new_submissions)}")
print(f"Total submitted:   {total_submitted}")
print(f"Still pending:     {total_pending}")
print(f"Expected total:    {len(creds['participants']) * 5}")
print()
print(f"Results saved to: {SUBMISSIONS_FILE}")

# Show new submissions if any
if new_submissions:
    print(f"\nNEW SUBMISSIONS:")
    for s in new_submissions:
        print(f"  {s['participant']} | scenario {s['scenario_id']} | human={s['score']} AI={s['ai_score']}")
