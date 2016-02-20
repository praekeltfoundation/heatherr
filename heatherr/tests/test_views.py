import json

from django.test import override_settings
from django.test.client import RequestFactory

from heatherr.tests import (
    HeatherrTestCase, CommandTestMixin, BotTestMixin)
from heatherr.views import dispatcher, BotRouter, BotMessage, Dispatcher


class TestDispatcher(HeatherrTestCase, CommandTestMixin):

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


class TestBotRouter(HeatherrTestCase, BotTestMixin):

    def test_bot_ambient(self):

        bot = BotRouter('the-bot')

        @bot.ambient(r'.+$')
        def echo(request, match):
            return '%s said %s' % (request.bot_name, request.message['text'])

        [response] = bot.handle(self.mk_bot_request({
            'text': 'the text',
            'type': 'message',
            'channel': 'C1000',
        }, bot_name='bot'))
        self.assertEqual(response, 'bot said the text')

    def test_bot_direct_mention(self):
        bot = BotRouter('the-bot')

        @bot.ambient('@BOTUSERID: hi there!')
        def echo(request, match):
            return 'direct mention to %s' % (request.bot_name,)

        [response] = bot.handle(self.mk_bot_request({
            'text': '<@bot-user-id>: hi there!',
            'type': 'message',
            'channel': 'C1000',
        }))
        self.assertEqual(response, 'direct mention to bot-user-name')

    def test_bot_mention(self):
        bot = BotRouter('the-bot')

        @bot.ambient('hi there @BOTUSERID')
        def echo(request, match):
            return 'mention to %s' % (request.bot_name,)

        [response] = bot.handle(self.mk_bot_request({
            'text': 'hi there <@bot-user-id>',
            'type': 'message',
            'channel': 'C1000',
        }))
        self.assertEqual(response, 'mention to bot-user-name')

    def test_bot_direct_message(self):
        bot = BotRouter('the-bot')

        @bot.direct_message(r'^.+$')
        def echo(request, match):
            return '%s said %s' % (request.bot_name, request.message['text'])

        self.assertEqual(
            bot.handle(self.mk_bot_request({
                'text': 'the text',
                'type': 'message',
                'channel': 'D1000',
            })),
            ['bot-user-name said the text'])

        self.assertEqual(
            bot.handle(self.mk_bot_request({
                'text': 'the text',
                'type': 'message',
                #  NOTE: this is a channel starting with C
                #        ie, not a direct message
                'channel': 'C1000',
            })),
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
        self.assertEqual(bot.handle(self.mk_bot_request({
            'ok': False
        })), None)

    def test_received_echo(self):
        bot = BotRouter('the-bot')
        self.assertEqual(bot.handle(self.mk_bot_request({
            'user': 'bot-user-id',
            'type': 'message',
            'text': 'marco polo',
        })), None)

    def test_unknown_type(self):
        bot = BotRouter('the-bot')
        self.assertEqual(bot.handle(self.mk_bot_request({
            'type': 'foo'
        })), None)

    def test_dispatcher_bots(self):
        disp = Dispatcher('slack-token')
        bot = disp.bot('the-bot')

        @bot.ambient(r'.+')
        def echo(request, match):
            return request.message.reply(
                '%s: %s' % (request.bot_name, request.message['text']))

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

    def test_autodoc(self):
        bot = dispatcher.bot('bot!', auto_document=True)

        @bot.ambient('baz')
        def baz(request, match):
            """This thing returns baz"""
            return 'baz'

        [help_str] = bot.handle(self.mk_bot_request({
            'text': '<@bot-user-id>: help',
            'type': 'message',
            'channel': 'C1000',
            'ts': 1
        }))
        self.assertTrue('This thing returns baz' in help_str['text'])
        self.assertTrue('<@bot-user-id>: help' in help_str['text'])
