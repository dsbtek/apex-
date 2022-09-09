from django.urls import reverse
from django.core import mail
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from .. import models

class UserLogin(APITestCase):
    def setUp(self):
        data_1 = {
            'Email': "rahman.s@e360africa.com"
        }
        data_2 = {
            'Email': "solankerahman@gmail.com",
            'is_active': False
        }
        get_user_model().objects.create_user(**data_1)
        get_user_model().objects.create_user(**data_2)


    def test_login_user(self):
        url = reverse('login')
        data = {
            'Email': 'rahman.s@e360africa.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'token')
        self.assertContains(response, 'user')
        # check if logged in signal was sent
        self.assertIsNotNone(get_user_model().objects.get(pk=1).last_login)

    def test_invalid_user_login(self):
        url = reverse('login')
        data = {
            'Email': 'rahman.sol@e360africa.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertGreaterEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertLessEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inactive_user_login(self):
        url = reverse('login')
        data = {
            'Email': 'solankerahman@gmail.com',
            'password': 'password'
        }
        response = self.client.post(url, data, format='json')
        self.assertGreaterEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertLessEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class UserResetPassword(APITestCase):
    def setUp(self):
        data_1 = {
            'Email': "rahman.s@e360africa.com"
        }
        data_2 = {
            'Email': "solankerahman@gmail.com",
            'is_active': False
        }
        get_user_model().objects.create_user(**data_1)
        get_user_model().objects.create_user(**data_2)

    def test_valid_user_can_request_for_password_change(self):
        url = reverse('password_reset')
        response = self.client.post(url, {'Email': 'rahman.s@e360africa.com'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    #test that mail is sent
    def test_mail_sent_on_password_reset_request(self):
        url = reverse('password_reset')
        response = self.client.post(url, {'Email': 'rahman.s@e360africa.com'}, format='json')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Smarteye account Password Reset')
        self.assertEqual(mail.outbox[0].from_email, 'support@e360.com')
        self.assertEqual(mail.outbox[0].to[0], 'rahman.s@e360africa.com')
        
    #test that password reset object is created in db
    def test_password_reset_object_created_in_db_upon_password_reset_request(self):
        url = reverse('password_reset')
        response = self.client.post(url, {'Email': 'rahman.s@e360africa.com'}, format='json')

        self.assertTrue(models.PasswordReset.objects.filter(user_id=1).exists())
    
    #test that invalid user can't request
    def test_invalid_user_cant_request_for_password_change(self):
        url = reverse('password_reset')
        response = self.client.post(url, {'Email': 'rahman.sol@e360africa.com'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    #test that inactive user can't request
    def test_inactive_user_cant_request_for_password_change(self):
        url = reverse('password_reset')
        response = self.client.post(url, {'Email': 'solankerahman@gmail.com'}, format='json')
       
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def generate_reset_link_from_mail_body(self):
        import re
        url = reverse('password_reset')
        self.client.post(url, {'Email': 'rahman.s@e360africa.com'}, format='json')
        try:
            return re.search("resetpassword/(.*)\?reset", mail.outbox[0].body).group(1)
        except AttributeError:
            return None

    #test valid reset link
    def test_valid_password_reset_link(self):
        #extract uid and token from email sent
        token_uid_string = self.generate_reset_link_from_mail_body()
        if token_uid_string is None:
            #fail the test
            self.fail("Reset link returned a None instance")
        token_uid_list = token_uid_string.split('/')
        uid = token_uid_list[0]
        token = token_uid_list[1]

        reset_link = reverse('password_reset_confirm', kwargs={'uid':uid, 'token':token})
        response = self.client.get(reset_link, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_password_reset_link(self):
        #extract uid and token from email sent
        token_uid_string = self.generate_reset_link_from_mail_body()
        if token_uid_string is None:
            #fail the test
            self.fail("Reset link returned a None instance")
        token_uid_list = token_uid_string.split('/')
        uid = token_uid_list[0]
        token = token_uid_list[1][-2:]

        reset_link = reverse('password_reset_confirm', kwargs={'uid':uid, 'token':token})
        response = self.client.get(reset_link, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_confirmation_status_of_reset_object_after_visiting_link(self):
        token_uid_string = self.generate_reset_link_from_mail_body()
        if token_uid_string is None:
            #fail the test
            self.fail("Reset link returned a None instance")
        token_uid_list = token_uid_string.split('/')
        uid = token_uid_list[0]
        token = token_uid_list[1]

        reset_link = reverse('password_reset_confirm', kwargs={'uid':uid, 'token':token})
        self.client.get(reset_link, format='json')
        reset_object = models.PasswordReset.objects.get(user_id=uid, token=token)
        self.assertTrue(reset_object.confirmation_status)
    
    def test_valid_password_change(self):
        token_uid_string = self.generate_reset_link_from_mail_body()
        if token_uid_string is None:
            #fail the test
            self.fail("Reset link returned a None instance")
        token_uid_list = token_uid_string.split('/')
        uid = token_uid_list[0]
        token = token_uid_list[1]

        url = reverse('password_change')
        response = self.client.post(url, {'user_id':uid, 'token':token, 'password':'new_password'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_user_password_change(self):
        url = reverse('password_change')
        response = self.client.post(url, {'user_id':4, 'token': 'nyddu','password':'new_password'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_inactive_user_password_change(self):
        url = reverse('password_change')
        response = self.client.post(url, {'user_id':2, 'token': 'nyddu', 'password':'new_password'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_password_really_changed_after_password_change(self):
        token_uid_string = self.generate_reset_link_from_mail_body()
        if token_uid_string is None:
            #fail the test
            self.fail("Reset link returned a None instance")
        token_uid_list = token_uid_string.split('/')
        uid = token_uid_list[0]
        token = token_uid_list[1]

        url = reverse('password_change')
        self.client.post(url, {'user_id':uid, 'token': token,'password':'new_password'}, format='json')
        user = get_user_model().objects.get(pk=uid)
        self.assertTrue(user.check_password('new_password'))

    def test_cant_use_reset_link_after_setting_new_password(self):
        token_uid_string = self.generate_reset_link_from_mail_body()
        if token_uid_string is None:
            #fail the test
            self.fail("Reset link returned a None instance")
        token_uid_list = token_uid_string.split('/')
        uid = token_uid_list[0]
        token = token_uid_list[1]

        url = reverse('password_change')
        self.client.post(url, {'user_id':uid, 'token': token, 'password':'new_password'}, format='json')

        reset_link = reverse('password_reset_confirm', kwargs={'uid':uid, 'token':token})


    #A test checker that smarteye api ci run sucessfully.