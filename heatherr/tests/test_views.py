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
        def echo(bot_user_id, bot_user_name, message, match):
            return '%s said %s' % (bot_user_name, message['text'])

        [response] = bot.handle('the-bot-user-id', 'bot', {
            'text': 'the text',
            'type': 'message',
            'channel': 'C1000',
        })
        self.assertEqual(response, 'bot said the text')

    def test_bot_direct_mention(self):
        bot = BotRouter('the-bot')

        @bot.ambient('@BOTUSERID: hi there!')
        def echo(bot_user_id, bot_user_name, message, match):
            return 'direct mention to %s' % (bot_user_name,)

        [response] = bot.handle('the-bot-user-id', 'bot', {
            'text': '<@the-bot-user-id>: hi there!',
            'type': 'message',
            'channel': 'C1000',
        })
        self.assertEqual(response, 'direct mention to bot')

    def test_bot_mention(self):
        bot = BotRouter('the-bot')

        @bot.ambient('hi there @BOTUSERID')
        def echo(bot_user_id, bot_user_name, message, match):
            return 'mention to %s' % (bot_user_name,)

        [response] = bot.handle('the-bot-user-id', 'bot', {
            'text': 'hi there <@the-bot-user-id>',
            'type': 'message',
            'channel': 'C1000',
        })
        self.assertEqual(response, 'mention to bot')

    def test_bot_direct_message(self):
        bot = BotRouter('the-bot')

        @bot.direct_message(r'^.+$')
        def echo(bot_user_id, bot_user_name, message, match):
            return '%s said %s' % (bot_user_name, message['text'])

        self.assertEqual(
            bot.handle('the-bot-user-id', 'bot', {
                'text': 'the text',
                'type': 'message',
                'channel': 'D1000',
            }),
            ['bot said the text'])

        self.assertEqual(
            bot.handle('the-bot-user-id', 'bot', {
                'text': 'the text',
                'type': 'message',
                #  NOTE: this is a channel starting with C
                #        ie, not a direct message
                'channel': 'C1000',
            }),
            [])

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
        self.assertEqual(bot.handle('bot-user-id', 'bot', {
            'ok': False
        }), None)

    def test_received_echo(self):
        bot = BotRouter('the-bot')
        self.assertEqual(bot.handle('bot-user-id', 'bot', {
            'user': 'bot-user-id',
            'type': 'message',
            'text': 'marco polo',
        }), None)

    def test_unknown_type(self):
        bot = BotRouter('the-bot')
        self.assertEqual(bot.handle('bot-user-id', 'bot', {
            'type': 'foo'
        }), None)

    def test_dispatcher_bots(self):
        disp = Dispatcher('slack-token')
        bot = disp.bot('the-bot')

        @bot.ambient(r'.+')
        def echo(bot_user_id, bot_user_name, message, pattern):
            return message.reply('%s: %s' % (bot_user_name, message['text']))

        response = disp.bots(RequestFactory().post(
            '/bots/',
            content_type='application/json',
            HTTP_X_BOT_USER_ID='bot-user-id',
            HTTP_X_BOT_USER_NAME='bot',
            data=json.dumps({
                'text': 'foo',
                'type': 'message',
                'channel': 'channel-id',
            })
        ))
        [reply] = json.loads(response.content)
        self.assertEqual(reply, {
            'text': 'bot: foo',
            'type': 'message',
            'channel': 'channel-id',
            'id': None,
        })
