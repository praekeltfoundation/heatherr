from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from heatherr.models import SlackAccount


class CommandTestCase(TestCase):

    default_user_name = 'username'
    default_team_id = 'team_id'
    default_user_id = 'user_id'

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

    def send_command(self, command_str,
                     team_id=None, user_id=None, token=None):
        team_id = team_id or self.default_team_id
        user_id = user_id or self.default_user_id
        token = token or settings.SLACK_TOKEN
        command, _, text = command_str.partition(' ')
        parameters = {
            'token': token,
            'command': command,
            'text': text,
            'team_id': team_id,
            'user_id': user_id,
        }
        return self.client.post(reverse('dispatcher'), parameters)

    def assertCommandResponse(self, command_str, expected_response,
                              team_id=None, user_id=None, token=None):
        response = self.send_command(command_str,
                                     team_id=team_id,
                                     user_id=user_id,
                                     token=token)
        self.assertEqual(response.json(), {
            'text': expected_response,
        })
