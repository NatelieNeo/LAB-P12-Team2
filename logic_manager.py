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


