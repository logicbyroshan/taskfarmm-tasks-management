import json
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from todo.models import Category, UserProfile

User = get_user_model()


class GoogleSSOTests(TestCase):
    def setUp(self):
        self.client_id = "mock-google-client-id.apps.googleusercontent.com"
        self.client_secret = "mock-google-client-secret"

    def test_google_login_unconfigured_renders_setup_page(self):
        """When GOOGLE_CLIENT_ID is not configured, renders the setup/dev guide."""
        with override_settings(GOOGLE_CLIENT_ID='', GOOGLE_CLIENT_SECRET=''):
            res = self.client.get(reverse('google_login'))
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, "Google SSO Configuration")
            self.assertContains(res, "Sign In with Test Google Account")

    def test_google_login_configured_redirects_to_google(self):
        """When GOOGLE_CLIENT_ID is configured, redirects to accounts.google.com."""
        with override_settings(GOOGLE_CLIENT_ID=self.client_id, GOOGLE_CLIENT_SECRET=self.client_secret):
            res = self.client.get(reverse('google_login'))
            self.assertEqual(res.status_code, 302)
            self.assertIn("accounts.google.com/o/oauth2/v2/auth", res.url)
            self.assertIn(self.client_id, res.url)
            self.assertIn("google_oauth_state", self.client.session)

    def test_google_callback_state_mismatch_rejected(self):
        """Callback with mismatched state returns to login with error."""
        with override_settings(GOOGLE_CLIENT_ID=self.client_id, GOOGLE_CLIENT_SECRET=self.client_secret):
            session = self.client.session
            session['google_oauth_state'] = 'correct-state'
            session.save()

            res = self.client.get(reverse('google_callback'), {'code': 'mock_code', 'state': 'wrong-state'}, follow=True)
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, "Authentication session expired or state verification failed")

    @patch('urllib.request.urlopen')
    def test_google_callback_successful_new_user_provisioning(self, mock_urlopen):
        """Callback successfully exchanges code, fetches profile, provisions user & starter project."""
        with override_settings(GOOGLE_CLIENT_ID=self.client_id, GOOGLE_CLIENT_SECRET=self.client_secret):
            session = self.client.session
            session['google_oauth_state'] = 'valid-test-state'
            session.save()

            # Mock token response
            mock_token_resp = MagicMock()
            mock_token_resp.read.return_value = json.dumps({'access_token': 'mock-access-token'}).encode('utf-8')
            mock_token_resp.__enter__.return_value = mock_token_resp

            # Mock userinfo response
            mock_userinfo_resp = MagicMock()
            mock_userinfo_resp.read.return_value = json.dumps({
                'email': 'alice.wonderland@gmail.com',
                'given_name': 'Alice',
                'family_name': 'Wonderland',
                'picture': 'https://example.com/avatar.jpg'
            }).encode('utf-8')
            mock_userinfo_resp.__enter__.return_value = mock_userinfo_resp

            mock_urlopen.side_effect = [mock_token_resp, mock_userinfo_resp]

            res = self.client.get(reverse('google_callback'), {'code': 'auth_code_123', 'state': 'valid-test-state'}, follow=True)
            self.assertEqual(res.status_code, 200)

            # Check user created
            user = User.objects.filter(email='alice.wonderland@gmail.com').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.first_name, 'Alice')
            self.assertEqual(user.last_name, 'Wonderland')
            self.assertTrue(user.is_active)

            # Check starter project created
            self.assertTrue(Category.objects.filter(user=user, name="General Tasks").exists())

    @patch('urllib.request.urlopen')
    def test_google_gis_credential_callback(self, mock_urlopen):
        """Google Identity Services ID Token credential verification."""
        with override_settings(GOOGLE_CLIENT_ID=self.client_id):
            mock_tokeninfo_resp = MagicMock()
            mock_tokeninfo_resp.read.return_value = json.dumps({
                'aud': self.client_id,
                'email': 'bob.builder@gmail.com',
                'given_name': 'Bob',
                'family_name': 'Builder'
            }).encode('utf-8')
            mock_tokeninfo_resp.__enter__.return_value = mock_tokeninfo_resp
            mock_urlopen.return_value = mock_tokeninfo_resp

            res = self.client.post(
                reverse('google_credential'),
                data=json.dumps({'credential': 'mock-jwt-id-token'}),
                content_type='application/json'
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data['success'])

            user = User.objects.filter(email='bob.builder@gmail.com').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.first_name, 'Bob')

    def test_google_dev_demo_login(self):
        """Dev login helper creates and logs in user when tested locally."""
        res = self.client.post(reverse('google_dev_login'), {
            'email': 'local.developer@gmail.com',
            'first_name': 'Local',
            'last_name': 'Dev'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        user = User.objects.filter(email='local.developer@gmail.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, 'Local')
