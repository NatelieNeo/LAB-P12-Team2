import logging
from google import genai

from config import GEMINI_MODEL, MAX_RETRIES
from ai_handler_manager import parse_response

logging.basicConfig(
level=logging.INFO,
format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(name)
# Build AI Prompt

def build_prompt(input_record):
    # Build the prompt using validated data from io_manager

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
Available pantry ingredients: {input_record['pantry_ingredients']}
Daily budget: SGD {input_record['daily_budget']}


NUTRITION ESTIMATION
Based on the user's age, gender, weight, height, activity level and fitness goal, estimate suitable daily nutritional targets.

Estimate:
- daily calorie target in kcal
- daily protein target in grams
- daily carbohydrate target in grams
- daily fat target in grams

The estimates should reasonably support the user's stated fitness goal.

For example:
- Weight-loss goals should generally prioritise sufficient protein while maintaining an appropriate calorie deficit.
- Muscle-gain goals should generally prioritise sufficient protein and energy intake to support muscle growth.
- Maintenance goals should aim to support the user's estimated daily energy requirements.

Return the estimated targets as numerical values.


FOOD RECOMMENDATIONS
Generate exactly 10 food recommendations that best match the user's requirements.

Consider all of the following when generating meals:

- estimated nutritional requirements
- fitness goal
- dietary restrictions and allergies
- meal preference
- available pantry ingredients
- budget
- practicality and availability

Never recommend food containing anything listed under the user's dietary restrictions or allergies.


MEAL SOURCE
# Every recommendation must have a meal_source_type.

meal_source_type must be exactly one of:

- eat_out
- home_cooked

Follow the user's meal preference.

If meal preference is "eat_out":
Only recommend eat_out meals.

If meal preference is "home_cooked":
Only recommend home_cooked meals.

If meal preference is "both":
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
- ingredients must be an empty list.
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

For eat-out recommendations, return an empty list.

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
"response_mime_type": "application/json"
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