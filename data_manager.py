import json
import uuid

#Saving user information into a JSON file
def save_user_input(filepath, user_data):

    try:
        with open(filepath, 'r') as user_information:
            users = json.load(user_information)
    except(FileNotFoundError, json.JSONDecodeError):
        users = {}

    entry_id = str(uuid.uuid4())   # unique every time
    users[entry_id] = user_data

    with open(filepath, "w") as user_information:
        json.dump(users, user_information, indent=1)

    return users

    #print("Successfully added user information to the dictionary")
