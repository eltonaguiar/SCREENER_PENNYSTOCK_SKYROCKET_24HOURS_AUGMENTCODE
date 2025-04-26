import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib

# Path to the cache settings file
CACHE_FILE = os.path.join(
    os.getcwd(), "json", "cache_settings.json"
)

def get_settings_hash(settings: Dict[str, Any]) -> str:
    """
    Generate a hash of the settings dictionary to use as a cache key.
    """
    # Convert settings to a sorted string representation to ensure consistent hashing
    settings_str = json.dumps(settings, sort_keys=True)
    return hashlib.md5(settings_str.encode()).hexdigest()

def save_cache_settings(settings: Dict[str, Any]) -> None:
    """
    Save the current settings and timestamp to the cache file.
    """
    # Create a cache entry with settings and timestamp
    cache_entry = {
        "settings": settings,
        "settings_hash": get_settings_hash(settings),
        "timestamp": datetime.now().strftime("%Y-%m-%d"),
        "iterations_completed": []
    }

    # Create the json directory if it doesn't exist
    json_dir = os.path.dirname(CACHE_FILE)
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    # Check if cache file exists
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)

            # If the settings hash matches and it's the same day, keep the completed iterations
            if (cache_data.get("settings_hash") == cache_entry["settings_hash"] and
                cache_data.get("timestamp") == cache_entry["timestamp"]):
                cache_entry["iterations_completed"] = cache_data.get("iterations_completed", [])
        except (json.JSONDecodeError, FileNotFoundError):
            # If there's an error reading the cache file, start fresh
            pass

    # Write the cache entry to the file
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_entry, f, indent=2)

def mark_iteration_complete(iteration_name: str) -> None:
    """
    Mark an iteration as complete in the cache file.
    """
    # Create the json directory if it doesn't exist
    json_dir = os.path.dirname(CACHE_FILE)
    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    if not os.path.exists(CACHE_FILE):
        print(f"Cache file does not exist when marking {iteration_name} complete. Creating new cache file.")
        # Create a new cache file with this iteration marked as complete
        cache_data = {
            "settings": {},
            "settings_hash": "",
            "timestamp": datetime.now().strftime("%Y-%m-%d"),
            "iterations_completed": [iteration_name]
        }
    else:
        try:
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)

            if iteration_name not in cache_data.get("iterations_completed", []):
                cache_data["iterations_completed"].append(iteration_name)
                print(f"Marked {iteration_name} as complete in cache.")
            else:
                print(f"{iteration_name} was already marked as complete in cache.")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error reading cache file when marking {iteration_name} complete: {e}")
            # Create a new cache file with this iteration marked as complete
            cache_data = {
                "settings": {},
                "settings_hash": "",
                "timestamp": datetime.now().strftime("%Y-%m-%d"),
                "iterations_completed": [iteration_name]
            }

    # Write the updated cache data
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Error writing to cache file: {e}")

def should_skip_iteration(iteration_name: str, current_settings: Dict[str, Any]) -> bool:
    """
    Check if an iteration can be skipped because it was already run with the same settings today.

    Returns:
        bool: True if the iteration can be skipped, False otherwise
    """
    if not os.path.exists(CACHE_FILE):
        print(f"Cache file does not exist: {CACHE_FILE}")
        return False

    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)

        # Check if the settings match and it's the same day
        current_hash = get_settings_hash(current_settings)
        cached_hash = cache_data.get("settings_hash")
        settings_match = cached_hash == current_hash

        today = datetime.now().strftime("%Y-%m-%d")
        cached_date = cache_data.get("timestamp")
        same_day = cached_date == today

        completed_iterations = cache_data.get("iterations_completed", [])
        iteration_completed = iteration_name in completed_iterations

        # Check if the output file exists
        json_path = os.path.join(
            os.getcwd(), "json", f"{iteration_name}.json"
        )
        file_exists = os.path.exists(json_path)

        # Debug output
        print(f"\nCache check for {iteration_name}:")
        print(f"  Settings match: {settings_match} (Current: {current_hash}, Cached: {cached_hash})")
        print(f"  Same day: {same_day} (Current: {today}, Cached: {cached_date})")
        print(f"  Iteration completed: {iteration_completed} (Completed: {completed_iterations})")
        print(f"  File exists: {file_exists} (Path: {json_path})")

        should_skip = settings_match and same_day and iteration_completed and file_exists
        print(f"  Should skip: {should_skip}")

        return should_skip
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading cache file: {e}")
        return False

def get_current_settings() -> Dict[str, Any]:
    """
    Get the current settings from the settings module.
    """
    from ... import settings

    # Extract all non-private variables from the settings module
    settings_dict = {}
    for key, value in vars(settings).items():
        if not key.startswith('_') and not callable(value):
            # Skip module objects
            if not isinstance(value, type(settings)):
                settings_dict[key] = value

    # Handle the trend_settings dictionary specially to ensure it's serializable
    if 'trend_settings' in settings_dict:
        settings_dict['trend_settings'] = dict(settings_dict['trend_settings'])

    return settings_dict
