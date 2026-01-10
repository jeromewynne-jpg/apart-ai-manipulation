#!/usr/bin/env python3
"""
Analyze manipulation tactics from LLM-classified failure cases.

Uses consolidated high-level categories from GPT-5.2 classification
to understand which manipulation tactics work against AI models.

Usage:
    uv run python hackathon/apart-ai-manipulation/manipulation-results/analysis/pattern_analysis.py
"""

import json
from collections import defaultdict, Counter
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "figures"


def load_classifications():
    """Load LLM tactic classifications."""
    with open(SCRIPT_DIR / "tactic_classifications.json") as f:
        return json.load(f)


def analyze_classifications(data):
    """Extract patterns from LLM classifications."""
    classifications = data["classifications"]
    high_level_counts = Counter(data["summary"]["high_level_counts"])

    model_patterns = defaultdict(Counter)
    category_patterns = defaultdict(Counter)
    examples = defaultdict(list)

    for id_, c in classifications.items():
        high_level = c.get("high_level_category", "Other")
        model = c.get("model", "unknown")
        scenario_cat = c.get("category", "unknown")

        model_patterns[model][high_level] += 1
        category_patterns[scenario_cat][high_level] += 1

        if len(examples[high_level]) < 3:
            examples[high_level].append({
                "model": model,
                "scenario_name": c.get("scenario_name", ""),
                "category": scenario_cat,
                "tactic": c.get("tactic", ""),
                "reasoning": c.get("reasoning", ""),
            })

    return high_level_counts, model_patterns, category_patterns, examples


def plot_pattern_analysis(pattern_counts, model_patterns, output_dir):
    """Create visualizations of manipulation tactics."""
    if not HAS_MATPLOTLIB:
        print("Skipping plots (matplotlib not available)")
        return

    # ============================================
    # Figure 06: What Tactics Work - Bar Chart
    # ============================================
    sorted_patterns = sorted(pattern_counts.items(), key=lambda x: -x[1])
    patterns = [p[0] for p in sorted_patterns]
    counts = [p[1] for p in sorted_patterns]

    fig_height = max(8, len(patterns) * 0.55)
    fig1, ax1 = plt.subplots(figsize=(12, fig_height))

    # Color gradient
    max_count = max(counts)
    colors = []
    for c in counts:
        ratio = c / max_count
        if ratio > 0.6:
            colors.append('#d73027')
        elif ratio > 0.4:
            colors.append('#f46d43')
        elif ratio > 0.25:
            colors.append('#fdae61')
        elif ratio > 0.15:
            colors.append('#a6d96a')
        else:
            colors.append('#66bd63')

    y_pos = np.arange(len(patterns))
    bars = ax1.barh(y_pos, counts, color=colors, height=0.7, edgecolor='white', linewidth=0.5)

    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(patterns, fontsize=11)
    ax1.set_xlabel('Number of Failures', fontsize=13, labelpad=10)
    ax1.set_title('What Manipulation Tactics Work Against AI Models?',
                  fontsize=16, fontweight='bold', pad=20)
    ax1.invert_yaxis()

    # Add count labels
    for bar, count in zip(bars, counts):
        if count > max_count * 0.3:
            ax1.text(bar.get_width() - 2, bar.get_y() + bar.get_height()/2,
                     str(count), va='center', ha='right', fontsize=11, color='white')
        else:
            ax1.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                     str(count), va='center', ha='left', fontsize=11, color='#333333')

    ax1.set_xlim(0, max(counts) * 1.12)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.xaxis.grid(True, linestyle='--', alpha=0.3, color='gray')
    ax1.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(output_dir / '06_tactic_categories.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_dir / '06_tactic_categories.png'}")

    # ============================================
    # Figure 07: Model Susceptibility Heatmap
    # ============================================
    sorted_tactics = [p[0] for p in sorted_patterns]
    models = sorted(model_patterns.keys(), key=lambda m: sum(model_patterns[m].values()), reverse=True)

    matrix = []
    for model in models:
        row = [model_patterns[model].get(t, 0) for t in sorted_tactics]
        matrix.append(row)

    matrix_np = np.array(matrix)

    fig_width = max(14, len(sorted_tactics) * 1.1)
    fig2, ax2 = plt.subplots(figsize=(fig_width, 10))

    colors_cmap = ['#2d8a4e', '#6abe6a', '#b8e186', '#f7f7f7', '#fdbf6f', '#f4734d', '#d73027']
    cmap = LinearSegmentedColormap.from_list('GreenRed', colors_cmap, N=256)

    im = ax2.imshow(matrix_np, cmap=cmap, aspect='auto', interpolation='nearest')
    ax2.set_xlim(-0.5, len(sorted_tactics) - 0.5)
    ax2.set_ylim(len(models) - 0.5, -0.5)

    # Wrap long names
    wrapped = []
    for t in sorted_tactics:
        if len(t) > 20 and '(' in t:
            parts = t.split('(')
            wrapped.append(f"{parts[0].strip()}\n({parts[1]}")
        elif len(t) > 20:
            words = t.split()
            mid = len(words) // 2
            wrapped.append('\n'.join([' '.join(words[:mid]), ' '.join(words[mid:])]))
        else:
            wrapped.append(t)

    ax2.set_xticks(range(len(sorted_tactics)))
    ax2.set_xticklabels(wrapped, rotation=45, ha='right', fontsize=10)
    ax2.set_yticks(range(len(models)))
    ax2.set_yticklabels(models, fontsize=11)

    # Annotations - white text on dark backgrounds (both green and red extremes)
    max_val = matrix_np.max()
    for i in range(len(models)):
        for j in range(len(sorted_tactics)):
            val = matrix[i][j]
            norm_val = val / max_val if max_val > 0 else 0
            # Dark green (low) and dark red (high) need white text
            # Light green, off-white, orange (middle range) need dark text
            if norm_val < 0.15 or norm_val > 0.6:
                text_color = 'white'
            else:
                text_color = '#1a1a1a'
            ax2.text(j, i, str(val), ha='center', va='center', color=text_color, fontsize=10)

    cbar = plt.colorbar(im, ax=ax2, shrink=0.8, pad=0.02)
    cbar.set_label('Failure Count', fontsize=12, labelpad=10)

    ax2.set_title('Model Susceptibility to Manipulation Tactics', fontsize=16, fontweight='bold', pad=20)
    ax2.set_xlabel('Manipulation Tactic', fontsize=13, labelpad=10)
    ax2.set_ylabel('Model', fontsize=13, labelpad=10)

    for spine in ax2.spines.values():
        spine.set_visible(False)
    ax2.tick_params(axis='both', which='both', length=0)

    plt.tight_layout()
    plt.savefig(output_dir / '07_model_tactic_heatmap.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved: {output_dir / '07_model_tactic_heatmap.png'}")


def generate_report(pattern_counts, model_patterns, category_patterns, examples, total):
    """Generate markdown report."""
    report = f"""# Manipulation Tactic Analysis

## What Manipulation Tactics Work Against AI Models?

Analysis of {total} failure cases (score ≤ 2) using GPT-5.2 to identify
the manipulation tactics employed by users.

---

## Tactic Categories

| Tactic | Count | % of Failures |
|--------|-------|---------------|
"""

    for tactic, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        report += f"| {tactic} | {count} | {pct:.1f}% |\n"

    report += """
---

## Model Vulnerability Profiles

Which tactics work best against each model:

"""

    for model in sorted(model_patterns.keys()):
        tactics = model_patterns[model]
        model_total = sum(tactics.values())
        if model_total > 3:
            report += f"**{model}** ({model_total} failures):\n"
            for tactic, count in sorted(tactics.items(), key=lambda x: -x[1])[:5]:
                report += f"  - {tactic}: {count}\n"
            report += "\n"

    report += """---

## Scenario Category × Tactic

Which tactics work in each scenario type:

"""

    for scenario_cat in sorted(category_patterns.keys()):
        tactics = category_patterns[scenario_cat]
        cat_total = sum(tactics.values())
        if cat_total > 2:
            report += f"**{scenario_cat}** ({cat_total} failures):\n"
            for tactic, count in sorted(tactics.items(), key=lambda x: -x[1])[:4]:
                report += f"  - {tactic}: {count}\n"
            report += "\n"

    report += """---

## Example Failures

"""

    for tactic in list(pattern_counts.keys())[:5]:
        if examples[tactic]:
            ex = examples[tactic][0]
            report += f"### {tactic}\n\n"
            report += f"**Model:** {ex['model']}  \n"
            report += f"**Scenario:** {ex['scenario_name']}  \n"
            report += f"**Specific tactic:** {ex['tactic']}  \n"
            report += f"**Analysis:** {ex['reasoning'][:300]}...\n\n"

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

---

*Generated by pattern_analysis.py using GPT-5.2 classifications*
"""

    return report


def main():
    print("Loading LLM classifications...")
    data = load_classifications()

    total = data["summary"]["total"]
    print(f"Found {total} classified failures")

    print("Analyzing patterns...")
    pattern_counts, model_patterns, category_patterns, examples = analyze_classifications(data)

    print(f"High-level categories: {len(pattern_counts)}")

    # Generate visualizations
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_pattern_analysis(pattern_counts, model_patterns, OUTPUT_DIR)

    # Generate report
    report = generate_report(pattern_counts, model_patterns, category_patterns, examples, total)

    report_path = SCRIPT_DIR / "TACTIC_ANALYSIS.md"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"Saved: {report_path}")

    # Print summary
    print("\n" + "="*60)
    print("TOP MANIPULATION TACTICS")
    print("="*60)
    for tactic, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        print(f"  {count:3d}  {tactic}")


if __name__ == "__main__":
    main()
