import os
from dotenv import load_dotenv, find_dotenv

def get_env_source(key):
    dotenv_path = find_dotenv()
    with open(dotenv_path, 'r') as file:
        for line in file:
            if line.startswith(f"{key}="):
                return f"From .env file: {line.strip()}"
    return f"From system environment"

# Find and load the .env file
dotenv_path = find_dotenv(raise_error_if_not_found=True)
print(f"Found .env file at: {dotenv_path}")

# Print values before loading .env
print("\nBefore loading .env:")
print(f"IBM_CLOUD_API_KEY: {os.getenv('IBM_CLOUD_API_KEY')} ({get_env_source('IBM_CLOUD_API_KEY')})")
print(f"USER_PROJECT_ID: {os.getenv('USER_PROJECT_ID')} ({get_env_source('USER_PROJECT_ID')})")

# Load the .env file
load_dotenv(dotenv_path, override=True)

# Print values after loading .env
print("\nAfter loading .env:")
print(f"IBM_CLOUD_API_KEY: {os.getenv('IBM_CLOUD_API_KEY')} ({get_env_source('IBM_CLOUD_API_KEY')})")
print(f"USER_PROJECT_ID: {os.getenv('USER_PROJECT_ID')} ({get_env_source('USER_PROJECT_ID')})")