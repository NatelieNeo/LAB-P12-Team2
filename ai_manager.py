# AI Prompt

def build_prompt(input_record):
    """Build the prompt using validated data from io_manager."""

    prompt = f"""
You are the meal recommendation engine for Calora, a Singapore-based
personalised meal planning application.

Generate exactly 3 meals: one breakfast, one lunch and one dinner.