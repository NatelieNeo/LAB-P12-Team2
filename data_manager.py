import json
import uuid
import dotenv
from config import DATA_FILE_ROOT

user_file_path = DATA_FILE_ROOT + "user_profiles.json"
meal_plan_file_path = DATA_FILE_ROOT + "meal_plans.json"

#Saving user information into a JSON file
def save_user_profile(user_data):

    try:
        with open(user_file_path, 'r') as user_information: #open JSON file in read mode
            users = json.load(user_information) 
    except(FileNotFoundError, json.JSONDecodeError): #if file not found create an empty dict
        users = {}

    entry_id = str(uuid.uuid4()) #create a unique uuid for the user
    users[entry_id] = user_data 

    with open(user_file_path, "w") as user_information: #open JSON file in write mode
        json.dump(users, user_information, indent=1) #writes the new user into the dictionary

    print("Successfully added user information to the dictionary")
    return users

def load_user_profiles(search_key=None, search_value=None):
    try:
        with open(user_file_path, 'r') as user_information: #open JSON file in read mode
            users = json.load(user_information) 
    except(FileNotFoundError, json.JSONDecodeError): #if file not found create an empty dict
        users = {}

    if search_key and search_value:
        results = {}
        for entry_id, user_data in users.items():
            if user_data.get(search_key) == search_value:
                results[entry_id] = user_data
        return results

    return users

def search_user_profile(search_key, search_value):
    try:
        with open(user_file_path, 'r') as user_information: #open JSON file in read mode
            users = json.load(user_information) 
    except(FileNotFoundError, json.JSONDecodeError): #if file not found create an empty dict
        users = {}

    results = {}
    for entry_id, user_data in users.items():
        if user_data.get(search_key) == search_value:
            results[entry_id] = user_data

    return results

def update_user_profile(username, updated_data):
    try:
        with open(user_file_path, 'r') as user_information: #open JSON file in read mode
            users = json.load(user_information) 
    except(FileNotFoundError, json.JSONDecodeError): #if file not found create an empty dict
        users = {}

    for entry_id, user_data in users.items():
        if user_data.get("username") == username:
            users[entry_id].update(updated_data)
            with open(user_file_path, "w") as user_information: #open JSON file in write mode
                json.dump(users, user_information, indent=1) #writes the updated user into the dictionary
            print("Successfully updated user information.")
            return
    else:
        print("User not found. No updates made.")

def verify_user_profile(search_key, search_value):
    results = search_user_profile(search_key, search_value)
    if results:
        return True
    else:
        return False
    
def save_meal_plan(meal_plan_data, user_id):
    try:
        with open(meal_plan_file_path, 'r') as meal_plan_information: #open JSON file in read mode
            meal_plans = json.load(meal_plan_information) 
    except(FileNotFoundError, json.JSONDecodeError): #if file not found create an empty dict
        meal_plans = {}

    entry_id = str(uuid.uuid4()) #create a unique uuid for the meal plan
    meal_plans[entry_id] = meal_plan_data 
    meal_plans[entry_id]["user_id"] = user_id

    with open(meal_plan_file_path, "w") as meal_plan_information: #open JSON file in write mode
        json.dump(meal_plans, meal_plan_information, indent=1) #writes the new meal plan into the dictionary

    print("Successfully added meal plan information to the dictionary")
    return meal_plans

def get_meal_plans_by_user(user_id):
    try:
        with open(meal_plan_file_path, 'r') as meal_plan_information: #open JSON file in read mode
            meal_plans = json.load(meal_plan_information) 
    except(FileNotFoundError, json.JSONDecodeError): #if file not found create an empty dict
        meal_plans = {}

    user_meal_plans = {}
    for entry_id, meal_plan_data in meal_plans.items():
        if meal_plan_data.get("user_id") == user_id:
            user_meal_plans[entry_id] = meal_plan_data

    return user_meal_plans