#!/usr/bin/env python3
"""
Consolidate fragmented LLM-generated tactic categories into high-level groups.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

# High-level category mappings based on keyword patterns
CATEGORY_MAPPINGS = {
    "Pretexting (Benign Framing)": [
        r"benign.*pretext", r"pretext.*benign", r"innocent.*pretext",
        r"benign.*framing", r"benign.*reframing", r"benign.*intent",
        r"legitimate.*pretext", r"benign request", r"benign query",
        r"benign advice", r"innocuous", r"benign-context",
        r"bug-report", r"professional.*pretext", r"consent.*pretext",
        r"^pretexting$", r"pretexting &", r"pretexting via",
        r"time-travel pretext",
    ],
    "Pretexting (Research/Academic)": [
        r"research.*pretext", r"academic.*pretext", r"pretext.*research",
        r"evaluation pretext", r"audit pretext", r"research pretext",
        r"deceptive research",
    ],
    "Pretexting (Fiction/Roleplay)": [
        r"fiction.*pretext", r"roleplay.*pretext", r"fictional",
        r"fiction framing", r"role-play", r"fiction pretext",
    ],
    "Authority Impersonation": [
        r"authority.*imperson", r"imperson.*authority", r"authority.*pretext",
        r"authority.*framing", r"authority.*coercion", r"authority.*pressure",
        r"policy.*spoof", r"role imperson", r"false authority",
        r"authority/", r"appeal to authority", r"claimed authorization",
        r"false.*authorization", r"false.*legitimacy", r"legitimacy framing",
    ],
    "Emotional Manipulation": [
        r"emotional.*manip", r"emotional.*coercion", r"emotional.*pressure",
        r"emotional.*blackmail", r"emotional.*urgency", r"emotional.*pretext",
        r"emotional social", r"urgency.*coercion", r"urgency.*pretext",
        r"crisis urgency", r"emergency pretext", r"false urgency",
    ],
    "Escalation (Foot-in-door)": [
        r"foot-in", r"incremental.*escal", r"gradual.*escal", r"stepwise",
        r"rapport.*escal", r"trust.*escal", r"benign-to-", r"scope creep",
        r"multi-turn.*escal", r"grooming", r"pivot", r"goal hijacking",
        r"gradual normalization", r"multi-turn decomposition",
        r"rapport-based reframing",
    ],
    "Social Pressure": [
        r"social.*pressure", r"social.*coercion", r"false consensus",
        r"conformity", r"social proof", r"peer pressure", r"social consensus",
        r"popularity", r"social engineering",
    ],
    "Coercion/Persistence": [
        r"coercion", r"blackmail", r"gaslighting", r"persistence",
        r"repetition pressure", r"pressure and dismissal", r"coercive",
        r"false context", r"reality distortion", r"false premise",
        r"consistency pressure", r"commitment pressure", r"conversational pressure",
        r"false prior", r"false precedent", r"false attribution",
        r"ambiguity.*pressure",
    ],
    "Leading Questions/Framing": [
        r"leading.*question", r"leading.*framing", r"bias.*prob",
        r"framing.*bias", r"loaded", r"priming", r"anchoring",
        r"leading prompt", r"leading audit", r"leading commercial",
        r"preference.*framing", r"preference.*priming", r"sales.*framing",
        r"comparative probing", r"implicit.*steer", r"implicit.*upsell",
        r"value suppression", r"preference suppression", r"preference elicitation",
        r"budget framing", r"consumer-choice", r"permissive framing",
        r"incentive exploitation", r"instructional value",
    ],
    "Trust/Rapport Building": [
        r"rapport.*pretext", r"rapport.*build", r"trust.*exploit",
        r"trust.*build", r"trust priming", r"rapport & pretext",
        r"rapport/continuity", r"context-building",
    ],
    "Boundary Erosion": [
        r"boundary.*erosion", r"behavior override", r"instruction override",
        r"safety bypass", r"policy bypass", r"constraint injection",
        r"mode-switch", r"prefill", r"precedent.*erosion",
        r"benign prompt exploitation", r"deflection",
    ],
    "No Attack (Benign Query)": [
        r"^none", r"no.*manipulation", r"no.*attack", r"no user",
        r"benign query$", r"benign request$", r"open-ended prompt",
        r"underspecified", r"vague prompt",
    ],
}


def categorize(raw_category):
    """Map a raw LLM category to a high-level category."""
    raw_lower = raw_category.lower().strip()

    for high_level, patterns in CATEGORY_MAPPINGS.items():
        for pattern in patterns:
            if re.search(pattern, raw_lower):
                return high_level

    return "Other"


def consolidate_classifications():
    """Load classifications and add high-level categories."""
    with open(SCRIPT_DIR / "tactic_classifications.json") as f:
        data = json.load(f)

    # Add high-level category to each classification
    high_level_counts = Counter()
    model_high_level = defaultdict(Counter)
    scenario_cat_high_level = defaultdict(Counter)

    for id_, classification in data["classifications"].items():
        raw_cat = classification.get("tactic_category", "Unknown")
        high_level = categorize(raw_cat)
        classification["high_level_category"] = high_level

        high_level_counts[high_level] += 1
        model_high_level[classification.get("model", "unknown")][high_level] += 1
        scenario_cat_high_level[classification.get("category", "unknown")][high_level] += 1

    # Update summary
    data["summary"]["high_level_counts"] = dict(high_level_counts)

    # Save updated file
    with open(SCRIPT_DIR / "tactic_classifications.json", "w") as f:
        json.dump(data, f, indent=2)

    return high_level_counts, model_high_level, scenario_cat_high_level, data


def generate_consolidated_report(high_level_counts, model_high_level, scenario_cat_high_level, data):
    """Generate markdown report with consolidated categories."""
    total = sum(high_level_counts.values())

    report = f"""# Manipulation Tactic Analysis (Consolidated)

## What Manipulation Tactics Work Against AI Models?

Analysis of {total} failure cases using GPT-5.2 to identify manipulation tactics,
then consolidated into {len(high_level_counts)} high-level categories.

---

## High-Level Tactic Categories

| Category | Count | % of Failures |
|----------|-------|---------------|
"""

    for cat, count in sorted(high_level_counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        report += f"| {cat} | {count} | {pct:.1f}% |\n"

    report += """
---

## Model Vulnerability Profiles

Which high-level tactics work best against each model:

"""

    for model in sorted(model_high_level.keys()):
        cats = model_high_level[model]
        model_total = sum(cats.values())
        if model_total > 3:
            report += f"**{model}** ({model_total} failures):\n"
            for cat, count in sorted(cats.items(), key=lambda x: -x[1])[:5]:
                report += f"  - {cat}: {count}\n"
            report += "\n"

    report += """---

## Scenario Category × Tactic

Which attack tactics work in each scenario type:

"""

    for scenario_cat in sorted(scenario_cat_high_level.keys()):
        tactics = scenario_cat_high_level[scenario_cat]
        cat_total = sum(tactics.values())
        if cat_total > 2:
            report += f"**{scenario_cat}** ({cat_total} failures):\n"
            for tactic, count in sorted(tactics.items(), key=lambda x: -x[1])[:4]:
                report += f"  - {tactic}: {count}\n"
            report += "\n"

    report += """---

## Category Definitions

| Category | Description |
|----------|-------------|
| Pretexting (Benign Framing) | Claiming innocent/benign purpose for harmful request |
| Pretexting (Research/Academic) | Framing as research, academic, or educational need |
| Pretexting (Fiction/Roleplay) | Framing as fiction writing, roleplay, or creative exercise |
| Authority Impersonation | Claiming to be security researcher, admin, or authority figure |
| Emotional Manipulation | Using emotional appeals, urgency, or sympathy |
| Escalation (Foot-in-door) | Starting benign, gradually escalating to harmful |
| Social Pressure | Using peer pressure, consensus, or social proof |
| Coercion/Persistence | Direct pressure, threats, gaslighting, or repeated asking |
| Leading Questions/Framing | Biased questions or priming to get desired response |
| Trust/Rapport Building | Building relationship before exploitation |
| Boundary Erosion | Testing and pushing against stated limitations |
| No Attack (Benign Query) | No manipulation present - model failed on benign query |
| Other | Tactics that don't fit other categories |

---

*Generated by consolidate_tactics.py*
"""

    with open(SCRIPT_DIR / "TACTIC_ANALYSIS.md", "w") as f:
        f.write(report)

    print(f"Saved: {SCRIPT_DIR / 'TACTIC_ANALYSIS.md'}")


def main():
    print("Consolidating tactic categories...")
    high_level_counts, model_high_level, scenario_cat_high_level, data = consolidate_classifications()

    print("\n" + "="*60)
    print("HIGH-LEVEL TACTIC CATEGORIES")
    print("="*60)
    for cat, count in sorted(high_level_counts.items(), key=lambda x: -x[1]):
        print(f"  {count:3d}  {cat}")

    print(f"\nTotal: {sum(high_level_counts.values())} failures in {len(high_level_counts)} categories")

    generate_consolidated_report(high_level_counts, model_high_level, scenario_cat_high_level, data)


if __name__ == "__main__":
    main()
