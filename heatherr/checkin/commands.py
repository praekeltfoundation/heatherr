from __future__ import absolute_import

from heatherr.checkin.models import Checkin
from heatherr.models import SlackAccount
from heatherr.views import dispatcher


checkin = dispatcher.command('/checkin')


@checkin.respond(r'^(?P<interval>daily|weekly)$')
def daily_or_weekly(request, match):
    """
    `/checkin daily`

    Sets a daily checkin for you for the current channel at 9am in
    according to the timezone your Slack account profile.
    """
    slackaccount = SlackAccount.objects.get(
        team_id=request.POST['team_id'])
    channel_id = request.POST['channel_id']
    channel_name = request.POST['channel_name']
    user_id = request.POST['user_id']
    (interval,) = match.groups()
    checkin, created = Checkin.objects.get_or_create(
        slackaccount=slackaccount,
        channel_id=channel_id,
        user_id=user_id,
        interval=interval)
    checkin.channel_name = channel_name
    checkin.save()
    return 'I\'ll prompt you %s for a <#%s|%s> team check-in' % (
        interval, channel_id, channel_name)


@checkin.respond(r'^list$')
def list_checkins(request, match):
    """
    `/checkin list`

    List all of the checkins you're subscribed to.
    """
    slackaccount = SlackAccount.objects.get(
        team_id=request.POST['team_id'])
    user_id = request.POST['user_id']
    checkins = Checkin.objects.filter(
        slackaccount=slackaccount, user_id=user_id)
    if not checkins.count():
        return 'You have no checkins set.'

    lines = ['You have the following checkins set:']
    lines.extend(['- #%s, a %s checkin for <#%s|%s>' % (
                  checkin.pk, checkin.interval,
                  checkin.channel_id, checkin.channel_name)
                  for checkin in checkins])
    return '\n'.join(lines)


@checkin.respond(r'^remove #?(?P<pk>\d+)$')
def remove_checking(request, match):
    """
    `/checkin remove #<number>`

    Remove a checkin, the #number matches the #number returned by
    list
    """
    slackaccount = SlackAccount.objects.get(
        team_id=request.POST['team_id'])
    user_id = request.POST['user_id']
    (pk,) = match.groups()
    try:
        checkin = Checkin.objects.get(
            slackaccount=slackaccount, user_id=user_id, pk=pk)
        checkin.delete()
        return 'Daily for <#%s|%s> was removed.' % (
            checkin.channel_id, checkin.channel_name)
    except Checkin.DoesNotExist:
        return 'Sorry, that reminder doesn\'t exist'
