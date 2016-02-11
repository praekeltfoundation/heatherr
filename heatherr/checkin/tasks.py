from heatherr import celery_app
from heatherr.models import SlackAccount

from django.conf import settings

import requests


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
    pass
