from django.test import TestCase
from django.contrib.auth.models import User

import responses

from heatherr.models import SlackAccount


class SlackAccountTest(TestCase):

    @responses.activate
    def test_api_call(self):
        user = User.objects.create_user(
            'username', 'user@example.org', 'password')
        slackaccount = SlackAccount.objects.create(user=user)
        slackaccount.access_token = 'the-access-token'
        slackaccount.save()

        responses.add(responses.POST, 'https://slack.com/api/foo.bar', json={
            'ok': True,
            'stuff': 'this is good',
        })

        response = slackaccount.api_call('foo.bar', extra_param=1)
        self.assertEqual(response, {
            'ok': True,
            'stuff': 'this is good',
        })
