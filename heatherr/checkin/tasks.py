import pkg_resources

from django.utils import timezone

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
    user_channel_id = checkin.get_user_channel_id()
    slackaccount = checkin.slackaccount
    response = slackaccount.api_call(
        'files.upload',
        channels=user_channel_id,
        initial_comment=(
            "Hey! Gentle reminder to send your %s update to let your <#%s|%s> "
            "team know what been busy with. Here's a template to help you "
            "get started. Type `/checkin remove %s` if you want me to stop "
            "sending this reminders. Type `/checkin list` to see all checkins"
            " set.") % (
                checkin.interval,
                checkin.channel_id,
                checkin.channel_name,
                checkin.pk),
        filetype='post',
        title='%s check-in' % (checkin.get_interval_display(),),
        content=pkg_resources.resource_string(
            'heatherr.checkin',
            'templates/checkin-%s-template.txt' % (checkin.interval,))
    )
    checkin.last_checkin = timezone.now()
    return response
