from os import name


def get_username():  
    username = input("Please enter your username: ")
    
    if username is None:
        print("Invalid input. Please enter a valid username.")
        return get_username() # Recursively call the function until a valid username is entered
        
    return username


def get_user_name():
    user_name = input("Please enter your name: ") or None
    if user_name is None:
        print("Invalid input. Please enter a valid name.")
        return get_user_name() # Recursively call the function until a valid name is entered

    print(f"Hi {user_name}, it's nice to meet you!")
    return user_name


def get_user_age(allow_null=False):
    while True:
        try:
            user_input = input("Please enter your age: ") or "0" # Allow empty input to be treated as 0
            age = int(user_input) # Convert the input to an integer

            if allow_null and age == 0:
                return None

            if age > 12 and age < 100:
                print("Great! Nice to know you're", age, "years old.")
                return age
            else:
                print("You've entered an invalid age. Please enter a valid age.") # -ve/too low/too high
                return get_user_age()  # Recursively call the function until a valid age is entered
            
        except ValueError:
            print("You've entered a string. Please enter a valid age.") # Call the function if age == string


def get_user_gender(allow_null=False):
    gender = input("Please enter your gender (M/F): ")
    if gender.upper() == "M":  # Allow lowercase inputs
        print("Great! Hi bro.")
        return gender.upper()
    elif gender.upper() == "F": # Allow lowercase inputs
        print("Great! Hi sis.")
        return gender.upper()
    else:
        if allow_null:
            return None

        print("Invalid input. Please enter M or F for gender.")
        return get_user_gender()  # Recursively call the function until a valid gender is entered            
    

def get_user_weight(allow_null=False):
    while True:
        try:
            user_input = input("Please enter your weight in kg (up to 1 decimal place): ") or "0"
            weight_kg = float(user_input) # Convert the input to float

            if allow_null and weight_kg == 0:
                return None

            if weight_kg > 20 and weight_kg < 300:  # Realistic weight range
                print("Thanks! Your weight is", weight_kg, "kg.")
                return weight_kg
            else:
                print("You've entered a negative number / unrealistic value. Please enter a valid weight.") # -ve
                return get_user_weight()  # Recursively call the function until a valid weight is entered

        except ValueError:
            print("You've entered a string. Please enter a valid weight.") 


def get_user_height(allow_null=False): 
    while True:
        try:
            user_input = input("Please enter your height in cm (up to 1 decimal place): ") or "0"
            height_cm = float(user_input) # Convert input to float

            if allow_null and height_cm == 0:
                return None

            if height_cm > 50 and height_cm < 250:  # Realistic height range
                print("Awesome! Your height is", height_cm, "cm.")
                return height_cm
            else:
                print("You've entered an unrealistic value. Please enter a valid height.") # -ve
                return get_user_height()  # Recursively call the function until a valid height is entered
            
        except ValueError:
            print("You've entered a string. Please enter a valid height.")


def get_activity_level(allow_null=False): #complete
    activity_level = input("Please enter your activity level (sedentary /workout 1-2 times a week/, moderately active /workout 3-4 times a week/, very active /5-6 times a week/): ")  
    
    if allow_null and activity_level == "":
        return None
    
    if activity_level == "sedentary":
        print("Cool!")
        return activity_level
    elif activity_level == "moderately active":
        print("That's great!")
        return activity_level  
    elif activity_level == "very active":
        print("Wow, that's impressive!") 
        return activity_level 
    else:
        print("Invalid input, please try again") 
        return get_activity_level()

def get_user_goal(allow_null=False): #user's goal
    user_goal = input("Please enter your desired goal (lose/maintain/gain): ")
    if allow_null and user_goal == "":
        return None

    if user_goal == "lose":
        print("Your desire is to lose weight")
        return user_goal
    elif user_goal == "maintain":
        print("Your desire is to maintain weight")
        return user_goal
    elif user_goal == "gain":
        print("Your desire is to gain muscle")
        return user_goal
    else:
        print("Invalid input, please try again")
        return get_user_goal()


def get_dietary_restrictions(allow_null=False): #user's diet
    dietary_restrictions = input("Please indicate your dietary restrictions (If none please enter 'nil'): ")        
    if allow_null and dietary_restrictions == "":
        return None
    
    if dietary_restrictions.isdigit():
        print("You've entered an integer, Please enter a valid string.")
        return get_dietary_restrictions()
    else:
        print("Your dietary restrictions: ", dietary_restrictions)
        return dietary_restrictions


def get_meal_preference(): #dynamic: user's meal preference
    while True:
        meal_preference = input("What type of food do you want to eat today?: ")
        if meal_preference.isdigit():
            print("You've entered an integer, Please enter a valid string.")
        else:
            print("Yum! ", meal_preference, " sounds good.")
            return meal_preference        


def get_meal_source(): #dynamic: user's meal source (eat in or out)
    meal_source = input("Are you planning to eat out or in today? enter in/out/both: ")
    if meal_source == "in":
        print("Nice! Eating in today.")
        return meal_source
    elif meal_source == "out":
        print("Nice! Eating out today.")
        return meal_source
    elif meal_source == "both":
        print("Nice! Eating in & out today.")
        return meal_source
    else:
        print("Invalid entry, please try again.")
        return get_meal_source()


def get_ingredients_avail(meal_source): #dynamic: ingredients avail if eat in
    if meal_source == "in":
        ingredients_avail = input("What ingredients do you have?: ")
        print("Ingredients available: ")    
        return ingredients_avail
    elif meal_source == "both":
        ingredients_avail = input("What ingredients do you have?: ")
        print("Ingredients available: ")
        return ingredients_avail
    elif meal_source == "out": # No pantry ingredients needed if only eating out
        return ""


def get_daily_budget(): #dynamic: budget
    while True:
        try:
            daily_budget = int(input("What's your total budget for the day? (minimum $6) (enter '0' for none): "))

            if daily_budget > 6:
                print("Your total budget is:$",daily_budget)
                return daily_budget

            elif daily_budget == 0:
                print("No daily budget.")
                return daily_budget

            else:
                print("You've entered an invalid amount. Please try again.") #-ve/too low
                return get_daily_budget()

        except ValueError:
            print("You've entered a string. Please try again.") #str
            return get_daily_budget()


def create_meal_plan(input_record, name): #dynamic: create meal plan
    #------Start of Dynamic Inputs------
    print(f"\nOkay {name}, let's get started with today's meal plan!")

    meal_preference = get_meal_preference()

    meal_source = get_meal_source()

    pantry_ingredients = get_ingredients_avail(meal_source) # Pass meal_source into the ingredients function

    daily_budget = get_daily_budget()

    daily_summary = [meal_preference, meal_source, pantry_ingredients, daily_budget] #outro of the daily requirements
    print("Daily summary completed: ", daily_summary)

    # ----- Combine everything into one dictionary -----
    input_record.update({
        "meal_preference": meal_preference,
        "meal_source": meal_source,
        "pantry_ingredients": pantry_ingredients,
        "daily_budget": daily_budget
    })

    return input_record

    
def option_list():
    print("1. Create a meal plan")
    print("2. View previous meal plans")
    print("3. View your profile")
    print("4. Update your profile")
    print("5. Exit the program")
    x = input("\nPlease select an option from the list below (1-5): ")

    return x    


# ----- Collect all user inputs -----
def welcome():
    print("Hi I am your personal health assistant, Calora!")
    print("I can help you track your health and fitness goals.\n")


def format_user_data(user_data):
    formatted_data = ""
    for entry_id, user_info in user_data.items():
        for key, value in user_info.items():
            filtered_key = key.replace("_", " ").capitalize()  # Format the key for better readability
            formatted_data += f"{filtered_key}: {value}\n"
        formatted_data += "\n"
    return formatted_data