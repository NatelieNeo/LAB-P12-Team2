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


