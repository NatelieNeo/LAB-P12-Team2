import json
import logging

logger = logging.getLogger(__name__)

def validate_response(data):
    """
    Validate the structure of the AI response.

    Returns:
        True if valid
        False if malformed
    """

    # Response must be a dictionary
    if not isinstance(data, dict):
        return False

    # Check top-level fields
    required_top_fields = {
        "estimated_nutrition_targets",
        "recommendations"
    }

    if set(data.keys()) != required_top_fields:
        return False
    
    # Validate nutrition targets

    targets = data["estimated_nutrition_targets"]

    if not isinstance(targets, dict):
        return False

    required_target_fields = {
        "calorie_target",
        "protein_target_g",
        "carb_target_g",
        "fat_target_g"
    }

    if set(targets.keys()) != required_target_fields:
        return False

    for value in targets.values():
        if not isinstance(value, (int, float)):
            return False

    # Validate recommendations

    recommendations = data["recommendations"]

    if not isinstance(recommendations, list):
        return False

    # Must contain exactly 10 recommendations
    if len(recommendations) != 10:
        return False

    required_recommendation_fields = {
        "meal_type",
        "meal_name",
        "meal_source_type",
        "calories",
        "protein_g",
        "carbs_g",
        "fat_g",
        "estimated_cost",
        "portion_size",
        "pantry_ingredients_used",
        "ingredients",
        "recipe_steps"
    }

    for recommendation in recommendations:

        if not isinstance(recommendation, dict):
            return False

        # Reject missing or extra fields
        if set(recommendation.keys()) != required_recommendation_fields:
            return False

        # Validate string fields
        if not isinstance(recommendation["meal_type"], str):
            return False

        if not isinstance(recommendation["meal_name"], str):
            return False

        if not isinstance(recommendation["portion_size"], str):
            return False

        # Validate meal source
        if recommendation["meal_source_type"] not in [
            "eat_out",
            "home_cooked"
        ]:
            return False

        # Validate numerical fields
        numeric_fields = [
            "calories",
            "protein_g",
            "carbs_g",
            "fat_g",
            "estimated_cost"
        ]

        for field in numeric_fields:
            if not isinstance(recommendation[field], (int, float)):
                return False

        # Validate list fields
        list_fields = [
            "pantry_ingredients_used",
            "ingredients",
            "recipe_steps"
        ]

        for field in list_fields:
            if not isinstance(recommendation[field], list):
                return False

    return True
