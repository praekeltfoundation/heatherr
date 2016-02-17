from __future__ import absolute_import

from functools import wraps
from collections import defaultdict

import json
import warnings
import re
import inspect

import logging

from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from heatherr.models import SlackAccount


logger = logging.getLogger(__name__)


class NotFoundHandler(object):

    def handle(self, request):
        return JsonResponse({
            "text": "Sorry, I don't know what to do with `%s`." % (
                request.POST['command'],)
        })


class Dispatcher(object):

    def __init__(self, slack_token):
        self.slack_token = slack_token
        self.command_registry = {}
        self.bot_registry = {}

    def register(self, command, handler):
        self.command_registry[command] = handler

    def unregister(self, command):
        return self.command_registry.pop(command, None)

    def command(self, command, auto_document=True):
        r = CommandRouter(command=command)
        if auto_document:
            r.auto_document()
        self.register(r.command, r)
        return r

    def bot(self, name, auto_document=True):
        r = BotRouter(name)
        if auto_document:
            r.auto_document()
        self.bot_registry.setdefault(name, r)
        return self.bot_registry[name]

    @csrf_exempt
    def commands(self, request):
        if self.slack_token != request.POST.get('token'):
            return HttpResponseBadRequest('Invalid or missing slack token.')

        command = request.POST['command']
        handler = self.command_registry.get(command, NotFoundHandler())
        return handler.handle(request)

    @csrf_exempt
    def bots(self, request):
        bot_user_id = request.META['HTTP_X_BOT_USER_ID']
        bot_user_name = request.META['HTTP_X_BOT_USER_NAME']
        data = json.load(request)

        if not data:
            logger.info('Received empty data from Heatherrd: %r' % (data,))
            return JsonResponse([], safe=False)

        bot_responses = []
        for bot in self.bot_registry.values():
            responses = bot.handle(bot_user_id, bot_user_name, data)
            if responses:
                bot_responses.extend(responses)

        return JsonResponse(filter(None, bot_responses), safe=False)


class BotMessage(dict):

    def reply(self, text, type='message', channel=None, id=None):
        return {
            'id': id,
            'type': type,
            'channel': channel or self.get('channel'),
            'text': text,
        }


class BotRouter(object):

    def __init__(self, name):
        self.name = name
        self.registry_ambient = defaultdict(list)
        self.registry_direct_message = defaultdict(list)

    def _registry_decorator(self, patterns, registry):
        def decorator(func):
            registry[func].extend(patterns)
            # setattr(func, 'patterns', patterns)

            @wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)
            return handler
        return decorator

    def ambient(self, *patterns):
        return self._registry_decorator(
            list(patterns), self.registry_ambient)

    def direct_message(self, *patterns):
        return self._registry_decorator(
            list(patterns), self.registry_direct_message)

    def auto_document(self):
        self.ambient(r'^@BOTUSERID: help$')(self.handle_ambient_help)
        # self.direct_message(r'^help$', r'^@BOTUSERID: help$')(
        #     self.handle_direct_message_help)

    def handle_ambient_help(
            self, bot_user_id, bot_user_name, message, match):
        """
        Ask a bot for help:

            @BOTUSERID: help

        Prints out the help for the bot.
        """
        docstrings = '\n\n'.join(
            [inspect.cleandoc(func.__doc__) for func in self.registry_ambient])

        help_str = 'Help for *%s*\n\n%s' % (self.name, docstrings)
        return help_str\
            .replace('@BOTUSERID', '<@%s>' % (bot_user_id,)) \
            .replace('BOTUSERNAME', bot_user_name)

    def handle(self, bot_user_id, bot_user_name, message):
        logger.debug(repr(message))
        if 'type' not in message:
            if not message['ok']:
                logger.warn(repr(message))
            return

        if message.get('user') == bot_user_id:
            logger.debug('Slack echoed back a bots own message.')
            return

        message_type = message['type']
        handler_name = 'handle_%s' % (message_type,)
        if not hasattr(self, handler_name):
            warnings.warn(
                '%s is unable to handle message type: %s' % (
                    self.name, message_type,),
                RuntimeWarning)
            return None

        return getattr(self, handler_name)(bot_user_id, bot_user_name, message)

    def handle_message(self, bot_user_id, bot_user_name, message):
        registry = self.get_registry(bot_user_id, message)
        responses = []
        for handler, patterns in registry.items():
            for pattern in patterns:
                p1 = re.sub('@BOTUSERID', '<@%s>' % (bot_user_id,), pattern)
                p2 = re.sub('BOTUSERNAME', bot_user_name, p1)
                match = re.match(p2, message['text'])
                if match:
                    responses.append(
                        handler(bot_user_id,
                                bot_user_name,
                                BotMessage(message),
                                match))
        return responses

    def get_registry(self, bot_user_id, message):
        if message['channel'].startswith('D'):
            return self.registry_direct_message
        return self.registry_ambient

    def handle_pong(self, bot_user_id, bot_user_name, message):
        SlackAccount.objects.filter(bot_user_id=bot_user_id).update(
            bot_status=SlackAccount.ONLINE,
            bot_checkin=timezone.now())


class CommandRouter(object):

    def __init__(self, command=None):
        self.registry = defaultdict(list)
        self.command = command

    def respond(self, *patterns):
        def decorator(func):
            self.registry[func].extend(list(patterns))
            setattr(func, 'patterns', frozenset(patterns))

            @wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)
            return handler
        return decorator

    def handle(self, request):
        text = request.POST['text']
        for handler, patterns in self.registry.items():
            for pattern in patterns:
                match = re.match(pattern, text)
                if match:
                    response = handler(request, match)
                    if isinstance(response, basestring):
                        return JsonResponse({
                            'text': response
                        })
                    return response
        return self.noop(text)

    def auto_document(self):
        self.registry[self.auto_document_handler].append(r'^help$')

    def auto_document_handler(self, request, match):
        """
        `help`

        Prints out the help for this command handler.
        """
        docstrings = '\n\n'.join(
            [inspect.cleandoc(func.__doc__) for func in self.registry])
        if self.command:
            return 'Help for *%s*\n\n%s' % (self.command, docstrings)
        return docstrings

    def noop(self, text):
        return JsonResponse({
            'text': 'Sorry, don\'t know what to do.'
        })


dispatcher = Dispatcher(settings.SLACK_TOKEN)
