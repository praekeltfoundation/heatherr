from __future__ import absolute_import

from heatherr.views import dispatcher
from heatherr.models import SlackAccount


slap = dispatcher.command('/slap')


@slap.respond(r'^@?(?P<target>[A-Za-z\-\.0-9]+)$')
def slap(request, match):
    """
    `/slap @userid`

    Slaps the @userid
    """
    slackaccount = SlackAccount.objects.get(
        team_id=request.POST['team_id'])
    user_id = request.POST['user_id']
    channel_id = request.POST['channel_id']
    (target,) = match.groups()
    slackaccount.api_call(
        'chat.postMessage',
        text='<@%s> slaps <@%s> around a bit with a large trout.' % (
            user_id, target),
        as_user=True,
        channel=channel_id,)
