
#----Functions-----
def get_user_name():  #complete
    name = input("Please enter your name: ") #name of user
    print("Hi!", name, "it's nice to meet you!")
    return name

def get_user_age():  #complete

    while True:
        try:

            age = int(input("Please enter your age: ")) #age of user

            if age > 0:
                print("Great! Nice to know you're", age, "years old.")
                return age

            else:
                print("You've entered a negative number. Please enter a valid age.") #-ve
                return get_user_age()  # Recursively call the function until a valid age is entered
        except ValueError:
            print("You've entered a string. Please enter a valid age.") #call the function if age == string



def get_user_gender(): #complete
    gender = input("Please enter your gender (M/F): ")
    if gender.upper() == "M":  #allow lowercase inputs too
        print("Great! Hi bro.")
        return gender.upper()
    elif gender.upper() == "F": #allow lowercase inputs too
        print("Great! Hi sis.")
        return gender.upper()
    else:
        print("Invalid input. Please enter M or F for gender.")
        return get_user_gender()  # Recursively call the function until a valid gender is entered            
    

def get_user_weight():  #complete

    while True:
        try:

            weight_kg = float(input("Please enter your weight in kg (up to 1 decimal place): ")) #weight of user

            if weight_kg > 0:
                print("Thanks! Your weight is", weight_kg, "kg.")
                return weight_kg
            else:
                print("You've entered a negative number. Please enter a valid weight.") #-ve
                return get_user_weight()  # Recursively call the function until a valid weight is entered

        except ValueError:
            print("You've entered a string. Please enter a valid weight.") #str


def get_user_height(): #complete

    while True:
        try:

            height_cm = float(input("Please enter your height in cm (up to 1 decimal place): ")) #height of user
            if height_cm > 0:
                print("Awesome! Your height is", height_cm, "cm.")
                return height_cm
            else:
                print("You've entered a negative number. Please enter a valid height.") #-ve
                return get_user_height()  # Recursively call the function until a valid height is entered
        except ValueError:
            print("You've entered a string. Please enter a valid height.") #str


def get_activity_level(): #complete
    activity_level = input("Please enter your activity level (sedentary /workout 1-2 times a week/, moderately active /workout 3-4 times a week/, very active /5-6 times a week/): ")  
    if activity_level == "sedentary":
        print("cool ", name)
        return activity_level
    elif activity_level == "moderately active":
        print("That's great ", name)
        return activity_level  
    elif activity_level == "very active":
        print("Wow, that's impressive ", name) 
        return activity_level 
    else:
        print("Invalid input, please try again") 
        return get_activity_level()


def get_user_goal(): #user's goal
    user_goal = input("Please enter your desired goal (lose/maintain/gain): ")
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

def get_dietry_restrictions(): #user's diet
    dietry_restrictions = input("Please indicate your dietry restrictions (If none please enter 'nil'): ")        
    if dietry_restrictions.isdigit():
        print("You've entered an integer, Please enter a valid string.")
        return get_dietry_restrictions()
    else:
        print("Your dietry restrictions: ", dietry_restrictions)
        return dietry_restrictions

def get_meal_preference(): #dynamic: user's meal preference
    meal_preference = input("What type of food do you want to eat today?: ")
    if meal_preference.isdigit():
        print("You've entered an integer, Please enter a valid string.")
        return meal_preference
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

def get_ingredients_avail(): #dynamic: ingredients avail if eat in
    if meal_source == "in":
        ingredients_avail = input("What ingredients do you have?: ")
        print("Ingredients available: ")    
        return ingredients_avail
    elif meal_source == "both":
        ingredients_avail = input("What ingredients do you have?: ")
        print("Ingredients available: ")

def get_daily_budget(): #dynamic: budget

    while True:
        try:
            daily_budget = int(input("What's your total budget for the day? (enter '0' for none): "))

            if daily_budget > 0:
                print("Your total budget is:$",daily_budget)
                return daily_budget

            elif daily_budget == 0:
                print("No daily budget.")
                return daily_budget

            else:
                print("You've entered a negative integer. Please try again.") #-ve
                return get_daily_budget()

        except ValueError:
            print("You've entered a string. Please try again.") #str
            return get_daily_budget()
    
        
            



    



    

print("Hi I am your personal health assistant, Calora!")
print("I can help you track your health and fitness goals.")
print("Let's get started by setting up your profile.")  #intro
#-------Profile Setup-------
name = get_user_name()

age = get_user_age()

gender = get_user_gender()

weight_kg = get_user_weight()

height_cm = get_user_height()

activity_level = get_activity_level()

user_goal = get_user_goal()

dietry_restrictions = get_dietry_restrictions()

user_profile = [name, age, gender, weight_kg, height_cm, activity_level, user_goal, dietry_restrictions]  #store user profile in a list
print("Profile setup complete! Here is your profile information: ", user_profile)

#------Start of Dynamic Inputs------

print("Okay ", name, " let's start with today's meal plan!") #intro to the daily meals

meal_preference = get_meal_preference()

meal_source = get_meal_source()

ingredients_avail = get_ingredients_avail()

daily_budget = get_daily_budget()

daily_summary = [meal_preference, meal_source, ingredients_avail, daily_budget] #outro of the daily requirements
print("Daily summary completed: ", daily_summary)


#----Notes----

#meal_preference = user input (open format)
#dietary_restrictions = user input (open format)
#dining_type = in / out
#if in then 

#BMR = M: (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
#BMR = F: (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

#Activity_Factor = sedentary(1.2), moderately active(1.5), very active(1.7)

#Maintenance_Calories = BMR * Activity_Factor

#desired_loss & desired_gain = 5% / 10% / 15%  
#need to convert desired_loss_percent into a float
#e.g. desired_loss_percent = input(float("Please enter your desired loss of weight...."))

#Weight_Loss_Calories = Maintenance_Calories * (1 - desired_loss_percent)

#muscle_gain_Calories = Maintenance_Calories * 1.1 #keep it standardised, allow 10% surplus first

#weight_loss_Protein = weight_kg * 2.0
#maintenance_Protein = weight_kg * 1.6
#muscle_gain_Protein = weight_kg * 1.8 

#carbs = (calories * 0.5) / 4

#round up the protein & carbs
#protein = round(protein)      carbs = round(carbs)
