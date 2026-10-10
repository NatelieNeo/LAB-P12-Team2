# ---------------------------------------------------------------------
# Deterministic output tags
# ---------------------------------------------------------------------
# Computed by OUR code from the AI's numeric output — never by asking
# the AI to self-categorize. Same numeric input -> same tag, every time.

def tag_calorie_range(calories: float) -> str:
    """Absolute per-dish calorie bracket (category 1)."""
    if calories < 400:
        return "Low (<400 kcal)"
    if calories <= 700:
        return "Moderate (400-700 kcal)"
    return "High (>700 kcal)"


def tag_calorie_fit(calories: float, per_meal_calorie_target: float, tolerance: float = CALORIE_FIT_TOLERANCE) -> str:
    """Calorie Target Fit Tag (category 2) — relative to THIS user's own
    per-meal target, not an absolute scale."""
    lower = per_meal_calorie_target * (1 - tolerance)
    upper = per_meal_calorie_target * (1 + tolerance)
    if calories < lower:
        return "under_target"
    if calories > upper:
        return "over_target"
    return "on_target"


def tag_protein(protein_g: float) -> str:
    if protein_g < 10:
        return "Low (<10g)"
    if protein_g <= 25:
        return "Medium (10-25g)"
    return "High (>25g)"


def tag_carbs(carbs_g: float) -> str:
    if carbs_g < 15:
        return "Low (<15g)"
    if carbs_g <= 40:
        return "Medium (15-40g)"
    return "High (>40g)"


def tag_fat(fat_g: float) -> str:
    if fat_g < 5:
        return "Low (<5g)"
    if fat_g <= 15:
        return "Medium (5-15g)"
    return "High (>15g)"


def tag_cost(estimated_cost: Optional[float]) -> str:
    """Cost Tier (category 4). A missing/unknown cost is labeled rather
    than guessed."""
    if estimated_cost is None:
        return "Unknown"
    if estimated_cost < 15:
        return "Budget (<$15)"
    if estimated_cost <= 30:
        return "Moderate ($15-$30)"
    return "Premium (>$30)"


def find_pantry_ingredients_used(ingredients: Optional[List[Any]], pantry_ingredients: List[str]) -> List[str]:
    """Deterministic, case-insensitive, substring match between the
    user's own "ingredients on hand" list and a dish's ingredients — NOT
    the AI's self-reported pantry_ingredients_used field, which isn't
    trusted here since the user's actual pantry list is the one
    authoritative source. Substring (not exact) matching so a pantry
    entry of "chicken" also matches a longer ingredient name like
    "chicken breast". Returns the pantry item as the user typed it
    (e.g. "chicken"), matching the display example."""
    ingredient_names_lower = [name.lower() for name in get_ingredient_names(ingredients)]
    used = []
    for pantry_item in pantry_ingredients or []:
        pantry_lower = str(pantry_item).lower()
        if any(pantry_lower in ingredient for ingredient in ingredient_names_lower):
            used.append(pantry_item)
    return used


def annotate_meal(
    candidate: Dict[str, Any], per_meal_calorie_target: float, pantry_ingredients: List[str]
) -> Dict[str, Any]:
    """Build the FINAL, output-facing dish dict for one chosen candidate
    — tags and name/source only, no raw numbers, so the displayed dish
    is robust to small run-to-run drift in the AI's own estimate (a
    fixed tag from the same bucket of numbers is always the same tag)."""
    return {
        "name": candidate.get("meal_name"),
        "source_type": candidate.get("meal_source_type"),
        "calorie_range": tag_calorie_range(candidate.get("calories", 0)),
        "calorie_tag": tag_calorie_fit(candidate.get("calories", 0), per_meal_calorie_target),
        "protein_tag": tag_protein(candidate.get("protein_g", 0)),
        "carbs_tag": tag_carbs(candidate.get("carbs_g", 0)),
        "fat_tag": tag_fat(candidate.get("fat_g", 0)),
        "cost_tier": tag_cost(candidate.get("estimated_cost")),
        "pantry_ingredients_used": find_pantry_ingredients_used(candidate.get("ingredients"), pantry_ingredients),
    }


# ---------------------------------------------------------------------
# Whole-plan assembly
# ---------------------------------------------------------------------

def build_plan_explanation(
    total_calories: float,
    daily_calorie_target: float,
    total_cost: Optional[float],
    daily_budget: Optional[float],
    within_budget: bool,
) -> str:
    """Compose the plain-language summary line shown at the top of the
    plan — built entirely from data already computed, not an extra AI
    call, so it's as deterministic as everything else here."""
    parts = [f"Totals {total_calories:.0f} kcal against a {daily_calorie_target:.0f} kcal daily target"]
    if daily_budget is not None and total_cost is not None:
        status = "within" if within_budget else "over"
        parts.append(f"an estimated {total_cost:.2f} — {status} your {daily_budget:.2f} daily budget")
    return "; ".join(parts) + "."


def build_meal_plan(
    recommendations: List[Dict[str, Any]], user_profile: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Public entry point. Takes the AI's raw `recommendations` list
    (ai_response.json's shape) plus the user_profile io_manager.py
    collected, and returns ONE full-day meal plan: the single best dish
    per slot, ranked by nutrition fit first and cost second, with the
    daily budget checked as a whole (budget is the SECONDARY factor —
    it never overrides which dish best matches the user's calorie/macro
    target, it only breaks ties and flags whether the resulting day's
    total fits).

    Returns None only if every slot ends up with zero usable candidates
    (e.g. dietary restrictions or source preference filtered everything
    out everywhere) — otherwise returns a plan covering whichever slots
    DO have a pick, with `is_complete`/`missing_slots` reporting the gap
    honestly rather than pretending a partial plan is a full one.
    """
    
    targets = calculate_targets(user_profile)
    per_meal_calorie_target = targets["per_meal_calorie_target"]
    per_meal_macro_targets = targets["per_meal_macro_targets"]
    daily_calorie_target = targets["daily_calorie_target"]

    dietary_restrictions = user_profile.get("dietary_restrictions") or []
    meal_source_preference = user_profile.get("meal_source", "both")
    pantry_ingredients = user_profile.get("pantry_ingredients") or []
    daily_budget = user_profile.get("daily_budget")

    grouped = group_candidates_by_slot(recommendations)

    chosen: Dict[str, Dict[str, Any]] = {}
    missing_slots: List[str] = []
    for slot in MEAL_SLOTS:
        ranked = rank_slot_candidates(
            grouped.get(slot, []),
            per_meal_calorie_target,
            per_meal_macro_targets,
            dietary_restrictions,
            meal_source_preference,
        )
        top = select_top_candidate(ranked)
        if top is None:
            missing_slots.append(slot)
        else:
            chosen[slot] = top

    if not chosen:
        return None

    # Plan-level totals are computed from the raw chosen candidates
    # BEFORE annotate_meal strips the numbers for the per-dish display —
    # these totals are the one deliberate exception to the tags-only
    # rule, same as the per-dish tagging design above.
    total_calories = sum(chosen[slot].get("calories", 0) for slot in chosen)
    costs = [chosen[slot]["estimated_cost"] for slot in chosen if chosen[slot].get("estimated_cost") is not None]
    total_cost = sum(costs) if costs else None

    within_budget = True
    if daily_budget is not None and total_cost is not None:
        within_budget = total_cost <= daily_budget

    meals = {
        slot: annotate_meal(chosen[slot], per_meal_calorie_target, pantry_ingredients)
        for slot in chosen
    }

    return {
        "meals": meals,
        "is_complete": not missing_slots,
        "missing_slots": missing_slots,
        "daily_calorie_target": daily_calorie_target,
        "total_calories": total_calories,
        "daily_budget": daily_budget,
        "total_cost": total_cost,
        "within_budget": within_budget,
        "explanation": build_plan_explanation(
            total_calories, daily_calorie_target, total_cost, daily_budget, within_budget
        ),
    }


def format_meal_plan(plan):
    lines = [
        "=== Your Meal Plan ===",
        f"Why this plan: {plan['explanation']}",
    ]

    for slot in ("breakfast", "lunch", "dinner"):
        meal = plan["meals"].get(slot)
        if meal is None:
            continue

        lines.extend([
            "",
            f"{slot.capitalize()}: {meal['name']} ({meal['source_type']})",
            f"Calories: {meal['calorie_range']} — {meal['calorie_tag']} for your target",
            "Macros: "
            f"Protein {meal['protein_tag']} / "
            f"Carbs {meal['carbs_tag']} / "
            f"Fat {meal['fat_tag']}",
        ])

        pantry = meal.get("pantry_ingredients_used", [])
        if pantry:
            lines.append(f"Uses from your pantry: {', '.join(pantry)}")

        lines.append(f"Cost: {meal['cost_tier']}")

    missing_slots = plan.get("missing_slots", [])
    if missing_slots:
        lines.extend([
            "",
            "Missing meals: " + ", ".join(missing_slots),
        ])

    return "\n".join(lines)

