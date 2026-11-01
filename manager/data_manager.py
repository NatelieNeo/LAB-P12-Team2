import json
import uuid
from config import USER_FILE, MEAL_PLAN_FILE


def _read_json(path):
    """Return the JSON contents of a file, or {} if missing/invalid."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_json(path, data):
    """Write data to a JSON file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


# Saving user information into a JSON file
def save_user_profile(user_data):
    users = _read_json(USER_FILE)

    entry_id = str(uuid.uuid4())  # unique id for the user
    users[entry_id] = user_data

    _write_json(USER_FILE, users)

    print("Successfully added user information to the dictionary")
    return users


def search_user_profile(search_key, search_value):
    users = _read_json(USER_FILE)

    results = {}
    for entry_id, user_data in users.items():
        if user_data.get(search_key) == search_value:
            results[entry_id] = user_data

    return results


def load_user_profiles(search_key=None, search_value=None):
    if search_key and search_value:
        return search_user_profile(search_key, search_value)

    return _read_json(USER_FILE)


def update_user_profile(username, updated_data):
    users = _read_json(USER_FILE)

    for entry_id, user_data in users.items():
        if user_data.get("username") == username:
            users[entry_id].update(updated_data)
            _write_json(USER_FILE, users)
            print("Successfully updated user information.")
            return

    print("User not found. No updates made.")


def verify_user_profile(search_key, search_value):
    return bool(search_user_profile(search_key, search_value))


def save_meal_plan(meal_plan_data, user_id):
    meal_plans = _read_json(MEAL_PLAN_FILE)

    entry_id = str(uuid.uuid4())  # unique id for the meal plan
    meal_plans[entry_id] = meal_plan_data
    meal_plans[entry_id]["user_id"] = user_id

    _write_json(MEAL_PLAN_FILE, meal_plans)

    print("Successfully added meal plan information to the dictionary")
    return meal_plans


def get_meal_plans_by_user(user_id):
    meal_plans = _read_json(MEAL_PLAN_FILE)

    user_meal_plans = {}
    for entry_id, meal_plan_data in meal_plans.items():
        if meal_plan_data.get("user_id") == user_id:
            user_meal_plans[entry_id] = meal_plan_data

    return user_meal_plans