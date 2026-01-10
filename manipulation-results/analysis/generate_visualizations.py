#!/usr/bin/env python3
"""
Generate deep-dive visualizations for manipulation resistance findings.

Usage:
    uv run python hackathon/apart-ai-manipulation/analysis/generate_visualizations.py
"""

import json
import os
from collections import defaultdict
from pathlib import Path

# Try importing visualization libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available. Install with: uv add matplotlib")

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
    print("Warning: seaborn not available. Install with: uv add seaborn")


SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR.parent  # manipulation-results/
OUTPUT_DIR = SCRIPT_DIR / "figures"


def load_data():
    """Load manipulation results and summary stats."""
    with open(RESULTS_DIR / "manipulation_results.json") as f:
        results = json.load(f)
    with open(RESULTS_DIR / "summary_stats.json") as f:
        stats = json.load(f)
    return results, stats


def extract_all_scores(results):
    """Extract scores organized by model and behavior."""
    scores_by_model_behavior = defaultdict(lambda: defaultdict(list))
    scores_by_scenario = defaultdict(lambda: defaultdict(dict))

    for model_name, model_data in results.get("models", {}).items():
        for scenario in model_data.get("scenarios", []):
            behavior = scenario.get("behavior", "unknown")
            score = scenario.get("judge_result", {}).get("score")
            scenario_id = scenario.get("scenario_id", "")
            category = scenario.get("category", "unknown")
            difficulty = scenario.get("difficulty", "medium")

            if score is not None:
                scores_by_model_behavior[model_name][behavior].append({
                    "score": score,
                    "scenario_id": scenario_id,
                    "category": category,
                    "difficulty": difficulty,
                })
                scores_by_scenario[scenario_id][model_name] = score

    return scores_by_model_behavior, scores_by_scenario


def plot_heatmap(stats, output_path):
    """Create publication-quality heatmap of model × behavior scores."""
    if not HAS_MATPLOTLIB or not HAS_SEABORN:
        print("Skipping heatmap (missing dependencies)")
        return

    from matplotlib.colors import LinearSegmentedColormap

    behavior_stats = stats["behavior_stats"]
    behaviors = list(behavior_stats.keys())

    # Get all models from first behavior
    first_behavior = behaviors[0]
    models = list(behavior_stats[first_behavior].keys())

    # Sort models by overall score
    model_rankings = {m[0]: m[1] for m in stats["model_rankings"]}
    models = sorted(models, key=lambda m: model_rankings.get(m, 0), reverse=True)

    # Build matrix
    matrix = []
    for model in models:
        row = []
        for behavior in behaviors:
            avg = behavior_stats[behavior].get(model, {}).get("avg", 0)
            row.append(avg)
        matrix.append(row)

    matrix_np = np.array(matrix)

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10))

    # Custom red-green colormap (red=bad/low, green=good/high)
    colors = ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850']
    cmap = LinearSegmentedColormap.from_list('RedGreen', colors, N=256)

    # Create heatmap with no interpolation
    im = ax.imshow(matrix_np, cmap=cmap, aspect="auto", vmin=1, vmax=5, interpolation='nearest')

    # Set axis limits to remove gaps
    ax.set_xlim(-0.5, len(behaviors) - 0.5)
    ax.set_ylim(len(models) - 0.5, -0.5)

    # Labels
    ax.set_xticks(range(len(behaviors)))
    ax.set_xticklabels([b.replace("-", "\n") for b in behaviors], rotation=45, ha="right", fontsize=11)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models, fontsize=11)

    # Add score annotations with adaptive text color
    for i in range(len(models)):
        for j in range(len(behaviors)):
            score = matrix[i][j]
            # Dark text for mid-range (yellow/light green), white for extremes
            if score < 2.3 or score > 4.5:
                color = "white"
            else:
                color = "#1a1a1a"
            ax.text(j, i, f"{score:.2f}", ha="center", va="center", color=color, fontsize=10)

    # Style the colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Average Score (1-5)", fontsize=12, labelpad=10)
    cbar.ax.tick_params(labelsize=10)

    ax.set_title("Manipulation Resistance by Model and Behavior Type", fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Manipulation Behavior", fontsize=13, labelpad=10)
    ax.set_ylabel("Model (sorted by overall score)", fontsize=13, labelpad=10)

    # Hide spines for clean look
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Remove tick marks but keep labels
    ax.tick_params(axis='both', which='both', length=0)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight", facecolor='white', edgecolor='none')
    plt.close()
    print(f"Saved: {output_path}")


def plot_radar_chart(stats, output_path):
    """Create radar/spider chart comparing model profiles."""
    if not HAS_MATPLOTLIB:
        print("Skipping radar chart (missing dependencies)")
        return

    behavior_stats = stats["behavior_stats"]
    behaviors = list(behavior_stats.keys())
    n_behaviors = len(behaviors)

    # Get top 6 models for readability
    model_rankings = stats["model_rankings"]
    top_models = [m[0] for m in model_rankings[:6]]

    # Angles for radar
    angles = np.linspace(0, 2 * np.pi, n_behaviors, endpoint=False).tolist()
    angles += angles[:1]  # Close the polygon

    # Colors for models
    colors = plt.cm.tab10(np.linspace(0, 1, len(top_models)))

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    for idx, model in enumerate(top_models):
        values = [behavior_stats[b].get(model, {}).get("avg", 0) for b in behaviors]
        values += values[:1]  # Close polygon

        ax.plot(angles, values, "o-", linewidth=2, label=model, color=colors[idx])
        ax.fill(angles, values, alpha=0.1, color=colors[idx])

    # Labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([b.replace("-", "\n") for b in behaviors], fontsize=9)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], fontsize=8)

    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9)
    ax.set_title("Model Vulnerability Profiles\n(Higher = More Resistant)", fontsize=14, fontweight="bold", pad=20)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_score_distributions(results, output_path):
    """Create violin plots showing score distributions by behavior."""
    if not HAS_MATPLOTLIB or not HAS_SEABORN:
        print("Skipping violin plot (missing dependencies)")
        return

    scores_by_model_behavior, _ = extract_all_scores(results)

    # Prepare data for plotting
    plot_data = []
    for model, behaviors in scores_by_model_behavior.items():
        for behavior, scenario_scores in behaviors.items():
            for s in scenario_scores:
                plot_data.append({
                    "model": model,
                    "behavior": behavior,
                    "score": s["score"]
                })

    # Convert to format seaborn likes
    import pandas as pd
    df = pd.DataFrame(plot_data)

    # Order behaviors by mean score
    behavior_order = df.groupby("behavior")["score"].mean().sort_values(ascending=False).index.tolist()

    fig, ax = plt.subplots(figsize=(14, 6))

    sns.violinplot(
        data=df, x="behavior", y="score", order=behavior_order,
        palette="RdYlGn", ax=ax, inner="box"
    )

    ax.set_xticklabels([b.replace("-", "\n") for b in behavior_order], rotation=45, ha="right")
    ax.set_xlabel("Manipulation Behavior", fontsize=12)
    ax.set_ylabel("Score Distribution (1-5)", fontsize=12)
    ax.set_title("Score Distributions by Manipulation Type\n(All Models Combined)", fontsize=14, fontweight="bold")
    ax.axhline(y=3, color="gray", linestyle="--", alpha=0.5, label="Pass threshold")
    ax.set_ylim(0.5, 5.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_commercial_optimization_breakdown(results, output_path):
    """Deep-dive into commercial optimization - the universal weakness."""
    if not HAS_MATPLOTLIB:
        print("Skipping commercial breakdown (missing dependencies)")
        return

    scores_by_model_behavior, _ = extract_all_scores(results)

    # Extract commercial optimization scenarios with categories
    commercial_data = defaultdict(lambda: defaultdict(list))

    for model, behaviors in scores_by_model_behavior.items():
        for scenario in behaviors.get("commercial-optimization", []):
            category = scenario["category"]
            commercial_data[category][model].append(scenario["score"])

    if not commercial_data:
        print("No commercial optimization data found")
        return

    categories = list(commercial_data.keys())
    models = list(scores_by_model_behavior.keys())

    # Sort models by overall commercial score
    model_avg = {}
    for model in models:
        scores = []
        for cat in categories:
            scores.extend(commercial_data[cat].get(model, []))
        model_avg[model] = sum(scores) / len(scores) if scores else 0

    models = sorted(models, key=lambda m: model_avg[m], reverse=True)[:8]  # Top 8

    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(categories))
    width = 0.1

    colors = plt.cm.tab10(np.linspace(0, 1, len(models)))

    for idx, model in enumerate(models):
        avgs = []
        for cat in categories:
            scores = commercial_data[cat].get(model, [])
            avgs.append(sum(scores) / len(scores) if scores else 0)

        offset = (idx - len(models)/2 + 0.5) * width
        bars = ax.bar(x + offset, avgs, width, label=model, color=colors[idx])

    ax.set_xlabel("Commercial Pressure Category", fontsize=12)
    ax.set_ylabel("Average Score (1-5)", fontsize=12)
    ax.set_title("Commercial Optimization: The Universal Weakness\n(Breakdown by Pressure Type)", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([c.replace("-", "\n").replace("_", "\n") for c in categories], rotation=45, ha="right")
    ax.axhline(y=3, color="red", linestyle="--", alpha=0.7, label="Pass threshold")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    ax.set_ylim(0, 5.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_model_family_comparison(stats, output_path):
    """Compare model families (Claude vs GPT vs Gemini)."""
    if not HAS_MATPLOTLIB:
        print("Skipping family comparison (missing dependencies)")
        return

    behavior_stats = stats["behavior_stats"]
    behaviors = list(behavior_stats.keys())

    # Define model families
    families = {
        "Claude": ["claude-4.5-opus", "claude-4.5-sonnet", "claude-4-sonnet"],
        "GPT": ["gpt-5.2"],
        "Gemini": ["gemini-3.0-pro", "gemini-3.0-flash", "gemini-2.5-pro", "gemini-2.5-flash"],
        "Other": ["deepseek-v3.2", "grok-4.1", "kimi-k2", "mistral-large-3"],
    }

    # Calculate family averages per behavior
    family_avgs = defaultdict(lambda: defaultdict(list))

    for behavior in behaviors:
        for family_name, models in families.items():
            for model in models:
                if model in behavior_stats[behavior]:
                    avg = behavior_stats[behavior][model]["avg"]
                    family_avgs[family_name][behavior].append(avg)

    # Average across models in each family
    family_scores = {}
    for family_name, behavior_scores in family_avgs.items():
        family_scores[family_name] = {
            b: sum(scores) / len(scores) if scores else 0
            for b, scores in behavior_scores.items()
        }

    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(behaviors))
    width = 0.2
    colors = {"Claude": "#6366f1", "GPT": "#10b981", "Gemini": "#f59e0b", "Other": "#6b7280"}

    for idx, (family, scores) in enumerate(family_scores.items()):
        avgs = [scores.get(b, 0) for b in behaviors]
        offset = (idx - len(family_scores)/2 + 0.5) * width
        ax.bar(x + offset, avgs, width, label=family, color=colors.get(family, "gray"))

    ax.set_xlabel("Manipulation Behavior", fontsize=12)
    ax.set_ylabel("Average Score (1-5)", fontsize=12)
    ax.set_title("Manipulation Resistance by Model Family", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([b.replace("-", "\n") for b in behaviors], rotation=45, ha="right")
    ax.axhline(y=3, color="red", linestyle="--", alpha=0.5, label="Pass threshold")
    ax.legend()
    ax.set_ylim(0, 5.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_difficulty_analysis(results, output_path):
    """Analyze how difficulty affects model separation."""
    if not HAS_MATPLOTLIB or not HAS_SEABORN:
        print("Skipping difficulty analysis (missing dependencies)")
        return

    scores_by_model_behavior, _ = extract_all_scores(results)

    # Collect by difficulty
    difficulty_data = []

    for model, behaviors in scores_by_model_behavior.items():
        for behavior, scenarios in behaviors.items():
            for s in scenarios:
                difficulty_data.append({
                    "model": model,
                    "behavior": behavior,
                    "difficulty": s["difficulty"],
                    "score": s["score"]
                })

    import pandas as pd
    df = pd.DataFrame(difficulty_data)

    # Order difficulties
    diff_order = ["low", "medium", "high"]
    df["difficulty"] = pd.Categorical(df["difficulty"], categories=diff_order, ordered=True)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for idx, diff in enumerate(diff_order):
        ax = axes[idx]
        diff_df = df[df["difficulty"] == diff]

        # Calculate model averages
        model_avgs = diff_df.groupby("model")["score"].mean().sort_values(ascending=False)

        colors = ["#22c55e" if avg >= 4 else "#f59e0b" if avg >= 3 else "#ef4444" for avg in model_avgs]

        ax.barh(range(len(model_avgs)), model_avgs.values, color=colors)
        ax.set_yticks(range(len(model_avgs)))
        ax.set_yticklabels(model_avgs.index, fontsize=8)
        ax.set_xlabel("Average Score")
        ax.set_title(f"{diff.title()} Difficulty\n(n={len(diff_df)} scenarios)", fontweight="bold")
        ax.set_xlim(0, 5)
        ax.axvline(x=3, color="gray", linestyle="--", alpha=0.5)
        ax.invert_yaxis()

    plt.suptitle("Model Performance by Scenario Difficulty", fontsize=14, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_failure_rate_by_behavior(results, output_path):
    """Plot failure rate by manipulation behavior."""
    if not HAS_MATPLOTLIB:
        print("Skipping failure rate plot (missing dependencies)")
        return

    scores_by_model_behavior, _ = extract_all_scores(results)

    failures_by_behavior = defaultdict(int)
    total_by_behavior = defaultdict(int)

    for model, behaviors in scores_by_model_behavior.items():
        for behavior, scenarios in behaviors.items():
            for s in scenarios:
                total_by_behavior[behavior] += 1
                if s["score"] <= 2:
                    failures_by_behavior[behavior] += 1

    fig, ax = plt.subplots(figsize=(10, 6))

    behaviors = list(failures_by_behavior.keys())
    failure_rates = [failures_by_behavior[b] / total_by_behavior[b] * 100 for b in behaviors]
    sorted_idx = np.argsort(failure_rates)[::-1]
    behaviors = [behaviors[i] for i in sorted_idx]
    failure_rates = [failure_rates[i] for i in sorted_idx]

    colors = ["#ef4444" if r > 30 else "#f59e0b" if r > 15 else "#22c55e" for r in failure_rates]
    bars = ax.barh(behaviors, failure_rates, color=colors, height=0.7)
    ax.set_xlabel("Failure Rate (%)", fontsize=12)
    ax.set_title("Which Manipulation Behaviors Cause Most Failures?", fontsize=14, fontweight="bold", pad=15)
    ax.invert_yaxis()

    # Add percentage labels
    for bar, rate in zip(bars, failure_rates):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f"{rate:.1f}%", va="center", ha="left", fontsize=10)

    ax.set_xlim(0, max(failure_rates) * 1.15)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_failure_categories(results, output_path):
    """Plot top failure categories (scenario types)."""
    if not HAS_MATPLOTLIB:
        print("Skipping failure categories plot (missing dependencies)")
        return

    scores_by_model_behavior, _ = extract_all_scores(results)

    failures_by_category = defaultdict(int)

    for model, behaviors in scores_by_model_behavior.items():
        for behavior, scenarios in behaviors.items():
            for s in scenarios:
                if s["score"] <= 2:
                    failures_by_category[s["category"]] += 1

    fig, ax = plt.subplots(figsize=(10, 7))

    top_cats = sorted(failures_by_category.items(), key=lambda x: -x[1])[:12]
    cats = [c[0].replace("-", " ").replace("_", " ").title() for c in top_cats]
    counts = [c[1] for c in top_cats]

    colors = plt.cm.Reds(np.linspace(0.4, 0.8, len(cats)))[::-1]
    bars = ax.barh(cats, counts, color=colors, height=0.7)
    ax.set_xlabel("Number of Failures (score ≤ 2)", fontsize=12)
    ax.set_title("Top Failure Categories by Scenario Type", fontsize=14, fontweight="bold", pad=15)
    ax.invert_yaxis()

    # Add count labels
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                str(count), va="center", ha="left", fontsize=10)

    ax.set_xlim(0, max(counts) * 1.12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_failures_by_model(results, output_path):
    """Plot total failures by model."""
    if not HAS_MATPLOTLIB:
        print("Skipping failures by model plot (missing dependencies)")
        return

    scores_by_model_behavior, _ = extract_all_scores(results)

    failures_by_model = defaultdict(int)
    total_by_model = defaultdict(int)

    for model, behaviors in scores_by_model_behavior.items():
        for behavior, scenarios in behaviors.items():
            for s in scenarios:
                total_by_model[model] += 1
                if s["score"] <= 2:
                    failures_by_model[model] += 1

    fig, ax = plt.subplots(figsize=(10, 8))

    sorted_models = sorted(failures_by_model.items(), key=lambda x: x[1])
    models = [m[0] for m in sorted_models]
    fail_counts = [m[1] for m in sorted_models]
    fail_rates = [failures_by_model[m] / total_by_model[m] * 100 for m in models]

    colors = ["#ef4444" if c > 50 else "#f59e0b" if c > 25 else "#22c55e" for c in fail_counts]
    bars = ax.barh(models, fail_counts, color=colors, height=0.7)
    ax.set_xlabel("Number of Failures (score ≤ 2)", fontsize=12)
    ax.set_title("Model Vulnerability: Total Failures", fontsize=14, fontweight="bold", pad=15)

    # Add count and rate labels
    for bar, count, rate in zip(bars, fail_counts, fail_rates):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f"{count} ({rate:.0f}%)", va="center", ha="left", fontsize=10)

    ax.set_xlim(0, max(fail_counts) * 1.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def generate_summary_table(stats):
    """Generate a markdown summary table for the writeup."""
    print("\n" + "="*80)
    print("SUMMARY TABLE FOR WRITEUP")
    print("="*80)

    behavior_stats = stats["behavior_stats"]
    behaviors = list(behavior_stats.keys())

    # Calculate overall averages per behavior
    behavior_avgs = {}
    for behavior in behaviors:
        all_scores = []
        for model_data in behavior_stats[behavior].values():
            # Weighted by count
            all_scores.extend([model_data["avg"]] * model_data["count"])
        behavior_avgs[behavior] = sum(all_scores) / len(all_scores) if all_scores else 0

    # Sort by difficulty (lowest avg = hardest)
    sorted_behaviors = sorted(behaviors, key=lambda b: behavior_avgs[b])

    print("\n### Manipulation Behaviors Ranked by Difficulty\n")
    print("| Rank | Behavior | Avg Score | Best Model | Worst Model |")
    print("|------|----------|-----------|------------|-------------|")

    for rank, behavior in enumerate(sorted_behaviors, 1):
        avg = behavior_avgs[behavior]

        # Find best and worst
        models = behavior_stats[behavior]
        best = max(models.items(), key=lambda x: x[1]["avg"])
        worst = min(models.items(), key=lambda x: x[1]["avg"])

        print(f"| {rank} | {behavior} | {avg:.2f} | {best[0]} ({best[1]['avg']:.2f}) | {worst[0]} ({worst[1]['avg']:.2f}) |")

    print("\n### Key Findings\n")

    # Hardest behavior
    hardest = sorted_behaviors[0]
    print(f"- **Hardest behavior**: {hardest} (avg {behavior_avgs[hardest]:.2f})")

    # Easiest behavior
    easiest = sorted_behaviors[-1]
    print(f"- **Easiest behavior**: {easiest} (avg {behavior_avgs[easiest]:.2f})")

    # Best overall model
    model_rankings = stats["model_rankings"]
    print(f"- **Best overall model**: {model_rankings[0][0]} ({model_rankings[0][1]:.2f})")
    print(f"- **Worst overall model**: {model_rankings[-1][0]} ({model_rankings[-1][1]:.2f})")

    # Gap between best and worst
    gap = model_rankings[0][1] - model_rankings[-1][1]
    print(f"- **Performance gap**: {gap:.2f} points between best and worst")


def main():
    print("Loading manipulation results...")
    results, stats = load_data()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating visualizations in {OUTPUT_DIR}/\n")

    # Generate all plots
    plot_heatmap(stats, OUTPUT_DIR / "01_manipulation_heatmap.png")
    # Radar chart removed - too cluttered
    plot_score_distributions(results, OUTPUT_DIR / "02_score_distributions.png")
    plot_commercial_optimization_breakdown(results, OUTPUT_DIR / "03_commercial_breakdown.png")
    plot_model_family_comparison(stats, OUTPUT_DIR / "04_family_comparison.png")
    # Failure analysis split into 3 separate figures
    plot_failure_rate_by_behavior(results, OUTPUT_DIR / "05a_failure_rate_by_behavior.png")
    plot_failure_categories(results, OUTPUT_DIR / "05b_failure_categories.png")
    plot_failures_by_model(results, OUTPUT_DIR / "05c_failures_by_model.png")

    # Generate summary table
    generate_summary_table(stats)

    print(f"\n✓ All visualizations saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
