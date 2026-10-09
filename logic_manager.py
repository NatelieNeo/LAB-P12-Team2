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