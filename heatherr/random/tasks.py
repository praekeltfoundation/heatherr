from heatherr import celery_app
from heatherr.models import SlackAccount


@celery_app.task(ignore_result=True)
def post_poll(team_id, user_id, channel_id, question, options):
    slackaccount = SlackAccount.objects.get(team_id=team_id)

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
