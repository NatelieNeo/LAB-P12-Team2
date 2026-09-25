# Build AI Prompt

def build_prompt(input_record):
    # Build the prompt using validated data from io_manager

    prompt = f"""
You are the meal recommendation engine for Calora, a Singapore-based
personalised meal planning application.

Your task is to generate a personalised full-day meal plan using
the information supplied by Calora.

Do not calculate or change the user's calorie or macronutrient
targets. These targets have already been calculated by Calora.


USER PROFILE

Name: {input_record['name']}
Age: {input_record['age']}
Gender: {input_record['gender']}
Weight: {input_record['weight_kg']} kg
Height: {input_record['height_cm']} cm
Activity level: {input_record['activity_level']}
Goal: {input_record['goal']}

