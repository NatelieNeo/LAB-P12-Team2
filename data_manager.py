import json
import uuid
import os

#Saving user information into a JSON file
def save_user_input(filepath, user_data):

    try:
        with open(filepath, 'r') as user_information: #open JSON file in read mode
            users = json.load(user_information) 
    except(FileNotFoundError, json.JSONDecodeError): #if file not found create an empty dict
        print("Unable to open user information file, inputs not saved.")
        users = {}

    entry_id = str(uuid.uuid4()) #create a unique uuid for the user
    users[entry_id] = user_data 

    with open(filepath, "w") as user_information: #open JSON file in write mode
        json.dump(users, user_information, indent=1) #writes the new user into the dictionary
        print("User information successfully added to the file.")
    return entry_id


def load_user_information(filepath):

    if not os.path.exists(filepath): #checking if file exists
        print("User information file not found")
        return {}

    try: 
        with open(filepath, 'r') as user_information: #opens user_information.json in read mode
            user_profile = json.load(user_information)
            print(user_profile)
            return user_profile

    except(FileNotFoundError, json.JSONDecodeError): 
        print("File could not be read")
        return {}

#def update_user_information():

#def remove_user_information():

load_user_information("user_information.json")

    #print("Successfully added user information to the dictionary")


