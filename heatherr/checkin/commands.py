from __future__ import absolute_import

from django.http import JsonResponse

from heatherr.checkin.models import Checkin
from heatherr.models import SlackAccount
from heatherr.views import dispatcher


checkin = dispatcher.command('/checkin')


@checkin.respond(r'^(?P<interval>daily|weekly)$')
def daily_or_weekly(request, match):
    slackaccount = SlackAccount.objects.get(
        team_id=request.POST['team_id'])
    channel_id = request.POST['channel_id']
    channel_name = request.POST['channel_name']
    user_id = request.POST['user_id']
    (interval,) = match.groups()
    Checkin.objects.create(
        slackaccount=slackaccount,
        channel_id=channel_id,
        user_id=user_id,
        interval=interval)
    return JsonResponse({
        'in_channel': True,
        'text': 'I\'ll prompt you %s for a #%s team check-in' % (
            interval, channel_name),
    })
