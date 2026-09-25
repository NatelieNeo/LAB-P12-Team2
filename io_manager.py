
#----Functions-----
def get_user_name():  #complete
    name = input("Please enter your name: ") #name of user
    print("Hi! ", name, "it's nice to meet you!")
    return name

def get_user_age():  #complete

    while True:
        try:

            age = int(input("Please enter your age: ")) #age of user

            if age > 0:
                print("Great! Nice to know you're", age, "years old.")
                return age

            else:
                print("Invalid input. Please enter a valid age.")
                return get_user_age()  # Recursively call the function until a valid age is entered
        except ValueError:
            print("Invalid input. Please enter a valid age.") #call the function if age == string



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
                print("Invalid input. Please enter a valid weight.")
                return get_user_weight()  # Recursively call the function until a valid weight is entered

        except ValueError:
            print("Invalid input. Please enter a valid weight.")


def get_user_height(): #complete

    while True:
        try:

            height_cm = float(input("Please enter your height in cm (up to 1 decimal place): ")) #height of user
            if height_cm > 0:
                print("Awesome! Your height is", height_cm, "cm.")
                return height_cm
            else:
                print("Invalid input. Please enter a valid height.")
                return get_user_height()  # Recursively call the function until a valid height is entered
        except ValueError:
            print("Invalid input. Please enter a valid height.")


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

user_profile = [name, age, gender, weight_kg, height_cm, activity_level]  #store user profile in a list
print("Profile setup complete! Here is your profile information: ", user_profile)