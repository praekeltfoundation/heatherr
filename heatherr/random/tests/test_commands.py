from urllib import unquote_plus, unquote

from django.test import override_settings
from heatherr.tests.base import HeatherrTestCase, CommandTestMixin

import responses


class RandomTest(HeatherrTestCase, CommandTestMixin):

    def setUp(self):
        self.slackaccount = self.get_slack_account()

    @responses.activate
    def test_slap(self):
        self.mock_api_call('chat.postMessage', data={
            'ts': 1,
        })
        self.send_command('/slap @foo')
        [call] = responses.calls
        args = unquote(unquote_plus(call.request.body))
        self.assertTrue(
            '<@user_id> slaps <@foo> around a bit with a large trout.'
            in args)

    @responses.activate
    def test_poll(self):
        self.mock_api_call('chat.postMessage', data={
            'ts': 1,
        })
        self.mock_api_call('reactions.add', data={
            'ok': True,
        })
        with override_settings(CELERY_ALWAYS_EAGER=True):
            self.send_command(
                '/poll Should we jump off a bridge? Yes, No or Maybe?')

        [post, reaction1, reaction2, reaction3] = responses.calls
        self.assertTrue('bridge' in post.request.body)
        self.assertTrue('Yes' in post.request.body)
        self.assertTrue('No' in post.request.body)

        self.assertTrue(',' not in post.request.body)
        self.assertTrue('or' not in post.request.body)

        self.assertTrue('name=one' in reaction1.request.body)
        self.assertTrue('name=two' in reaction2.request.body)
        self.assertTrue('name=three' in reaction3.request.body)

    @responses.activate
    def test_binary_poll(self):
        self.mock_api_call('chat.postMessage', data={
            'ts': 1,
        })
        self.mock_api_call('reactions.add', data={
            'ok': True,
        })
        with override_settings(CELERY_ALWAYS_EAGER=True):
            self.send_command(
                '/poll Should we jump off a bridge?')

        [post, reaction1, reaction2] = responses.calls
        self.assertTrue('bridge' in post.request.body)

        self.assertTrue('name=thumbsup' in reaction1.request.body)
        self.assertTrue('name=thumbsdown' in reaction2.request.body)
