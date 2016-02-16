from datetime import timedelta

from heatherr import celery_app
from heatherr.models import SlackAccount

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

import requests


@celery_app.task(ignore_result=True)
def connect_bot(slackaccount_pk):
    slackaccount = SlackAccount.objects.get(pk=slackaccount_pk)
    response = requests.post(
        '%s%s' % (settings.HEATHERRD_URL, 'connect'),
        auth=(slackaccount.bot_user_id, slackaccount.bot_access_token))
    try:
        response.raise_for_status()
        slackaccount.bot_enabled = True
        slackaccount.bot_status = SlackAccount.CONNECTING
    except requests.exceptions.HTTPError:
        slackaccount.bot_enabled = False
        slackaccount.bot_status = SlackAccount.ERROR

    slackaccount.save()


@celery_app.task(ignore_result=True)
def disconnect_bot(slackaccount_pk):
    slackaccount = SlackAccount.objects.get(pk=slackaccount_pk)
    response = requests.post(
        '%s%s' % (settings.HEATHERRD_URL, 'disconnect'),
        auth=(slackaccount.bot_user_id, slackaccount.bot_access_token))

    response.raise_for_status()
    slackaccount.bot_enabled = False
    slackaccount.bot_status = SlackAccount.OFFLINE
    slackaccount.save()


@celery_app.task(ignore_result=True)
def ensure_bots_connected(minutes=1):
    enabled = SlackAccount.objects.filter(bot_enabled=True)
    slackaccounts = enabled.filter(
        Q(bot_checkin__isnull=True) |
        Q(bot_checkin__lte=(timezone.now() - timedelta(minutes=minutes))))

    for slackaccount in slackaccounts:
        connect_bot(slackaccount.pk)
