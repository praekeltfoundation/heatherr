from __future__ import absolute_import

from functools import wraps
from collections import defaultdict
import re

from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt



class NotFoundHandler(object):

    def handle(self, request):
        return JsonResponse({
            "text": "Sorry, I don't know what to do with `%s`." % (
                request.POST['command'],)
        })


class Dispatcher(object):

    def __init__(self, slack_token):
        self.slack_token = slack_token
        self.registry = {}

    def register(self, command, handler):
        self.registry[command] = handler

    def unregister(self, command):
        return self.registry.pop(command)

    def command(self, command):
        r = CommandRouter()
        self.register(command, r)
        return r

    @csrf_exempt
    def view(self, request):
        if self.slack_token != request.POST.get('token'):
            return HttpResponseBadRequest('Invalid or missing slack token.')

        command = request.POST['command']
        handler = self.registry.get(command, NotFoundHandler())
        return handler.handle(request)


class CommandRouter(object):

    def __init__(self):
        self.registry = defaultdict(list)

    def respond(self, *patterns):
        def decorator(func):
            self.registry[func].extend(list(patterns))

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

    def noop(self, text):
        return JsonResponse({
            'text': 'Sorry, don\'t know what to do.'
        })


dispatcher = Dispatcher(settings.SLACK_TOKEN)
