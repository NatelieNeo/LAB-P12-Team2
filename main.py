# Connects the IO layer to the AI layer
from io_manager import collect_user_input
from ai_manager import call_ai
from ai_handler_manager import parse_response
from data_manager import save_user_input

def main():

    # ----- IO LAYER -----
    input_record = collect_user_input() # Collect user information and store it in input_record

    # ----- DATA LAYER (SAVE INPUT) -----
    save_user_input("user_information.json", input_record)

    # ----- AI LAYER -----
    ai_output = call_ai(input_record) # Send input_record to Gemini through ai_manager

    # Stop the program if the AI request failed
    if ai_output is None:
        print("Unable to generate meal recommendations.")
        return
    
    # ----- AI HANDLER LAYER -----
    # Parse and validate the AI response using ai_handler_manager
    raw_ai_output = ai_output
    validated_ai_output = parse_response(raw_ai_output)

    # Stop the program if the AI response is invalid
    if validated_ai_output is None:
        print("AI returned an invalid meal recommendation response.")
        return

    # ----- OUTPUT -----
    # Temporary: display validated AI output
    print("\n===== VALIDATED AI OUTPUT =====")
    print(validated_ai_output)

# Run the program
if __name__ == "__main__":
    main()