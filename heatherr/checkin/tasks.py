from heatherr import celery_app
from heatherr.models import SlackAccount


@celery_app.task(ignore_result=True)
def check_all_checkins():
    slackaccounts = SlackAccount.objects.all()
    for slackaccount in slackaccounts:
        check_slackaccount_checkins(slackaccount)


def check_slackaccount_checkins(slackaccount):
    users = slackaccount.get_users()
    requireds = [checkin
                 for checkin in slackaccount.checkin_set.all()
                 if checkin.required(users=users)]
    for checkin in requireds:
        check_checkin(checkin)


def check_checkin(checkin):
    token = checkin.slackaccount.bot_access_token
    user_channel_id = get_user_channel_id()

    requests.post('%s%s' % (settings.HEATHER_RELAY, 'rtm'),
                  headers={'X-Bot-Access-Token': token},
                  data={
                      "type": "message",
                      "channel": user_channel_id,
                      "text": "Hi there!"
                  })
