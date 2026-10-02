import json
import uuid

#Saving user information into a JSON file
def save_user_input(filepath, user_data):

    try:
        with open(filepath, 'r') as user_information: #open JSON file in read mode
            users = json.load(user_information) 
    except(FileNotFoundError, json.JSONDecodeError): #if file not found create an empty dict
        users = {}

    entry_id = str(uuid.uuid4()) #create a unique uuid for the user
    users[entry_id] = user_data 

    with open(filepath, "w") as user_information: #open JSON file in write mode
        json.dump(users, user_information, indent=1) #writes the new user into the dictionary

    return users

    #print("Successfully added user information to the dictionary")
