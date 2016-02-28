from django.contrib.auth.models import User

import responses

from heatherr.tests.base import HeatherrTestCase


class SlackAccountTest(HeatherrTestCase):

    @responses.activate
    def test_api_call(self):
        user = User.objects.create_user(
            'username', 'user@example.org', 'password')
        slackaccount = self.get_slack_account()
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
