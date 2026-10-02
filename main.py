# Connects the IO layer to the AI layer
from io_manager import collect_user_input
from ai_manager import call_ai

def main():

    # ----- IO LAYER -----
    input_record = collect_user_input() # Collect user information and store it in input_record

    # ----- AI LAYER -----
    ai_output = call_ai(input_record) # Send input_record to Gemini through ai_manager

    # Stop the program if the AI request failed
    if ai_output is None:
        print("Unable to generate meal recommendations.")
        return

    # Temporary: display AI output to check that linkage works
    print(ai_output)


# Run the program
if __name__ == "__main__":
    main()