import os

GEMINI_MODEL = "gemini-3.1-flash-lite"
DATA_FILE_ROOT = "data/"
USER_FILE = os.path.join(DATA_FILE_ROOT, "user_profiles.json")
MEAL_PLAN_FILE = os.path.join(DATA_FILE_ROOT, "meal_plans.json")
MAX_RETRIES = 3
MEALS_PER_RECOMMENDATION_SET = 10