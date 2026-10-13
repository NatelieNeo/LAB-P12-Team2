import os
import logging

from dotenv import load_dotenv
from google import genai

from config import GEMINI_MODEL, MAX_RETRIES
from manager.ai_handler_manager import parse_response
from manager.logic_manager import calculate_macro_targets, calculate_targets

load_dotenv()  # Load environment variables from .env file

logging.basicConfig(
level=logging.INFO,
format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# Build AI Prompt
def build_prompt(input_record):
    # Build the prompt using validated data from io_manager
    targets = calculate_targets(input_record)
    daily_macro_targets = calculate_macro_targets(
        targets["daily_calorie_target"], input_record["goal"]
    )
    prompt = f"""
You are the meal recommendation engine for Calora, a Singapore-based personalised meal planning application.

Your task is to analyse the user's profile, fitness goal, dietary requirements, food preferences and budget, then recommend the food options that best match their requirements.


USER PROFILE
# Basic information collected from io_manager.py

Name: {input_record['name']}
Age: {input_record['age']}
Gender: {input_record['gender']}
Weight: {input_record['weight_kg']} kg
Height: {input_record['height_cm']} cm
Activity level: {input_record['activity_level']}
Goal: {input_record['goal']}


USER MEAL PREFERENCES
# Preferences and restrictions collected from io_manager.py

Dietary restrictions/allergies: {input_record['dietary_restrictions']}
Meal preference: {input_record['meal_preference']}
Meal source: {input_record['meal_source']}
Available pantry ingredients: {input_record['pantry_ingredients']}
Daily budget: SGD {input_record['daily_budget']}


NUTRITION ESTIMATION
Use the application-calculated values below as the authoritative nutrition targets; do not calculate a different target.

Daily targets:
- calories: {targets['daily_calorie_target']:.0f} kcal
- protein: {daily_macro_targets['protein_g']:.1f} g
- carbohydrates: {daily_macro_targets['carbs_g']:.1f} g
- fat: {daily_macro_targets['fat_g']:.1f} g

For planning, use three meals per day. Each meal's calorie target is approximately {targets['per_meal_calorie_target']:.0f} kcal, with per-meal macro targets of {targets['per_meal_macro_targets']['protein_g']:.1f} g protein, {targets['per_meal_macro_targets']['carbs_g']:.1f} g carbohydrates, and {targets['per_meal_macro_targets']['fat_g']:.1f} g fat.

The estimated_nutrition_targets object in your JSON must repeat the daily targets above.


FOOD RECOMMENDATIONS
Generate exactly 10 food recommendations that best match the user's requirements.
Use only breakfast, lunch, or dinner as meal_type. Include at least 3 recommendations for each of these three meal types.
Aim for realistic serving sizes whose calories are within approximately 80%-120% of the per-meal calorie target above. Prefer options within that range rather than consistently undersized meals; do not inflate portions or nutrition estimates to hit a number.
The user's meal preference/craving is "{input_record['meal_preference']}". Treat this as an important preference: include at least 2 recommendations matching it for each meal type whenever safe, practical options exist. Keep recommendations within the user's calorie and macro targets; do not ignore the craving just because another cuisine is marginally closer nutritionally. If a matching option would conflict with an allergy, dietary restriction, or realistic budget, exclude it and explain nothing outside the JSON.

Consider all of the following when generating meals:

- estimated nutritional requirements
- fitness goal
- dietary restrictions and allergies
- meal preference
- available pantry ingredients
- budget
- practicality and availability

Never recommend food containing anything listed under the user's dietary restrictions or allergies.


GENERAL RECOMMENDATION RULES
- AI handler validates format
- AI checks recommendations against restrictions
- Code removes incompatible or uncertain meals
- Display remaining meals


MEAL SOURCE
# Every recommendation must have a meal_source_type.

meal_source_type must be exactly one of:

- eat_out
- home_cooked

Follow the user's meal_source.

If meal_source is "in":
Only recommend home_cooked meals.

If meal_source is "out":
Only recommend eat_out meals.

If meal_source is "both":
Recommendations may contain both eat_out and home_cooked options.

# eat_out OPTIONS
Recommend realistic and affordable local food

For meals where meal_source_type is "eat_out":

- Prioritise food that is affordable and commonly available in Singapore.
- Prefer realistic hawker centre, coffee shop and food court options.
- Local dishes may include chicken rice, economical rice, yong tau foo, fishball noodles and other suitable Singapore dishes.
- Consider the user's fitness and nutritional goals.
- Give a realistic portion size.
- Estimate the calories for the portion.
- Estimate protein, carbohydrates and fat for the portion.
- Estimate the price in Singapore Dollars.
- Do not invent a specific restaurant, stall or business.
- In ingredients, list the known main ingredients in the dish, including sauces, stock, and common condiments when known. Ingredient names are enough; quantities are not needed.
- Never leave ingredients empty for an eat-out dish. If you cannot identify its ingredients reliably, do not recommend that dish.
- Do not claim a dish is safe for an allergy unless its ingredients are known.
- recipe_steps must be an empty list.

# home_cooked OPTIONS
# Include measurements and cooking instructions for recipes

For meals where meal_source_type is "home_cooked":

- Prioritise ingredients already available in the user's pantry.
- Additional ingredients may be included when necessary.
- Provide every ingredient required to make one serving.
- Give the exact quantity and unit for each ingredient.
- Provide simple cooking instructions in the correct order.
- Estimate calories, protein, carbohydrates and fat for one serving.
- Estimate the cost of one serving in SGD.
- Keep recipes realistic and reasonably easy to prepare.

PANTRY INGREDIENTS
# Shows which ingredients the user already owns

For each home-cooked recommendation, return pantry_ingredients_used.

pantry_ingredients_used must contain only ingredients that:
1. Appear in the user's available pantry ingredients.
2. Are actually used in the recommended recipe.

If no pantry ingredients are used, return an empty list.

For eat-out recommendations, return an empty list. The ingredients field still lists the dish's known ingredients for dietary-restriction filtering.

NUTRITION INFORMATION
# Raw nutrition estimates for each recommendation
For EVERY food recommendation provide:

- calories
- protein_g
- carbs_g
- fat_g

These must be numerical estimates.

Do not use descriptions such as "high protein" instead of numerical values.


COST INFORMATION
# Estimated cost of buying or preparing one serving

For EVERY food recommendation provide:
- estimated_cost

estimated_cost must be a numerical value in Singapore Dollars.

Consider the user's supplied budget when ranking recommendations.


OUTPUT FORMAT

-Return ONLY valid JSON.
-Do not include Markdown.
-Do not include explanations before or after the JSON.
-Do not add additional fields.
-The "recommendations" list must contain exactly 10 recommendation objects using the structure shown below.

Use exactly the following structure:
{{
    "estimated_nutrition_targets": {{
        "calorie_target": 0,
        "protein_target_g": 0,
        "carb_target_g": 0,
        "fat_target_g": 0
    }},

    "recommendations": [
        {{
            "meal_type": "",
            "meal_name": "",
            "meal_source_type": "",
            "calories": 0,
            "protein_g": 0,
            "carbs_g": 0,
            "fat_g": 0,
            "estimated_cost": 0.00,
            "portion_size": "",
            "pantry_ingredients_used": [],
            "ingredients": [],
            "recipe_steps": []
        }}
    ]
}}
"""
# Returns the completed prompt so it can be sent to the AI API
    return prompt


def call_ai(input_record):
    """
    Handles communication with Gemini.

    Returns:
        dict if successful
        None if all attempts fail
    """

    prompt = build_prompt(input_record)
    
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logger.error("GEMINI_API_KEY was not found in the .env file.")
        return None

    try:
        # Initialise Gemini client using API key
        client = genai.Client(
            api_key=api_key
        )

    except Exception as error:
        logger.error(
            "Failed to initialise Gemini client: %s",
            error
        )
        return None

    try:
        client = genai.Client()

    except Exception as error:
        logger.error(
            "Failed to initialise Gemini client: %s",
            error
        )
        return None

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            logger.info(
                "Calling Gemini API - attempt %s/%s",
                attempt,
                MAX_RETRIES
            )

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 1,
                    "seed": 42
                }
            )

            # Send the AI response to ai_handler_manager.py
            result = parse_response(response.text)

            # Valid response
            if result is not None:
                logger.info(
                    "AI response successfully validated."
                )

                return result

            # Invalid response
            logger.warning(
                "Invalid AI response on attempt %s.",
                attempt
            )

        except Exception as error:
            logger.error(
                "Gemini API error on attempt %s: %s",
                attempt,
                error
            )

    logger.error(
        "AI request failed after %s attempts.",
        MAX_RETRIES
    )

    return None