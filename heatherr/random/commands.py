from __future__ import absolute_import

import re

from heatherr.views import dispatcher
from heatherr.models import SlackAccount
from heatherr.random.tasks import post_poll


slap = dispatcher.command('/slap')


@slap.respond(r'^@(?P<target>[A-Za-z\-\.0-9]+)$')
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

poll = dispatcher.command('/poll')


@poll.respond(r'^(?P<question>.+)\? (?P<options>.+)$')
def poll(request, match):
    """
    `/poll Should we jump off a bridge? Yes, No, Maybe?`

    Create a poll
    """
    team_id = request.POST['team_id']
    user_id = request.POST['user_id']
    channel_id = request.POST['channel_id']
    (question, option_str) = match.groups()
    options = re.split(r',\s*|\sor\s+', option_str)[:10]

    post_poll.delay(team_id, user_id, channel_id, question, options)
