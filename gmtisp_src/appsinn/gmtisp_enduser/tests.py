# gmtisp_enduser/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch
from requests.exceptions import HTTPError

User = get_user_model()  # Get the custom user model

class LoginViewTests(TestCase):
    def setUp(self):
        # Create a test user using the custom user model
        self.username = 'beckuser'
        self.password = '123'
        self.email = 'beckuser@you.com'
        User.objects.create_user(username=self.username, password=self.password, email=self.email)
        self.client = Client()

    @patch('gmtisp_enduser.services.OpenWispAPIClient')
    def test_login_success(self, MockOpenWispAPIClient):
        # Mock the API client methods
        mock_client = MockOpenWispAPIClient.return_value
        mock_client.get_auth_token.return_value = 'testtoken'
        mock_client.get_user_details.return_value = {
            'username': self.username,
            'email': self.email,
            # 'first_name': 'Test',
            # 'last_name': 'User'
        }

        # Data for successful login
        login_data = {'username': self.username, 'password': self.password}
        
        # Post request to login
        response = self.client.post(reverse('login'), login_data)
        
        # Assert that we are redirected to the profile page
        self.assertRedirects(response, reverse('profile'))
        
        # Check session data
        self.assertEqual(self.client.session.get('username'), self.username)
        self.assertEqual(self.client.session.get('email'), self.email)
        # self.assertEqual(self.client.session.get('first_name'), 'Test')
        # self.assertEqual(self.client.session.get('last_name'), 'User')
