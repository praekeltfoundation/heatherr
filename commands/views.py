from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from announce.commands import AnnounceCommand


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

    @csrf_exempt
    def view(self, request):
        if self.slack_token != request.POST.get('token'):
            return HttpResponseBadRequest('Invalid or missing slack token.')

        command = request.POST['command']
        handler = self.registry.get(command, NotFoundHandler())
        return handler.handle(request)


dispatcher = Dispatcher(settings.SLACK_TOKEN)
# NOTE: this is here for backwards compatbility
dispatcher.register('/bellman', AnnounceCommand())
dispatcher.register('/announce', AnnounceCommand())
