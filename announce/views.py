import logging

logger = logging.getLogger('bellman.views')

from django.http import HttpResponse, HttpResponseBadRequest  # JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from bellman import Bellman
# Create your views here.


def require_slack_token(slack_token):
    def decorator(func):
        @csrf_exempt
        def handler(request, *args, **kwargs):
            if slack_token == request.POST.get('token'):
                return func(request, *args, **kwargs)
            return HttpResponseBadRequest('Invalid or missing slack token.')
        return handler
    return decorator


@require_slack_token(settings.SLACK_TOKEN)
def announce(request):
    logger.debug('POST from Slack')
    logger.debug(request.POST)
    app = Bellman(
        text=request.POST['text'],
        user_name=request.POST['user_name'],
        user_id=request.POST['user_id'])
    app.execute()
    return HttpResponse(app.get_response())
