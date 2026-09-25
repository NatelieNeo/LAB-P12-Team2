import json
import logging

logger = logging.getLogger(__name__)

def validate_nutrition_targets(targets):
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

    return True

def validate_recommendation(recommendation):
    if not isinstance(recommendation, dict):
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

    if set(recommendation.keys()) != required_recommendation_fields:
        return False

    if not isinstance(recommendation["meal_type"], str):
        return False

    if not isinstance(recommendation["meal_name"], str):
        return False

    if not isinstance(recommendation["portion_size"], str):
        return False

    if recommendation["meal_source_type"] not in [
        "eat_out",
        "home_cooked"
    ]:
        return False

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

    list_fields = [
        "pantry_ingredients_used",
        "ingredients",
        "recipe_steps"
    ]

    for field in list_fields:
        if not isinstance(recommendation[field], list):
            return False

    return True

def validate_recommendations(recommendations):
    if not isinstance(recommendations, list):
        return False

    if len(recommendations) != 10:
        return False

    for recommendation in recommendations:
        if not validate_recommendation(recommendation):
            return False

    return True

def validate_response(data):
    if not isinstance(data, dict):
        return False

    required_top_fields = {
        "estimated_nutrition_targets",
        "recommendations"
    }

    if set(data.keys()) != required_top_fields:
        return False

    if not validate_nutrition_targets(
        data["estimated_nutrition_targets"]
    ):
        return False

    if not validate_recommendations(
        data["recommendations"]
    ):
        return False

    return True

def parse_response(response_text):
    """
    Convert Gemini's response text into JSON
    and validate its structure.

    Returns:
        dict if valid
        None if invalid
    """

    if not response_text:
        logger.warning("AI returned an empty response.")
        return None

    try:
        data = json.loads(response_text)

    except json.JSONDecodeError as error:
        logger.warning(
            "AI response contains invalid JSON: %s",
            error
        )
        return None

    if not validate_response(data):
        logger.warning(
            "AI response failed schema validation."
        )
        return None

    return data