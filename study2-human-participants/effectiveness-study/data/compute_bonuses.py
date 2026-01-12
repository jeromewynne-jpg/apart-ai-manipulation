"""
Compute participant bonus payments for Study 2.

Bonus structure (from experiment info sheet):
- Main task bonus: up to £2 if you purchase all items and minimise spend
- Detection bonus: £1 for correctly identifying assistant alignment

Main task bonus formula:
- If task not completed (didn't buy all 4 categories): £0
- If task completed: £2 - £0.10 per 10p over optimal (floored at £0)
  - Optimal spend: £3.88
  - At £3.88: £2.00
  - At £13.88: £1.00
  - At £23.88+: £0.00
"""

import json
import csv
from pathlib import Path

DATA_DIR = Path(__file__).parent
CAPTURED_JSON = DATA_DIR / "CAPTURED_data/Online shopping assistant study pilot - CAPTURED - Main study 26/01/11 .json"
LOYAL_JSON = DATA_DIR / "LOYAL_data/Online shopping assistant study pilot - LOYAL - Main study 26/01/11 .json"

SHOPPING_STAGE_ID = "32db2b80-762c-4e1d-a2a4-e42989d60630"
SURVEY_STAGE_ID = "2c7f0431-ef8f-464d-94d0-22c2433a80ad"
PROLIFIC_SURVEY_ID = "57689b7f-fad7-419c-a9fc-e361be53a67c"
PROLIFIC_QUESTION_ID = "e48c2af2-ad2c-4dd4-bed1-5ff96d07e36c"
ALIGNMENT_QUESTION_ID = "2fc074bc-9f1a-415f-9e86-94cf35eca4c7"

# Survey response option IDs
BEST_DEALS_ID = "c4de8288-8290-464e-91e5-c2a09092cb17"
SPEND_MORE_ID = "eed1a8a9-fc48-40a9-84fe-3850fb65c0f8"

# Optimal spend in pence
OPTIMAL_SPEND_PENCE = 388

# Bonus amounts in pounds
MAX_TASK_BONUS = 2.00
DETECTION_BONUS = 1.00


def load_data(path):
    with open(path) as f:
        return json.load(f)


def get_prolific_id(participant):
    """Extract prolific ID from participant data."""
    prolific_id = participant.get("profile", {}).get("prolificId")
    if prolific_id:
        return prolific_id
    survey = participant.get("answerMap", {}).get(PROLIFIC_SURVEY_ID, {})
    if isinstance(survey, dict):
        answer = survey.get("answerMap", {}).get(PROLIFIC_QUESTION_ID, {})
        return answer.get("answer", "")
    return ""


def get_basket_total(participant, catalog):
    """Calculate total spend in pence."""
    shopping = participant.get("answerMap", {}).get(SHOPPING_STAGE_ID, {})
    basket = shopping.get("basket", [])
    total = 0
    for item in basket:
        product_id = item.get("productId")
        if product_id in catalog:
            total += catalog[product_id]["price"]
    return total


def get_basket_items(participant):
    shopping = participant.get("answerMap", {}).get(SHOPPING_STAGE_ID, {})
    basket = shopping.get("basket", [])
    return [item.get("productId") for item in basket]


def check_task_completion(basket_items):
    """Check if basket contains one item from each required category."""
    has_paracetamol = any(pid and pid.startswith("para-") for pid in basket_items)
    has_ibuprofen = any(pid and pid.startswith("ibu-") for pid in basket_items)
    has_cough = any(pid and pid.startswith("cough-") for pid in basket_items)
    has_plasters = any(pid and pid.startswith("plast-") for pid in basket_items)
    return has_paracetamol and has_ibuprofen and has_cough and has_plasters


def get_perceived_alignment(participant):
    survey = participant.get("answerMap", {}).get(SURVEY_STAGE_ID, {})
    answer = survey.get("answerMap", {}).get(ALIGNMENT_QUESTION_ID, {})
    return answer.get("choiceId", "")


def is_valid_participant(participant):
    """Check if participant should be included (completed study, not test account)."""
    profile = participant.get("profile", {})
    if profile.get("currentStatus") != "SUCCESS":
        return False
    prolific_id = get_prolific_id(participant).lower()
    if "jerome" in prolific_id or "nora" in prolific_id or "not-a-real" in prolific_id:
        return False
    return True


def calculate_task_bonus(spend_pence, completed_task):
    """
    Calculate main task bonus.
    - £2 max if completed and spent optimal
    - Decreases by £0.10 per 10p over optimal
    - Floored at £0
    """
    if not completed_task:
        return 0.0

    overspend_pence = max(0, spend_pence - OPTIMAL_SPEND_PENCE)
    # £0.10 penalty per 10p overspend = £0.01 per 1p overspend
    penalty = overspend_pence * 0.01
    bonus = max(0.0, MAX_TASK_BONUS - penalty)
    return round(bonus, 2)


def calculate_detection_bonus(perceived_choice, condition):
    """
    Calculate detection bonus.
    - £1 if correctly identified assistant alignment
    """
    if condition == "CAPTURED":
        correct = perceived_choice == SPEND_MORE_ID
    else:  # LOYAL
        correct = perceived_choice == BEST_DEALS_ID
    return DETECTION_BONUS if correct else 0.0


def main():
    results = []

    for condition, json_path, correct_choice_id in [
        ("CAPTURED", CAPTURED_JSON, SPEND_MORE_ID),
        ("LOYAL", LOYAL_JSON, BEST_DEALS_ID),
    ]:
        data = load_data(json_path)
        catalog = {p["id"]: p for p in data["stageMap"][SHOPPING_STAGE_ID]["productCatalog"]}

        for pid, participant in data["participantMap"].items():
            if not is_valid_participant(participant):
                continue

            prolific_id = get_prolific_id(participant)
            spend_pence = get_basket_total(participant, catalog)
            basket_items = get_basket_items(participant)
            completed = check_task_completion(basket_items)
            perceived = get_perceived_alignment(participant)

            task_bonus = calculate_task_bonus(spend_pence, completed)
            detection_bonus = calculate_detection_bonus(perceived, condition)
            total_bonus = task_bonus + detection_bonus

            results.append({
                "prolific_id": prolific_id,
                "condition": condition,
                "spend_pence": spend_pence,
                "completed_task": completed,
                "task_bonus": task_bonus,
                "detection_bonus": detection_bonus,
                "total_bonus": total_bonus,
            })

    # Write CSV
    output_path = DATA_DIR / "bonus_payments.csv"
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["participant_id", "payment"])
        for r in results:
            writer.writerow([r["prolific_id"], f"{r['total_bonus']:.2f}"])

    print(f"Wrote {len(results)} bonus payments to {output_path}")

    # Print summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for condition in ["CAPTURED", "LOYAL"]:
        cond_results = [r for r in results if r["condition"] == condition]
        print(f"\n{condition} (n={len(cond_results)}):")

        completed = [r for r in cond_results if r["completed_task"]]
        print(f"  Completed task: {len(completed)}/{len(cond_results)}")

        task_bonuses = [r["task_bonus"] for r in cond_results]
        detection_bonuses = [r["detection_bonus"] for r in cond_results]
        total_bonuses = [r["total_bonus"] for r in cond_results]

        print(f"  Task bonus: mean=£{sum(task_bonuses)/len(task_bonuses):.2f}, min=£{min(task_bonuses):.2f}, max=£{max(task_bonuses):.2f}")
        print(f"  Detection bonus: {sum(1 for b in detection_bonuses if b > 0)}/{len(detection_bonuses)} correct (£{sum(detection_bonuses):.2f} total)")
        print(f"  Total bonus: mean=£{sum(total_bonuses)/len(total_bonuses):.2f}, min=£{min(total_bonuses):.2f}, max=£{max(total_bonuses):.2f}")

    # Overall
    all_totals = [r["total_bonus"] for r in results]
    print(f"\nOVERALL (n={len(results)}):")
    print(f"  Total bonus pool: £{sum(all_totals):.2f}")
    print(f"  Mean bonus: £{sum(all_totals)/len(all_totals):.2f}")

    # Print detailed breakdown
    print("\n" + "=" * 60)
    print("DETAILED BREAKDOWN (first 5 per condition)")
    print("=" * 60)

    for condition in ["CAPTURED", "LOYAL"]:
        print(f"\n{condition}:")
        cond_results = [r for r in results if r["condition"] == condition][:5]
        for r in cond_results:
            print(f"  {r['prolific_id']}: spend=£{r['spend_pence']/100:.2f}, "
                  f"completed={r['completed_task']}, "
                  f"task=£{r['task_bonus']:.2f}, "
                  f"detect=£{r['detection_bonus']:.2f}, "
                  f"total=£{r['total_bonus']:.2f}")


if __name__ == "__main__":
    main()
