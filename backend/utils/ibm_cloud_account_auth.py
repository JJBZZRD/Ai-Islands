import os
import requests
import logging
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient, Credentials

# Load environment variables from .env file
load_dotenv()

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
RESOURCE_SERVICE_URL = "https://resource-controller.cloud.ibm.com/v2/resource_instances"

class Authentication:
    def __init__(self):
        self.api_key = os.getenv('IBM_CLOUD_API_KEY')
        if not self.api_key:
            raise ValueError("API key is not set in the environment variables.")

    def _validate_api_key(self, api_key: str) -> bool:
        url = IAM_TOKEN_URL
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        data = {
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key
        }
        response = requests.post(url, headers=headers, data=data)
        return response.status_code == 200

    def get_iam_token(self):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        }
        data = {
            'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
            'apikey': self.api_key,
        }
        response = requests.post(IAM_TOKEN_URL, headers=headers, data=data)
        if response.status_code == 200:
            token = response.json()['access_token']
            logging.info("IAM token retrieved successfully")
            return token
        else:
            error_message = f"Failed to get IAM token: {response.text}"
            raise RuntimeError(error_message)

class ResourceService:
    def get_resource_list(self, iam_token):
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Accept': 'application/json',
        }
        response = requests.get(RESOURCE_SERVICE_URL, headers=headers)
        if response.status_code == 200:
            return response.json()['resources']
        else:
            raise Exception(f"Failed to get resource list: {response.text}")

    def get_service_credentials(self, iam_token, service_name):
        resource_service_url = "https://resource-controller.cloud.ibm.com/v2/resource_instances"
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Accept': 'application/json',
        }
        response = requests.get(resource_service_url, headers=headers)
        if response.status_code == 200:
            resources = response.json()['resources']
            for resource in resources:
                if service_name.lower() in resource['name'].lower():
                    instance_id = resource['guid']
                    resource_key_url = f"https://resource-controller.cloud.ibm.com/v2/resource_instances/{instance_id}/resource_keys"
                    key_response = requests.get(resource_key_url, headers=headers)
                    if key_response.status_code == 200:
                        keys = key_response.json()['resources']
                        if keys:
                            return keys[0]['credentials']
                        else:
                            data = {
                                'name': f'{service_name}-Credentials',
                                'source': instance_id,
                                'role': 'Writer'
                            }
                            create_key_response = requests.post(resource_key_url, headers=headers, json=data)
                            if create_key_response.status_code == 201:
                                return create_key_response.json()['credentials']
                            else:
                                raise Exception(f"Failed to create resource key: {create_key_response.text}")
            raise Exception("No matching instance found for the specified service name.")
        else:
            raise Exception(f"Failed to get service credentials: {response.text}")

class AccountInfo:
    def __init__(self):
        self.api_key = os.getenv('IBM_CLOUD_API_KEY')
        self.projects_url = os.getenv('IBM_CLOUD_PROJECTS_URL')
        self.models_url = os.getenv('IBM_CLOUD_MODELS_URL')
        self.credentials = Credentials(
            url=self.models_url,
            api_key=self.api_key
        )
        self.watsonx = APIClient(self.credentials)
        self.auth = Authentication()
        self.resource_service = ResourceService()

        if not self.api_key or not self.projects_url or not self.models_url:
            raise ValueError("API key or URLs are not set in the environment variables.")

    def get_iam_token(self):
        return self.auth.get_iam_token()

    def get_resource_list(self):
        iam_token = self.get_iam_token()
        return self.resource_service.get_resource_list(iam_token)

    def get_service_credentials(self, iam_token, service_name):
        return self.resource_service.get_service_credentials(iam_token, service_name)

    def list_projects(self, iam_token):
        headers = {
            "Authorization": f"Bearer {iam_token}",
            "Content-Type": "application/json"
        }
        endpoint = f"{self.projects_url}/v2/projects"
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            projects = response.json().get('resources', [])
            return projects
        else:
            error_message = f"Failed to list projects: {response.text}"
            raise RuntimeError(error_message)

# Functions to handle projects
def get_projects():
    auth = Authentication()
    account_info = AccountInfo()
    try:
        iam_token = auth.get_iam_token()
        projects = account_info.list_projects(iam_token)
        return [{"id": project["metadata"]["guid"], "name": project["entity"]["name"]} for project in projects]
    except Exception as e:
        logging.error(f"Error: {e}")
        return []

def select_project(project_id: str):
    try:
        return {"status": "Project selected", "project_id": project_id}
    except Exception as e:
        logging.error(f"Error: {e}")
        return {"status": "Error", "message": str(e)}