from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from heatherr.models import SlackAccount

import responses


class HeatherrTestCase(TestCase):

    default_team_id = 'team_id'
    default_user_name = 'username'

    def get_user_account(self, username=None):
        user, _ = User.objects.get_or_create(
            username=(username or self.default_user_name))
        user.is_active = True
        user.save()
        return user

    def get_slack_account(self, username=None, team_id=None):
        user = self.get_user_account(username)
        slackaccount, _ = SlackAccount.objects.get_or_create(
            user=user, team_id=(team_id or self.default_team_id))
        return slackaccount

    def mock_api_call(self, method, data):
        responses.add(
            responses.POST, 'https://slack.com/api/%s' % (method,),
            json=data)


class CommandTestCase(HeatherrTestCase):

    default_user_id = 'user_id'
    default_channel_id = 'channel_id'
    default_channel_name = 'channel_name'

    def send_command(self, command_str,
                     team_id=None, user_id=None, user_name=None,
                     channel_id=None, channel_name=None,
                     token=None):
        team_id = team_id or self.default_team_id
        user_id = user_id or self.default_user_id
        user_name = user_name or self.default_user_name
        channel_id = channel_id or self.default_channel_id
        channel_name = channel_name or self.default_channel_name
        token = token or settings.SLACK_TOKEN
        command, _, text = command_str.partition(' ')
        parameters = {
            'token': token,
            'command': command,
            'text': text,
            'team_id': team_id,
            'user_id': user_id,
            'user_name': user_name,
            'channel_id': channel_id,
            'channel_name': channel_name,
        }
        return self.client.post(reverse('dispatcher'), parameters)

    def assertCommandResponse(self, command_str, expected_response,
                              team_id=None, user_id=None, token=None,
                              response_type=None):
        response = self.send_command(command_str,
                                     team_id=team_id,
                                     user_id=user_id,
                                     token=token)
        data = response.json()
        self.assertEqual(data['text'], expected_response)
        if response_type is not None:
            self.assertEqual(data['response_type'], response_type)
