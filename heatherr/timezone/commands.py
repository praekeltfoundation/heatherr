from __future__ import absolute_import

from django.http import JsonResponse


from heatherr.models import SlackAccount
from heatherr.views import dispatcher
import arrow


timezone = dispatcher.command('/time')


@timezone.respond(r'^for @?(?P<name>.+)$')
def for_(request, match):
    """
    `for <friend's name>`

    Print the local timezone and time for a friend on Slack.
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
    localtime = (utc.to(member['tz']) + utc.dst())
    text = '<@%s> is in %s, local time is %s' % (
        member['id'], member['tz_label'], localtime.format('h:mm A'))
    return JsonResponse({
        'response_type': 'in_channel',
        'text': text,
    })
