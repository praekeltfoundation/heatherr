import json
from urllib import unquote_plus, unquote

from heatherr.tests.base import CommandTestCase

import responses


class RandomTest(CommandTestCase):

    def setUp(self):
        self.slackaccount = self.get_slack_account()

    @responses.activate
    def test_slap(self):

        self.mock_api_call('chat.postMessage', data=json.dumps({}))
        self.send_command('/slap @foo')
        [call] = responses.calls
        args = unquote(unquote_plus(call.request.body))
        self.assertTrue(
            '<@user_id> slaps <@foo> around a bit with a large trout.'
            in args)
