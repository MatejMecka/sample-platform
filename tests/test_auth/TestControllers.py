import time

from tests.base import BaseTestCase, signup_information
from flask import url_for
from mod_auth.controllers import generate_hmac_hash


class TestSignUp(BaseTestCase):

    def test_if_email_signup_form_renders(self):
        response = self.app.test_client().get(url_for('auth.signup'))
        self.assertEqual(response.status_code, 200)
        self.assert_template_used('auth/signup.html')

    def test_blank_email(self):
        response = self.signup(email='')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email address is not filled in', response.data)

    def test_invalid_email_address(self):
        invalid_email_address = ['plainaddress',
                                 '#@%^%#$@#$@#.com',
                                 '@domain.com',
                                 'Joe Smith <email@domain.com>',
                                 'email.domain.com',
                                 'email@domain.com (Joe Smith)',
                                 'email@-domain.com',
                                 'email@111.222.333.44444']

        for email in invalid_email_address:
            with self.subTest():
                response = self.signup(email)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'Entered value is not a valid email address', response.data)

    def test_existing_email_signup(self):
        response = self.signup(email=signup_information['existing_user_email'])
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email sent for verification purposes. Please check your mailbox', response.data)

    def test_valid_email_signup(self):
        response = self.signup(email=signup_information['valid_email'])
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email sent for verification purposes. Please check your mailbox', response.data)

    def signup(self, email):
        return self.app.test_client().post(url_for('auth.signup'), data=dict(email=email), follow_redirects=True)


class CompleteSignUp(BaseTestCase):

    def setUp(self):
        self.time_of_hash = int(time.time())
        content_to_hash = "{email}|{expiry}".format(email=signup_information['valid_email'], expiry=self.time_of_hash)
        self.hash = generate_hmac_hash(self.app.config.get('HMAC_KEY', ''), content_to_hash)
        content_to_hash = "{email}|{expiry}".format(email=signup_information['existing_user_email'],
                                                    expiry=self.time_of_hash)
        self.existing_user_hash = generate_hmac_hash(self.app.config.get('HMAC_KEY', ''), content_to_hash)

    def test_if_link_expired(self):
        response = self.complete_signup(signup_information['valid_email'], self.time_of_hash+3600, self.hash)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'The request to complete the registration was invalid.', response.data)

    def test_if_wrong_link(self):
        response = self.complete_signup(signup_information['existing_user_email'], self.time_of_hash, self.hash)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'The request to complete the registration was invalid.', response.data)

    def test_if_valid_link(self):
        response = self.complete_signup(signup_information['valid_email'], self.time_of_hash, self.hash)
        self.assertEqual(response.status_code, 200)
        self.assert_template_used('auth/complete_signup.html')

    def test_if_password_is_blank(self):
        response = self.complete_signup(signup_information['valid_email'], self.time_of_hash, self.hash,
                                        name=signup_information['existing_user_name'], password='', password_repeat='')
        self.assertEqual(response.status_code, 200)
        self.assert_template_used('auth/complete_signup.html')
        self.assertIn(b'Password is not filled in', response.data)

    def test_if_password_length_is_invalid(self):
        response = self.complete_signup(signup_information['valid_email'], self.time_of_hash, self.hash,
                                        name=signup_information['existing_user_name'], password='small',
                                        password_repeat='small')
        self.assertEqual(response.status_code, 200)
        self.assert_template_used('auth/complete_signup.html')
        self.assertIn(b'Password needs to be between', response.data)

    def test_if_passwords_dont_match(self):
        response = self.complete_signup(signup_information['valid_email'], self.time_of_hash, self.hash,
                                        name=signup_information['existing_user_name'], password='some_password',
                                        password_repeat='another_password')
        self.assertEqual(response.status_code, 200)
        self.assert_template_used('auth/complete_signup.html')
        self.assertIn(b'The password needs to match the new password', response.data)

    def complete_signup(self, email, expires, mac, name='', password='', password_repeat=''):
        return self.app.test_client().post(url_for('auth.complete_signup', email=email, expires=expires, mac=mac),
                                           data=dict(name=name, password=password, password_repeat=password_repeat),
                                           follow_redirects=True)


class TestLogOut(BaseTestCase):

    def test_if_logout_redirects_to_login(self):
        response = self.app.test_client().get(url_for('auth.logout'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been logged out', response.data)
        self.assert_template_used('auth/login.html')
