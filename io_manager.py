
#----Functions-----
def get_user_name():  
    name = input("Please enter your name: ") #name of user
    print("Hi! ", name, "it's nice to meet you!")
    return name

def get_user_age():
    age = int(input("Please enter your age: ")) #age of user
    if str(age).isdigit() and age > 0:
        print("Great! Nice to know you're", age, "years old.")
        return age
    else:
        print("Invalid input. Please enter a valid age.")
        return get_user_age()  # Recursively call the function until a valid age is entered

def get_user_gender():
    gender = input("Please enter your gender (M/F): ")
    if gender == "M":
        print("Great! Hi bro.")
    elif gender == "F":
        print("Great! Hi sis.")
    else:
        print("Invalid input. Please enter M or F for gender.")
        return get_user_gender()  # Recursively call the function until a valid gender is entered            
    

def get_user_weight():
    weight_kg = float(input("Please enter your weight in kg (up to 1 decimal place): ")) #weight of user
    if weight_kg > 0:
        print("Thanks! Your weight is", weight_kg, "kg.")
        return weight_kg
    else:
        print("Invalid input. Please enter a valid weight.")
        return get_user_weight()  # Recursively call the function until a valid weight is entered


def get_user_height():
    height_cm = float(input("Please enter your height in cm (up to 1 decimal place): ")) #height of user
    if height_cm > 0:
        print("Awesome! Your height is", height_cm, "cm.")
        return height_cm
    else:
        print("Invalid input. Please enter a valid height.")
        return get_user_height()  # Recursively call the function until a valid height is entered

print("Hi I am your personal health assistant, Calora!")
print("I can help you track your health and fitness goals.")
print("Let's get started by setting up your profile.")  #intro
#-------Profile Setup-------
name = get_user_name()

age = get_user_age()

gender = get_user_gender()

weight_kg = get_user_weight()

height_cm = get_user_height()

user_profile = [name, age, gender, weight_kg, height_cm]  #store user profile in a list
print("Profile setup complete! Here is your profile information: ", user_profile)