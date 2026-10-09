import json
import uuid
import dotenv
from config import DATA_FILE_ROOT

user_file_path = DATA_FILE_ROOT + "user_profiles.json"

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