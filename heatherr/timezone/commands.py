from __future__ import absolute_import

from django.http import JsonResponse


from heatherr.models import SlackAccount
from heatherr.views import dispatcher
import arrow


time = dispatcher.command('/time')


@time.respond(r'^for @?(?P<name>.+)$')
def for_(request, match):
    """
    Print the local timezone and time for a friend on Slack::

        /time for @smn

        @smn is in Central European Time, local time is 5:29 PM

    The timezone is retrieved from the person's Slack account profile.
    If it's incorrect then have it updated there.
    """
    slackaccount = SlackAccount.objects.get(
        team_id=request.POST['team_id'])
    response = slackaccount.api_call('users.list', presence=1)
    (name,) = match.groups()
    found_members = filter(
        lambda member: member['name'] == name, response['members'])
    if not found_members:
        return 'I don\'t know %s' % (name,)
    [member] = found_members
    utc = arrow.utcnow()
    if not member['tz']:
        return ('I can\'t tell because <@%s>\'s Slack profile has no '
                'timezone set.') % (member['id'],)
    localtime = (utc.to(member['tz']) + utc.dst())
    text = '<@%s> is in %s, local time is %s' % (
        member['id'], member['tz_label'], localtime.format('h:mm A'))
    return JsonResponse({
        'text': text,
    })
