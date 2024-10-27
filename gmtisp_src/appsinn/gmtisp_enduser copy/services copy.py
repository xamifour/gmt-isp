# gmtisp_enduser/services.py
# curl -H "Authorization: Bearer 913e4862fedabc7fad8950c1feba131d58f1e2ad" http://127.0.0.1:8000/api/v1/users/user/

import requests
import logging
from requests.exceptions import HTTPError

BASE_URL = 'http://127.0.0.1:8000/api/v1/'
AUTH_TOKEN_URL = f'{BASE_URL}users/token/'
USER_LIST_URL = f'{BASE_URL}users/user/'


class OpenWispAPIClient:
    def __init__(self):
        self.base_url = BASE_URL
        self.logger = logging.getLogger(__name__)

    def get_auth_token(self, username, password):
        url = AUTH_TOKEN_URL
        try:
            response = requests.post(url, data={'username': username, 'password': password})
            response.raise_for_status()
            data = response.json()
            if 'token' in data:
                return {'token': data['token'], 'username': username}
            else:
                raise ValueError("Missing token in response")
        except HTTPError as http_err:
            if response.status_code == 400:
                raise ValueError("Invalid username or password")
            self.logger.error(f'HTTP error occurred: {http_err}', exc_info=True)
            if response.content:
                self.logger.error('Response content: %s', response.content)
            raise
        except Exception as err:
            self.logger.error(f'Other error occurred: {err}', exc_info=True)
            raise

    def get_user_details(self, token, username):
        url = USER_LIST_URL
        headers = {'Authorization': f'Bearer {token}'}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            users = response.json().get('results', [])
            for user in users:
                if user['username'] == username:
                    return user
            raise ValueError("User not found")
        except HTTPError as http_err:
            self.logger.error(f'HTTP error occurred: {http_err}', exc_info=True)
            raise
        except Exception as err:
            self.logger.error(f'Other error occurred: {err}', exc_info=True)
            raise
