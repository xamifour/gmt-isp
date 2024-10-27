# curl -H "Authorization: Bearer 913e4862fedabc7fad8950c1feba131d58f1e2ad" http://127.0.0.1:8000/api/v1/users/user/
# ka@Kwames-MacBook-Pro ~ % curl -H "Authorization: Bearer <your_token>" http://127.0.0.1:8000/api/v1/users/user/


# gmtisp_enduser/services.py

import os
import requests
import logging
from requests.exceptions import HTTPError

BASE_URL = os.getenv('API_BASE_URL', 'http://127.0.0.1:8000/api/v1/')

class OpenWispAPIClient:
    def __init__(self, base_url=BASE_URL, username=None, password=None):
        self.base_url = base_url
        self.session = requests.Session()
        if username and password:
            self.authenticate(username, password)

    def authenticate(self, username: str, password: str) -> None:
        auth_url = f"{self.base_url}api/token/"
        try:
            response = self.session.post(auth_url, data={'username': username, 'password': password})
            response.raise_for_status()
            self.token = response.json().get('token')
            self.session.headers.update({'Authorization': f'Token {self.token}'})
        except HTTPError as e:
            logging.error(f"Authentication failed: {e}")
            raise

    def request(self, method: str, endpoint: str, **kwargs) -> dict:
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            logging.error(f"Request failed: {e}")
            raise

    def get_user(self, user_id: str) -> dict:
        return self.request('GET', f'users/{user_id}/')  # Consistent path

    def create_user(self, user_data: dict) -> dict:
        return self.request('POST', 'users/', json=user_data)  # Consistent path

    def update_user(self, user_id: str, user_data: dict) -> dict:
        return self.request('PUT', f'users/{user_id}/', json=user_data)  # Consistent path

    def delete_user(self, user_id: str) -> None:
        self.request('DELETE', f'users/{user_id}/')  # Consistent path
