from functools import wraps

from django.conf import settings
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt


def slack_command(func):
    @csrf_exempt
    @wraps(func)
    def handler(request, *args, **kwargs):
        if settings.SLACK_TOKEN != request.POST.get('token'):
            return HttpResponseBadRequest('Invalid or missing slack token.')
        return func(request, *args, **kwargs)
    return handler


def require_slack_token(slack_token):
    def decorator(func):
        @csrf_exempt
        @wraps(func)
        def handler(request, *args, **kwargs):
            if slack_token == request.POST.get('token'):
                return func(request, *args, **kwargs)
            return HttpResponseBadRequest('Invalid or missing slack token.')
        return handler
    return decorator
