"""
logic_manager.py — Logic Layer (Calora)

Responsibilities:
- Calculate the user's BMR -> TDEE -> daily calorie target -> per-meal
  calorie/macro targets from the profile io_manager.py collects.
- Take the AI's raw `recommendations` list — the shape ai_manager.py's
  Gemini prompt actually returns (see ai_response.json): meal_type,
  meal_name, meal_source_type, calories, protein_g, carbs_g, fat_g,
  estimated_cost, ingredients as [{item, quantity, unit}, ...],
  pantry_ingredients_used, portion_size, recipe_steps — and turn it into
  ONE ranked meal plan: one dish for breakfast, one for lunch, one for
  dinner (the "Snack" meal_type in a 10-dish response is not one of the
  three slots and is dropped, never forced into one).
- Apply the business rules, in order: dietary safety (hard filter) ->
  meal-source preference (hard filter) -> rank by nutrition fit
  (calorie-fit distance, then macro-fit distance) with cost as the
  secondary factor, breaking ties between otherwise-equally-good options.
- Tag every CHOSEN dish deterministically (calorie range, calorie-fit,
  protein/carbs/fat tier, cost tier) using the fixed thresholds below —
  never by asking the AI to self-categorize, so the same numbers always
  produce the same tags on every run.

100% procedural — no classes anywhere in this file, only functions and
plain dicts/lists. This file never calls print()/input() (that's
io_manager.py's job) and never calls the AI API (that's ai_manager.py's
job) — it only transforms the AI's recommendations into a plan and
hands back plain dicts for io_manager.py to display and data_manager.py
to persist.

Expected user_profile shape (built in main.py from io_manager.py's
collectors):
    {
        "name": str, "age": int, "gender": str, "weight_kg": float,
        "height_cm": float, "activity_level": str, "goal": str,
        "dietary_restrictions": list[str], "meal_preference": str,
        "meal_source": str,          # "eat_out" | "home_cooked" | "both"
        "pantry_ingredients": list[str],
        "daily_budget": float | None,
    }

Public entry point: build_meal_plan(recommendations, user_profile).
  
  """

from typing import Any, Dict, List, Optional

# Fixed assumption: exactly 3 meals a day (breakfast/lunch/dinner). A
# "Snack" or any other meal_type the AI returns is not one of these
# three slots and is excluded from the plan, not merged into one.
MEAL_SLOTS = ["breakfast", "lunch", "dinner"]

# How far (as a fraction of the per-meal target) a dish's calories may sit and still count as "on_target" rather than under/over.
CALORIE_FIT_TOLERANCE = 0.20

# ---------------------------------------------------------------------
# BMR / TDEE / target math
# ---------------------------------------------------------------------

# Activity multipliers used to convert BMR -> TDEE.
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

# Calorie adjustment applied on top of TDEE, by goal type.
GOAL_ADJUSTMENTS = {
    "lose": -500,
    "maintain": 0,
    "gain": 300,
}

# Macro split (protein/carbs/fat as a fraction of total calories) by goal
# type. "gain" is weighted toward protein deliberately, so muscle-gain
# users are actually steered toward higher-protein recommendations, not
# just a bigger calorie surplus with the same macro ratio as maintenance.
MACRO_SPLITS = {
    "lose": {"protein": 0.35, "carbs": 0.35, "fat": 0.30},
    "maintain": {"protein": 0.30, "carbs": 0.40, "fat": 0.30},
    "gain": {"protein": 0.35, "carbs": 0.40, "fat": 0.25},
}

def calculate_bmr(gender: str, weight_kg: float, height_cm: float, age: int) -> float:
    """Mifflin-St Jeor BMR formula. Case-insensitive on gender so an
    unnormalized value ("Male", "MALE") never silently falls through to
    the female formula."""
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    return base + 5 if str(gender).lower() == "male" else base - 161


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Scale BMR by an activity multiplier to estimate TDEE. Unknown
    activity levels default to "sedentary" (1.2) rather than crashing."""
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, ACTIVITY_MULTIPLIERS["sedentary"])
    return bmr * multiplier


def calculate_daily_calorie_target(tdee: float, goal: str) -> float:
    """Apply the goal-based adjustment (deficit/surplus/none) on top of TDEE."""
    return tdee + GOAL_ADJUSTMENTS.get(goal, 0)


def calculate_per_meal_calorie_target(daily_calorie_target: float) -> float:
    """Split the daily calorie target evenly across the fixed 3 meals/day."""
    return daily_calorie_target / len(MEAL_SLOTS)


def calculate_macro_targets(calorie_amount: float, goal: str) -> Dict[str, float]:
    """Split a calorie figure (daily OR per-meal — caller decides which)
    into grams of protein/carbs/fat using the goal's macro split.
    Protein and carbs are 4 kcal/g, fat is 9 kcal/g."""
    split = MACRO_SPLITS.get(goal, MACRO_SPLITS["maintain"])
    return {
        "protein_g": round((calorie_amount * split["protein"]) / 4, 1),
        "carbs_g": round((calorie_amount * split["carbs"]) / 4, 1),
        "fat_g": round((calorie_amount * split["fat"]) / 9, 1),
    }

def calculate_targets(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Run the full BMR -> TDEE -> daily target -> per-meal target/macros
    pipeline for one user_profile. This is the single source of truth
    for "what should this user be eating" — never the AI's own
    estimated_nutrition_targets guess, so the same profile always
    produces the same targets regardless of what a given AI call
    happens to estimate that run."""
    bmr = calculate_bmr(
        user_profile["gender"], user_profile["weight_kg"], user_profile["height_cm"], user_profile["age"]
    )
    tdee = calculate_tdee(bmr, user_profile["activity_level"])
    daily_calorie_target = calculate_daily_calorie_target(tdee, user_profile["goal"])
    per_meal_calorie_target = calculate_per_meal_calorie_target(daily_calorie_target)
    per_meal_macro_targets = calculate_macro_targets(per_meal_calorie_target, user_profile["goal"])
    return {
        "bmr": bmr,
        "tdee": tdee,
        "daily_calorie_target": daily_calorie_target,
        "per_meal_calorie_target": per_meal_calorie_target,
        "per_meal_macro_targets": per_meal_macro_targets,
    }

# ---------------------------------------------------------------------
# Normalizing the AI's raw recommendation shape
# ---------------------------------------------------------------------

def get_ingredient_names(ingredients: Optional[List[Any]]) -> List[str]:
    """Reduce the AI's ingredients list — each entry either a plain
    string or a {"item": ..., "quantity": ..., "unit": ...} object (the
    real ai_response.json shape) — to plain ingredient-name strings.
    Quantity/unit are discarded; no business rule needs them."""
    names: List[str] = []
    for ingredient in ingredients or []:
        if isinstance(ingredient, dict):
            item = ingredient.get("item")
            if item:
                names.append(str(item))
        elif isinstance(ingredient, str) and ingredient:
            names.append(ingredient)
    return names


def group_candidates_by_slot(recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Split the AI's single flat `recommendations` list into per-slot
    buckets keyed by MEAL_SLOTS, matching meal_type case-insensitively
    ("Breakfast" -> "breakfast"). A meal_type that isn't one of the
    three fixed slots (e.g. "Snack") is simply not one of the buckets —
    dropped here, not folded into a real slot."""
    grouped: Dict[str, List[Dict[str, Any]]] = {slot: [] for slot in MEAL_SLOTS}
    for candidate in recommendations or []:
        slot = str(candidate.get("meal_type", "")).strip().lower()
        if slot in grouped:
            grouped[slot].append(candidate)
    return grouped

# ---------------------------------------------------------------------
# Business rules (applied within one meal slot's candidates)
# ---------------------------------------------------------------------

def apply_dietary_safety_rule(
    candidates: List[Dict[str, Any]], dietary_restrictions: List[str]
) -> List[Dict[str, Any]]:
    """Rule: exclude any candidate whose ingredients OR dish name contain
    a restricted item. Substring matching (not exact match) so a
    "peanut" restriction also catches an ingredient listed as "peanut
    butter", and checking the dish name too catches a case like "Peanut
    Butter Toast" even if "peanut butter" never appears as its own
    ingredient entry."""
    if not dietary_restrictions:
        return candidates
    restricted_lower = [r.lower() for r in dietary_restrictions]
    safe = []
    for candidate in candidates:
        haystack = [name.lower() for name in get_ingredient_names(candidate.get("ingredients"))]
        haystack.append(str(candidate.get("meal_name", "")).lower())
        if not any(restricted in text for restricted in restricted_lower for text in haystack):
            safe.append(candidate)
    return safe

def apply_source_preference_rule(
    candidates: List[Dict[str, Any]], meal_source_preference: str
) -> List[Dict[str, Any]]:
    """Rule: enforce the user's eat-out-only / home-cooked-only choice.
    "both" (or anything else unrecognized) means no restriction."""
    if not meal_source_preference or meal_source_preference == "both":
        return candidates
    return [c for c in candidates if c.get("meal_source_type") == meal_source_preference]

def calculate_calorie_distance(candidate: Dict[str, Any], per_meal_calorie_target: float) -> float:
    """Absolute difference between a candidate's calories and the
    per-meal target. Lower is a better fit."""
    return abs(candidate.get("calories", 0) - per_meal_calorie_target)

def calculate_macro_distance(candidate: Dict[str, Any], macro_targets: Dict[str, float]) -> float:
    """Sum of absolute gram differences between a candidate's macros and
    the target macros (protein + carbs + fat). Lower is a better fit —
    this is what makes the BMR/TDEE-derived macro target actually count
    toward which dish wins, not just a number nobody uses."""
    protein_diff = abs(candidate.get("protein_g", 0) - macro_targets.get("protein_g", 0))
    carbs_diff = abs(candidate.get("carbs_g", 0) - macro_targets.get("carbs_g", 0))
    fat_diff = abs(candidate.get("fat_g", 0) - macro_targets.get("fat_g", 0))
    return protein_diff + carbs_diff + fat_diff

def cost_component(candidate: Dict[str, Any]) -> float:
    """A candidate with an unknown (None) estimated_cost is ranked last
    on cost, not treated as free — `cost or float("inf")` would be wrong
    here too, since a genuinely free ($0) dish is falsy and would
    otherwise be mistaken for "unknown"."""
    cost = candidate.get("estimated_cost")
    return float("inf") if cost is None else cost

def rank_slot_candidates(
    candidates: List[Dict[str, Any]],
    per_meal_calorie_target: float,
    macro_targets: Dict[str, float],
    dietary_restrictions: List[str],
    meal_source_preference: str,
) -> List[Dict[str, Any]]:
    """Apply the hard filters (dietary safety, source preference) for
    ONE meal slot's raw AI candidates, then rank what's left.

    Ranking key, in priority order:
      1. Calorie-fit distance (primary) — how close to the per-meal
         calorie target, since hitting the user's calorie goal is the
         core purpose of the plan.
      2. Macro-fit distance (still nutrition, not cost) — how close to
         the per-meal protein/carbs/fat target, so a goal like "gain"
         actually favors protein-forward dishes, not just any dish at
         the right calorie count.
      3. Cost (secondary factor, exactly as specified) — the final
         tiebreaker between otherwise similarly-good options, cheaper
         wins.

    If the source-preference filter would remove every candidate in this
    slot, it's skipped so a dietary-safe-but-wrong-source dish still
    gets ranked rather than leaving the slot with zero options — the
    preference remains a soft/ranking-level nudge in that edge case, but
    a normal AI response (which is asked to honor the preference already)
    will rarely need this fallback. 
    """
    safe = apply_dietary_safety_rule(candidates, dietary_restrictions)
    preferred = apply_source_preference_rule(safe, meal_source_preference)
    pool = preferred if preferred else safe

    scored = []
    for candidate in pool:
        annotated = dict(candidate)
        annotated["_calorie_distance"] = calculate_calorie_distance(candidate, per_meal_calorie_target)
        annotated["_macro_distance"] = calculate_macro_distance(candidate, macro_targets)
        scored.append(annotated)

    scored.sort(key=lambda c: (c["_calorie_distance"], c["_macro_distance"], cost_component(c)))
    return scored


def select_top_candidate(ranked_candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The single top-ranked candidate for a slot, or None if the slot
    has no usable candidates left after the business rules."""
    return ranked_candidates[0] if ranked_candidates else None
  
  
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




