import json
import logging

from config import RECOMMENDATION_COUNT

logger = logging.getLogger(__name__)


# Required schema, defined once and reused by the validators below
TARGET_FIELDS = {
    "calorie_target",
    "protein_target_g",
    "carb_target_g",
    "fat_target_g",
}

STRING_FIELDS = ["meal_type", "meal_name", "portion_size"]
NUMERIC_FIELDS = ["calories", "protein_g", "carbs_g", "fat_g", "estimated_cost"]
LIST_FIELDS = ["pantry_ingredients_used", "ingredients", "recipe_steps"]
RECOMMENDATION_FIELDS = set(
    STRING_FIELDS + NUMERIC_FIELDS + LIST_FIELDS + ["meal_source_type"]
)
MEAL_SOURCE_TYPES = ("eat_out", "home_cooked")
TOP_LEVEL_FIELDS = {"estimated_nutrition_targets", "recommendations"}


def _is_number(value):
    return isinstance(value, (int, float))


def validate_nutrition_targets(targets):
    if not isinstance(targets, dict) or set(targets.keys()) != TARGET_FIELDS:
        return False

    return all(_is_number(value) for value in targets.values())


def validate_recommendation(recommendation):
    if not isinstance(recommendation, dict):
        return False

    if set(recommendation.keys()) != RECOMMENDATION_FIELDS:
        return False

    if recommendation["meal_source_type"] not in MEAL_SOURCE_TYPES:
        return False

    return (
        all(isinstance(recommendation[f], str) for f in STRING_FIELDS)
        and all(_is_number(recommendation[f]) for f in NUMERIC_FIELDS)
        and all(isinstance(recommendation[f], list) for f in LIST_FIELDS)
    )


def validate_recommendations(recommendations):
    if not isinstance(recommendations, list):
        return False

    if len(recommendations) != RECOMMENDATION_COUNT:
        return False

    return all(validate_recommendation(r) for r in recommendations)


def validate_response(data):
    if not isinstance(data, dict) or set(data.keys()) != TOP_LEVEL_FIELDS:
        return False

    return (
        validate_nutrition_targets(data["estimated_nutrition_targets"])
        and validate_recommendations(data["recommendations"])
    )


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

