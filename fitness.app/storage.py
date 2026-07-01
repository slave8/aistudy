import json
from json import JSONDecodeError
from pathlib import Path

PROFILES_FILE = Path("user_profiles.json")
ACTIVE_PROFILE_FILE = Path("active_profile.json")
WORKOUT_LIST_FILE = Path("saved_workout_list.json")
RECORD_FILE = Path("workout_records.json")


def load_json(path, default_value):
    if not path.exists():
        return default_value

    try:
        content = path.read_text(encoding="utf-8").strip()

        if not content:
            return default_value

        return json.loads(content)

    except JSONDecodeError:
        return default_value


def save_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_profiles():
    profiles = load_json(PROFILES_FILE, {})

    if not isinstance(profiles, dict):
        return {}

    return profiles


def save_profile(profile):
    profiles = load_profiles()

    username = profile["username"]
    profiles[username] = profile

    save_json(PROFILES_FILE, profiles)
    save_json(ACTIVE_PROFILE_FILE, {"username": username})


def load_profile(username=None):
    profiles = load_profiles()

    if username:
        return profiles.get(username)

    active = load_json(ACTIVE_PROFILE_FILE, {})

    if isinstance(active, dict):
        active_username = active.get("username")

        if active_username in profiles:
            return profiles[active_username]

    if profiles:
        first_username = next(iter(profiles))
        return profiles[first_username]

    return None


def delete_profile(username):
    profiles = load_profiles()

    if username in profiles:
        del profiles[username]
        save_json(PROFILES_FILE, profiles)

    active = load_json(ACTIVE_PROFILE_FILE, {})

    if isinstance(active, dict) and active.get("username") == username:
        save_json(ACTIVE_PROFILE_FILE, {})


def load_all_workout_lists():
    all_lists = load_json(WORKOUT_LIST_FILE, {})

    if not isinstance(all_lists, dict):
        return {}

    return all_lists


def save_workout_list(username, weekday, workout_list):
    all_lists = load_all_workout_lists()

    if username not in all_lists:
        all_lists[username] = {}

    if not isinstance(all_lists[username], dict):
        all_lists[username] = {}

    all_lists[username][weekday] = workout_list

    save_json(WORKOUT_LIST_FILE, all_lists)


def load_workout_list(username, weekday):
    all_lists = load_all_workout_lists()
    user_lists = all_lists.get(username, {})

    if isinstance(user_lists, list):
        return user_lists

    if not isinstance(user_lists, dict):
        return []

    return user_lists.get(weekday, [])


def load_user_workout_lists(username):
    all_lists = load_all_workout_lists()
    user_lists = all_lists.get(username, {})

    if isinstance(user_lists, list):
        return {"기본": user_lists}

    if not isinstance(user_lists, dict):
        return {}

    return user_lists


def load_records():
    records = load_json(RECORD_FILE, [])

    if not isinstance(records, list):
        return []

    return records


def save_records(records):
    save_json(RECORD_FILE, records)


def save_record(record):
    records = load_records()
    records.append(record)
    save_records(records)