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