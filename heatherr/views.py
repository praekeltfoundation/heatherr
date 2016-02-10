from __future__ import absolute_import

from functools import wraps
from collections import defaultdict

import json
import warnings
import re
import inspect

import requests

import logging

from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

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
        self.bot_registry.setdefault(name, BotRouter(name))
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
        bot_access_token = request.META['HTTP_X_BOT_ACCESS_TOKEN']
        bot_user_id = request.META['HTTP_X_BOT_USER_ID']
        data = json.load(request)
        responses = dict([(name, bot.handle(bot_user_id,
                                            bot_access_token,
                                            data))
                          for name, bot in self.bot_registry.items()])
        return JsonResponse(responses)


class BotMessage(dict):

    def reply(self, text, type='message', channel=None, id=None):
        return {
           'id': id,
           'type': type,
           'channel': self.get('channel', channel),
           'text': text,
        }


class BotRouter(object):

    def __init__(self, name):
        self.name = name
        self.registry = defaultdict(list)

    def ambient(self, *patterns):
        def decorator(func):
            self.registry[func].extend(list(patterns))
            setattr(func, 'patterns', frozenset(patterns))

            @wraps(func)
            def handler(*args, **kwargs):
                return func(*args, **kwargs)
            return handler
        return decorator

    def handle(self, bot_user_id, bot_access_token, message):
        logger.debug(repr(message))
        if 'type' not in message:
            if not message['ok']:
                logger.warn(repr(message))
            return

        if message.get('user') == bot_user_id:
            logger.debug('Got echoed back a bots own message.')
            return

        message_type = message['type']
        handler_name = 'handle_%s' % (message_type,)
        if not hasattr(self, handler_name):
            warnings.warn(
                '%s is unable to handle message type: %s' % (
                    self.name, message_type,),
                RuntimeWarning)
            return None

        return getattr(self, handler_name)(bot_access_token, message)

    def handle_message(self, bot_access_token, message):
        text = message['text']
        for handler, patterns in self.registry.items():
            for pattern in patterns:
                match = re.match(pattern, text)
                if match:
                    handler(
                        BotMessage(bot_access_token, message), match)




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
