from __future__ import absolute_import

from heatherr.checkin.models import Checkin
from heatherr.models import SlackAccount
from heatherr.views import dispatcher


checkin = dispatcher.command('/checkin')


@checkin.respond(r'^(?P<interval>daily|weekly)$')
def daily_or_weekly(request, match):
    slackaccount = SlackAccount.objects.get(
        team_id=request.POST['team_id'])
    channel_id = request.POST['channel_id']
    user_id = request.POST['user_id']
    (interval,) = match.groups()
    Checkin.objects.create(
        slackaccount=slackaccount,
        channel_id=channel_id,
        user_id=user_id,
        interval=interval)
    return 'I\'ll prompt you %s for a <#%s> team check-in' % (
        interval, channel_id)


@checkin.respond(r'^stop (?P<interval>daily|weekly)$')
def stop_checkin(request, match):
    slackaccount = SlackAccount.objects.get(
        team_id=request.POST['team_id'])
    channel_id = request.POST['channel_id']
    user_id = request.POST['user_id']
    (interval,) = match.groups()
    checkins = Checkin.objects.filter(
        slackaccount=slackaccount,
        channel_id=channel_id,
        user_id=user_id,
        interval=interval)

    rows_deleted, _ = checkins.delete()
    if rows_deleted:
        return ('Cool, I\'ve removed your %s reminders for <#%s>') % (
            interval, channel_id)
    return ('Sorry, I don\'t have any %s check-ins'
            ' to remove for you in <#%s>') % (interval, channel_id)
