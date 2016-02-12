import json

from django.test import override_settings
from django.test.client import RequestFactory

from heatherr.tests import CommandTestCase
from heatherr.views import dispatcher, BotRouter, BotMessage, Dispatcher


class TestDispatcher(CommandTestCase):

    def test_not_found_handler(self):
        self.assertCommandResponse(
            '/foo bar baz',
            'Sorry, I don\'t know what to do with `/foo`.')

    def test_token(self):
        with override_settings(SLACK_TOKEN='foo'):
            response = self.send_command('/foo', token='baz')
            self.assertContains(
                response, 'Invalid or missing slack token.', status_code=400)

    def test_autodoc(self):
        app = dispatcher.command('/foo')

        @app.respond('baz')
        def baz(request, match):
            """This thing returns baz"""
            return 'baz'

        response = self.send_command('/foo help')
        self.assertContains(response, 'This thing returns baz')
        dispatcher.unregister('/foo')


class TestBotRouter(CommandTestCase):

    def test_bot_ambient(self):

        bot = BotRouter('the-bot')

        @bot.ambient(r'.+$')
        def echo(bot_user_id, message, match):
            return '%s said %s' % (bot_user_id, message['text'])

        [response] = bot.handle('the-bot-user-id', {
            'text': 'the text',
            'type': 'message',
            'channel': 'C1000',
        })
        self.assertEqual(response, 'the-bot-user-id said the text')

    def test_bot_message(self):
        msg = {
            'channel': 'the-channel-id'
        }
        self.assertEqual(
            BotMessage(msg).reply('hi'), {
                'channel': 'the-channel-id',
                'text': 'hi',
                'id': None,
                'type': 'message'
            })
        self.assertEqual(
            BotMessage(msg).reply('hi', channel='foo', id=2, type='bar'), {
                'channel': 'foo',
                'text': 'hi',
                'id': 2,
                'type': 'bar'
            })

    def test_received_typeless(self):
        bot = BotRouter('the-bot')
        self.assertEqual(bot.handle('bot-user-id', {
            'ok': False
        }), None)

    def test_received_echo(self):
        bot = BotRouter('the-bot')
        self.assertEqual(bot.handle('bot-user-id', {
            'user': 'bot-user-id',
            'type': 'message',
            'text': 'marco polo',
        }), None)

    def test_unknown_type(self):
        bot = BotRouter('the-bot')
        self.assertEqual(bot.handle('bot-user-id', {
            'type': 'foo'
        }), None)

    def test_dispatcher_bots(self):
        disp = Dispatcher('slack-token')
        bot = disp.bot('the-bot')

        @bot.ambient(r'.+')
        def echo(bot_user_id, message, pattern):
            return message.reply('%s: %s' % (bot_user_id, message['text']))

        response = disp.bots(RequestFactory().post(
            '/bots/',
            content_type='application/json',
            HTTP_X_BOT_USER_ID='bot-user-id',
            data=json.dumps({
                'text': 'foo',
                'type': 'message',
                'channel': 'channel-id',
            })
        ))
        [reply] = json.loads(response.content)
        self.assertEqual(reply, {
            'text': 'bot-user-id: foo',
            'type': 'message',
            'channel': 'channel-id',
            'id': None,
        })
