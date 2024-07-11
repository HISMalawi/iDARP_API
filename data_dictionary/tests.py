from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse


class TopicsTests(APITestCase):

    def test_user_can_pull_topics(self):
        """
        Ensure we can create a new account object.
        """
        url = reverse('topics')
        print(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
