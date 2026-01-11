"""
Analysis script for Study 1: Human-Model Judge Calibration

Calculates inter-annotator agreement (IAA) and analyzes correlation
between human raters and AI judge using downloaded submissions.

Usage:
    python analyze_results.py                    # Analyze downloaded data
    python analyze_results.py --output results/  # Custom output directory

Prerequisites:
    Run `python download_results.py` first to download submissions.

Outputs:
    - human_annotations.csv: All human annotations
    - scenario_summary.csv: Per-scenario aggregated results
    - analysis_report.md: Full analysis report with statistics
"""

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

# Suppress warnings
warnings.filterwarnings("ignore")

SCRIPT_DIR = Path(__file__).parent


def load_from_submissions_json() -> pd.DataFrame:
    """Load annotations from the downloaded submissions.json file."""
    submissions_file = SCRIPT_DIR / "results" / "submissions.json"

    if not submissions_file.exists():
        raise FileNotFoundError(
            f"No submissions file found at {submissions_file}\n"
            "Run `python download_results.py` first to download submissions."
        )

    with open(submissions_file) as f:
        data = json.load(f)

    submissions = data.get("submissions", [])
    print(f"Loaded {len(submissions)} submissions from {submissions_file}")
    print(f"Last updated: {data.get('last_updated', 'unknown')}")

    # Convert to the format expected by analysis functions
    annotations = []
    for s in submissions:
        annotation = {
            "participant_id": s["participant"].replace("participant-", ""),
            "scenario_id": s["scenario_id"],
            "score": s["score"],
            "pass_criteria_met": s.get("pass_criteria_met", []),
            "fail_criteria_triggered": s.get("fail_criteria_triggered", []),
            "explanation": s.get("explanation", ""),
            "ai_judge_score": s.get("ai_score"),
            "behavior": s.get("behavior"),
            "difficulty": s.get("difficulty"),
        }
        annotations.append(annotation)

    return pd.DataFrame(annotations)


def load_scenario_data() -> pd.DataFrame:
    """Load scenario metadata from scenarios.json."""
    scenarios_file = SCRIPT_DIR / "scenarios.json"

    if not scenarios_file.exists():
        print("Warning: scenarios.json not found")
        return pd.DataFrame()

    with open(scenarios_file) as f:
        scenarios = json.load(f)

    return pd.DataFrame(scenarios)


def calculate_iaa(df: pd.DataFrame) -> dict:
    """
    Calculate inter-annotator agreement statistics.

    Returns dict with:
        - krippendorff_alpha: Krippendorff's alpha for ordinal data
        - fleiss_kappa: Fleiss' kappa for categorical agreement
        - pairwise_agreement: Average pairwise exact agreement
        - correlation_matrix: Pairwise correlations between raters
    """
    from scipy import stats

    results = {}

    # Pivot to get rater × scenario matrix
    # Each scenario should have multiple ratings
    pivot = df.pivot_table(
        index='scenario_id',
        columns='participant_id',
        values='score',
        aggfunc='first'
    )

    print(f"Rating matrix: {pivot.shape[0]} scenarios × {pivot.shape[1]} raters")

    # 1. Average pairwise agreement (exact match)
    scores_by_scenario = df.groupby('scenario_id')['score'].apply(list)
    exact_agreements = []
    for scores in scores_by_scenario:
        if len(scores) < 2:
            continue
        # Count pairs that agree
        n_pairs = 0
        n_agree = 0
        for i in range(len(scores)):
            for j in range(i + 1, len(scores)):
                n_pairs += 1
                if scores[i] == scores[j]:
                    n_agree += 1
        if n_pairs > 0:
            exact_agreements.append(n_agree / n_pairs)

    results['pairwise_exact_agreement'] = np.mean(exact_agreements) if exact_agreements else None

    # 2. Average pairwise agreement (within 1 point)
    within_one_agreements = []
    for scores in scores_by_scenario:
        if len(scores) < 2:
            continue
        n_pairs = 0
        n_agree = 0
        for i in range(len(scores)):
            for j in range(i + 1, len(scores)):
                n_pairs += 1
                if abs(scores[i] - scores[j]) <= 1:
                    n_agree += 1
        if n_pairs > 0:
            within_one_agreements.append(n_agree / n_pairs)

    results['pairwise_within_one_agreement'] = np.mean(within_one_agreements) if within_one_agreements else None

    # 3. Krippendorff's alpha (ordinal)
    try:
        # Need to format data for krippendorff
        # Rows = raters, columns = items
        reliability_data = pivot.T.values  # raters × scenarios

        # Simple alpha calculation for ordinal data
        # Using simplified formula
        n_raters, n_items = reliability_data.shape

        # Count observed disagreement
        observed_disagreement = 0
        n_pairs_total = 0

        for item in range(n_items):
            ratings = reliability_data[:, item]
            valid_ratings = ratings[~np.isnan(ratings)]
            if len(valid_ratings) < 2:
                continue

            for i in range(len(valid_ratings)):
                for j in range(i + 1, len(valid_ratings)):
                    observed_disagreement += (valid_ratings[i] - valid_ratings[j]) ** 2
                    n_pairs_total += 1

        if n_pairs_total > 0:
            observed_disagreement /= n_pairs_total

        # Expected disagreement (if random)
        all_ratings = reliability_data.flatten()
        all_ratings = all_ratings[~np.isnan(all_ratings)]

        expected_disagreement = 0
        n_expected_pairs = 0
        for i in range(len(all_ratings)):
            for j in range(i + 1, len(all_ratings)):
                expected_disagreement += (all_ratings[i] - all_ratings[j]) ** 2
                n_expected_pairs += 1

        if n_expected_pairs > 0:
            expected_disagreement /= n_expected_pairs

        if expected_disagreement > 0:
            alpha = 1 - (observed_disagreement / expected_disagreement)
            results['krippendorff_alpha'] = alpha
        else:
            results['krippendorff_alpha'] = 1.0  # Perfect agreement

    except Exception as e:
        print(f"Warning: Could not calculate Krippendorff's alpha: {e}")
        results['krippendorff_alpha'] = None

    # 4. Score distribution stats
    results['score_mean'] = df['score'].mean()
    results['score_std'] = df['score'].std()
    results['score_distribution'] = df['score'].value_counts().sort_index().to_dict()

    return results


def calculate_human_ai_agreement(df: pd.DataFrame) -> dict:
    """
    Calculate agreement between human raters and AI judge.

    Returns dict with:
        - pearson_correlation: Pearson r between mean human score and AI score
        - spearman_correlation: Spearman rho (rank correlation)
        - mean_absolute_error: Average |human - AI| difference
        - confusion_matrix: 5x5 matrix of human vs AI scores
        - agreement_by_category: Agreement rates for pass/borderline/fail
    """
    from scipy import stats

    results = {}

    # Get mean human score per scenario
    scenario_means = df.groupby('scenario_id').agg({
        'score': ['mean', 'std', 'count'],
        'ai_judge_score': 'first'
    }).reset_index()

    scenario_means.columns = ['scenario_id', 'human_mean', 'human_std', 'n_raters', 'ai_score']

    # Convert AI score to numeric
    scenario_means['ai_score'] = pd.to_numeric(scenario_means['ai_score'], errors='coerce')

    # Drop scenarios without AI scores
    valid = scenario_means.dropna(subset=['ai_score', 'human_mean'])

    if len(valid) < 3:
        print("Warning: Not enough data for human-AI agreement analysis")
        return results

    human_scores = valid['human_mean'].values
    ai_scores = valid['ai_score'].values

    # 1. Pearson correlation
    r, p_value = stats.pearsonr(human_scores, ai_scores)
    results['pearson_r'] = r
    results['pearson_p'] = p_value

    # 2. Spearman correlation
    rho, p_value_spearman = stats.spearmanr(human_scores, ai_scores)
    results['spearman_rho'] = rho
    results['spearman_p'] = p_value_spearman

    # 3. Mean absolute error
    results['mae'] = np.mean(np.abs(human_scores - ai_scores))

    # 4. Root mean squared error
    results['rmse'] = np.sqrt(np.mean((human_scores - ai_scores) ** 2))

    # 5. Agreement within 1 point
    results['within_one_agreement'] = np.mean(np.abs(human_scores - ai_scores) <= 1)

    # 6. Exact agreement (rounded human mean)
    human_rounded = np.round(human_scores)
    results['exact_agreement'] = np.mean(human_rounded == ai_scores)

    # 7. Category agreement (pass/borderline/fail)
    def categorize(score):
        if score >= 4:
            return 'pass'
        elif score <= 2:
            return 'fail'
        else:
            return 'borderline'

    human_categories = [categorize(s) for s in human_scores]
    ai_categories = [categorize(s) for s in ai_scores]

    category_agreement = np.mean([h == a for h, a in zip(human_categories, ai_categories)])
    results['category_agreement'] = category_agreement

    # 8. Confusion by AI score category
    results['confusion_by_ai_category'] = {}
    for ai_cat in ['pass', 'borderline', 'fail']:
        mask = [categorize(s) == ai_cat for s in ai_scores]
        if sum(mask) > 0:
            human_in_cat = [h for h, m in zip(human_scores, mask) if m]
            results['confusion_by_ai_category'][ai_cat] = {
                'n': sum(mask),
                'human_mean': np.mean(human_in_cat),
                'human_std': np.std(human_in_cat),
            }

    # 9. Where do humans and AI disagree most?
    valid['disagreement'] = np.abs(valid['human_mean'] - valid['ai_score'])
    top_disagreements = valid.nlargest(10, 'disagreement')[['scenario_id', 'human_mean', 'ai_score', 'disagreement']]
    results['top_disagreements'] = top_disagreements.to_dict('records')

    return results


def generate_report(
    annotations_df: pd.DataFrame,
    iaa_results: dict,
    human_ai_results: dict,
    output_path: Path
) -> str:
    """Generate markdown analysis report."""

    report = []
    report.append("# Human-AI Judge Calibration Study: Analysis Report\n")
    report.append(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Overview
    report.append("## Overview\n")
    n_annotations = len(annotations_df)
    n_participants = annotations_df['participant_id'].nunique()
    n_scenarios = annotations_df['scenario_id'].nunique()

    report.append(f"- **Total annotations:** {n_annotations}")
    report.append(f"- **Participants:** {n_participants}")
    report.append(f"- **Scenarios rated:** {n_scenarios}")
    report.append(f"- **Average ratings per scenario:** {n_annotations / n_scenarios:.1f}\n")

    # Score distribution
    report.append("## Human Score Distribution\n")
    report.append("| Score | Count | Percentage |")
    report.append("|-------|-------|------------|")
    score_dist = annotations_df['score'].value_counts().sort_index()
    for score, count in score_dist.items():
        pct = count / n_annotations * 100
        report.append(f"| {score} | {count} | {pct:.1f}% |")
    report.append("")

    # IAA Results
    report.append("## Inter-Annotator Agreement (IAA)\n")

    if iaa_results.get('krippendorff_alpha') is not None:
        alpha = iaa_results['krippendorff_alpha']
        interpretation = "excellent" if alpha > 0.8 else "good" if alpha > 0.6 else "moderate" if alpha > 0.4 else "fair" if alpha > 0.2 else "poor"
        report.append(f"- **Krippendorff's α:** {alpha:.3f} ({interpretation})")

    if iaa_results.get('pairwise_exact_agreement') is not None:
        report.append(f"- **Pairwise exact agreement:** {iaa_results['pairwise_exact_agreement']:.1%}")

    if iaa_results.get('pairwise_within_one_agreement') is not None:
        report.append(f"- **Pairwise within-1 agreement:** {iaa_results['pairwise_within_one_agreement']:.1%}")

    report.append("")

    # Human-AI Agreement
    report.append("## Human-AI Judge Agreement\n")

    if human_ai_results.get('pearson_r') is not None:
        r = human_ai_results['pearson_r']
        p = human_ai_results['pearson_p']
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        report.append(f"- **Pearson correlation:** r = {r:.3f}{sig} (p = {p:.4f})")

    if human_ai_results.get('spearman_rho') is not None:
        rho = human_ai_results['spearman_rho']
        p = human_ai_results['spearman_p']
        sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        report.append(f"- **Spearman correlation:** ρ = {rho:.3f}{sig} (p = {p:.4f})")

    if human_ai_results.get('mae') is not None:
        report.append(f"- **Mean Absolute Error:** {human_ai_results['mae']:.2f} points")

    if human_ai_results.get('within_one_agreement') is not None:
        report.append(f"- **Agreement within 1 point:** {human_ai_results['within_one_agreement']:.1%}")

    if human_ai_results.get('category_agreement') is not None:
        report.append(f"- **Category agreement (pass/borderline/fail):** {human_ai_results['category_agreement']:.1%}")

    report.append("")

    # Disagreement analysis
    if human_ai_results.get('top_disagreements'):
        report.append("### Largest Human-AI Disagreements\n")
        report.append("| Scenario ID | Human Mean | AI Score | Difference |")
        report.append("|-------------|------------|----------|------------|")
        for d in human_ai_results['top_disagreements'][:5]:
            report.append(f"| {d['scenario_id']} | {d['human_mean']:.2f} | {d['ai_score']:.0f} | {d['disagreement']:.2f} |")
        report.append("")

    # Interpretation
    report.append("## Interpretation\n")

    if human_ai_results.get('pearson_r') is not None:
        r = human_ai_results['pearson_r']
        if r > 0.7:
            report.append("✅ **Strong correlation** between human and AI judge ratings suggests the AI judge is well-calibrated with human judgment.\n")
        elif r > 0.5:
            report.append("⚠️ **Moderate correlation** between human and AI judge ratings. The AI judge captures the general trend but may miss nuances.\n")
        else:
            report.append("❌ **Weak correlation** between human and AI judge ratings suggests significant calibration issues.\n")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Analyze human calibration study results")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=SCRIPT_DIR / "results",
        help="Output directory for results"
    )
    args = parser.parse_args()

    # Create output directory
    args.output.mkdir(exist_ok=True)

    print("=" * 70)
    print("STUDY 1: HUMAN-AI JUDGE CALIBRATION ANALYSIS")
    print("=" * 70)

    # Load downloaded submissions
    print("\nLoading submissions...")
    try:
        annotations_df = load_from_submissions_json()
    except FileNotFoundError as e:
        print(f"\n{e}")
        return

    if len(annotations_df) == 0:
        print("No annotations found. Has anyone completed the study yet?")
        return

    # Save as CSV for reference
    csv_path = args.output / "human_annotations.csv"
    annotations_df.to_csv(csv_path, index=False)
    print(f"Saved annotations to {csv_path}")

    # Run analysis
    print("\nCalculating inter-annotator agreement...")
    iaa_results = calculate_iaa(annotations_df)

    print("\nCalculating human-AI agreement...")
    human_ai_results = calculate_human_ai_agreement(annotations_df)

    # Generate per-scenario summary
    print("\nGenerating scenario summary...")
    scenario_summary = annotations_df.groupby('scenario_id').agg({
        'score': ['mean', 'std', 'count'],
        'ai_judge_score': 'first',
        'behavior': 'first',
    }).reset_index()
    scenario_summary.columns = ['scenario_id', 'human_mean', 'human_std', 'n_ratings', 'ai_score', 'behavior']
    scenario_summary['ai_score'] = pd.to_numeric(scenario_summary['ai_score'], errors='coerce')
    scenario_summary['difference'] = scenario_summary['human_mean'] - scenario_summary['ai_score']

    summary_path = args.output / "scenario_summary.csv"
    scenario_summary.to_csv(summary_path, index=False)
    print(f"Saved scenario summary to {summary_path}")

    # Generate report
    print("\nGenerating analysis report...")
    report = generate_report(annotations_df, iaa_results, human_ai_results, args.output)

    report_path = args.output / "analysis_report.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Saved report to {report_path}")

    # Save raw results as JSON
    results_json = {
        "iaa": {k: v if not isinstance(v, np.floating) else float(v)
                for k, v in iaa_results.items() if k != 'score_distribution'},
        "human_ai": {k: v if not isinstance(v, (np.floating, np.ndarray)) else float(v) if isinstance(v, np.floating) else v
                     for k, v in human_ai_results.items() if k != 'top_disagreements'},
    }

    json_path = args.output / "analysis_results.json"
    with open(json_path, "w") as f:
        json.dump(results_json, f, indent=2, default=str)
    print(f"Saved raw results to {json_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"\nAnnotations: {len(annotations_df)}")
    print(f"Participants: {annotations_df['participant_id'].nunique()}")
    print(f"Scenarios: {annotations_df['scenario_id'].nunique()}")

    if iaa_results.get('krippendorff_alpha') is not None:
        print(f"\nKrippendorff's α: {iaa_results['krippendorff_alpha']:.3f}")

    if human_ai_results.get('pearson_r') is not None:
        print(f"Human-AI correlation: r = {human_ai_results['pearson_r']:.3f}")

    if human_ai_results.get('category_agreement') is not None:
        print(f"Category agreement: {human_ai_results['category_agreement']:.1%}")

    print(f"\n✅ Analysis complete! Results saved to {args.output}/")


if __name__ == "__main__":
    main()
