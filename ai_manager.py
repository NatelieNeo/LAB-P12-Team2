# Build AI Prompt

def build_prompt(input_record):
    # Build the prompt using validated data from io_manager

    prompt = f"""
You are the meal recommendation engine for Calora, a Singapore-based
personalised meal planning application.

Your task is to analyse the user's profile, fitness goal, dietary
requirements, food preferences and budget, then recommend the food
options that best match their requirements.


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
