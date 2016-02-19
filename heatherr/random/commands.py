from __future__ import absolute_import

import re

from heatherr.views import dispatcher
from heatherr.models import SlackAccount


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
    slackaccount = SlackAccount.objects.get(
        team_id=request.POST['team_id'])
    user_id = request.POST['user_id']
    channel_id = request.POST['channel_id']
    (question, option_str) = match.groups()
    options = re.split(r',\s*|\sor\s+', option_str)[:10]

    emoji_map = [
        'one',
        'two',
        'three',
        'four',
        'five',
        'six',
        'seven',
        'eight',
        'nine',
        'keycap_ten',
    ]

    post = ['Poll from <@%s>:' % (user_id,)]
    post.append('%s?' % (question,))
    post.extend([':%s: %s' % (emoji_map[idx], option)
                 for (idx, option) in enumerate(options)])
    print '\n'.join(post)

    resp = slackaccount.api_call(
        'chat.postMessage',
        text='\n'.join(post),
        channel=channel_id,
        as_user=True,
    )

    for idx, option in enumerate(options):
        slackaccount.api_call(
            'reactions.add',
            name=emoji_map[idx],
            channel=channel_id,
            timestamp=str(resp['ts']),)
