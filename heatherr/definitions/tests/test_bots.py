import json
import responses

from heatherr.tests.base import (
    HeatherrTestCase, BotTestMixin)
from heatherr.definitions.bots import definitions
from heatherr.definitions.models import Acronym


class TestBots(HeatherrTestCase, BotTestMixin):

    def setUp(self):
        self.slackaccount = self.get_slack_account()
        self.slackaccount.bot_user_id = 'bot-user-id'
        self.slackaccount.save()

    @responses.activate
    def test_add_definition(self):

        self.mock_api_call('reactions.add', json.dumps({}))

        self.assertEqual(Acronym.objects.count(), 0)
        definitions.handle(self.mk_bot_request({
            'text': '<@bot-user-id>: FOO is something about this',
            'type': 'message',
            'channel': 'C1000',
            'ts': 1,
        }))
        [acronym] = Acronym.objects.all()
        self.assertEqual(acronym.slackaccount, self.slackaccount)
        self.assertEqual(acronym.acronym, 'FOO')
        self.assertEqual(acronym.definition, 'something about this')

    def test_get_definition(self):

        self.mock_api_call('chat.postMessage', json.dumps({}))

        Acronym.objects.create(
            slackaccount=self.slackaccount,
            acronym='FOO',
            definition='something about FOO')

        [resp] = definitions.handle(self.mk_bot_request({
            'text': '<@bot-user-id>: FOO?',
            'type': 'message',
            'channel': 'C1000',
            'ts': 1,
        }))
        self.assertEqual(resp['text'], 'something about FOO (1)')

    @responses.activate
    def test_remove_definitions(self):

        self.mock_api_call('reactions.add', json.dumps({}))

        acronym = Acronym.objects.create(
            slackaccount=self.slackaccount,
            acronym='FOO',
            definition='something about FOO')
        [resp] = definitions.handle(self.mk_bot_request({
            'text': '<@bot-user-id>: remove %s for %s' % (
                acronym.pk, acronym.acronym),
            'type': 'message',
            'channel': 'C1000',
            'ts': 1,
        }))
        call = responses.calls[0]
        self.assertEqual(
            call.request.url, 'https://slack.com/api/reactions.add')
        self.assertTrue('thumbsup' in call.request.body)

    def test_remove_non_existent_definitions(self):
        [resp] = definitions.handle(self.mk_bot_request({
            'text': '<@bot-user-id>: remove 1 for FOO',
            'type': 'message',
            'channel': 'C1000',
            'ts': 1,
        }))
        self.assertEqual(resp['text'], 'Sorry, don\'t know what to delete.')
