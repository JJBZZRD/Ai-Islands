import os
import requests
import logging
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient, Credentials
from backend.utils.watson_settings_manager import watson_settings

from backend.core.exceptions import ModelError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
RESOURCE_SERVICE_URL = "https://resource-controller.cloud.ibm.com/v2/resource_instances"

class Authentication:
    def __init__(self):
        self.api_key = watson_settings.get('IBM_CLOUD_API_KEY')
        if not self.api_key:
            logger.error("API key is not set in the settings.")
            raise ValueError("API key is not set in the settings.")

    # def _validate_api_key(self, api_key: str) -> bool:
    #     try:
    #         url = IAM_TOKEN_URL
    #         headers = {
    #             "Content-Type": "application/x-www-form-urlencoded",
    #             "Accept": "application/json"
    #         }
    #         data = {
    #             "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
    #             "apikey": api_key
    #         }
    #         response = requests.post(url, headers=headers, data=data)
    #         return response.status_code == 200
    #     except requests.RequestException as e:
    #         logger.error(f"Error validating API key: {str(e)}")
    #         return False

    def validate_api_key(self):
        try:
            self.get_iam_token()
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False

    # def get_iam_token(self):
    #     headers = {
    #         'Content-Type': 'application/x-www-form-urlencoded',
    #         'Accept': 'application/json',
    #     }
    #     data = {
    #         'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
    #         'apikey': self.api_key,
    #     }
    #     response = requests.post(IAM_TOKEN_URL, headers=headers, data=data)
    #     if response.status_code == 200:
    #         token = response.json()['access_token']
    #         logging.info("IAM token retrieved successfully")
    #         return token
    #     else:
    #         error_message = f"Failed to get IAM token: {response.text}"
    #         raise RuntimeError(error_message)

    def get_iam_token(self):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        }
        data = {
            'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
            'apikey': self.api_key,
        }
        try:
            response = requests.post(IAM_TOKEN_URL, headers=headers, data=data)
            response.raise_for_status()
            token = response.json().get('access_token')
            if not token:
                raise ValueError("No access token in response")
            logger.info("IAM token retrieved successfully")
            return token
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise ModelError(f"Failed to get IAM token: HTTP {e.response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error occurred: {str(e)}")
            raise ModelError(f"Failed to get IAM token: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            raise ModelError(f"Failed to get IAM token: {str(e)}")

    def validate_project(self, project_id: str) -> bool:
        try:
            projects = get_projects()
            if not projects:
                logging.warning("No projects found in the IBM Cloud account.")
                return False
            
            valid_project = any(project['id'] == project_id for project in projects)
            if not valid_project:
                logging.error(f"Project ID {project_id} not found in available projects.")
                logging.info(f"Available project IDs: {[project['id'] for project in projects]}")
            return valid_project
        except Exception as e:
            logging.error(f"Error validating project ID: {str(e)}")
            return False

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
            raise ModelError(f"Failed to get resource list: {response.text}")

    def get_service_credentials(self, iam_token, service_name):
        headers = {
            'Authorization': f'Bearer {iam_token}',
            'Accept': 'application/json',
        }
        response = requests.get(RESOURCE_SERVICE_URL, headers=headers)
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
                                raise ModelError(f"Failed to create resource key: {create_key_response.text}")
            raise ModelError("No matching instance found for the specified service name.")
        else:
            raise ModelError(f"Failed to get service credentials: {response.text}")

class AccountInfo:
    def __init__(self):
        self.api_key = watson_settings.get('IBM_CLOUD_API_KEY')
        self.projects_url = watson_settings.get('IBM_CLOUD_PROJECTS_URL')
        self.models_url = watson_settings.get('IBM_CLOUD_MODELS_URL')

        if not self.api_key or not self.projects_url or not self.models_url:
            logger.error("API key or URLs are not set in the settings.")
            raise ValueError("API key or URLs are not set in the settings.")

        # The following is the old way of doing things, before lazy evaluation.
        # Replace this section with lazy evaluation below! -------------------------
        # self.credentials = Credentials(
        #     url=self.models_url,
        #     api_key=self.api_key
        # )
        # self.watsonx = APIClient(self.credentials)
        # self.auth = Authentication()
        # self.resource_service = ResourceService()
        # ------------------------------------------------------------------------

        # Lazy evaluation:
        # START
        self._credentials = None
        self._watsonx = None
        self._auth = None
        self._resource_service = None

    @property
    def credentials(self):
        if self._credentials is None:
            self._credentials = Credentials(
                url=self.models_url,
                api_key=self.api_key
            )
        return self._credentials

    @property
    def watsonx(self):
        if self._watsonx is None:
            self._watsonx = APIClient(self.credentials)
        return self._watsonx

    @property
    def auth(self):
        if self._auth is None:
            self._auth = Authentication()
        return self._auth

    @property
    def resource_service(self):
        if self._resource_service is None:
            self._resource_service = ResourceService()
        return self._resource_service

    # Lazy evaluation:
    # END
    
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
    try:
        auth = Authentication()
        account_info = AccountInfo()
        iam_token = auth.get_iam_token()
        projects = account_info.list_projects(iam_token)
        return [{"id": project["metadata"]["guid"], "name": project["entity"]["name"]} for project in projects]
    except Exception as e:
        logger.error(f"Error getting projects: {str(e)}")
        return []

def select_project(project_id: str):
    try:
        return {"status": "Project selected", "project_id": project_id}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "Error", "message": str(e)}