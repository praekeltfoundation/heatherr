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
        '%s%s' % (settings.HEATHERR_RELAY, 'connect'),
        auth=(slackaccount.bot_user_id, slackaccount.bot_access_token))
    try:
        response.raise_for_status()
        slackaccount.bot_enabled = True
        slackaccount.bot_status = 'connecting'
    except requests.exception.HTTPError:
        slackaccount.bot_enabled = False
        slackaccount.bot_status = 'error'

    slackaccount.save()


@celery_app.task(ignore_result=True)
def disconnect_bot(slackaccount_pk):
    slackaccount = SlackAccount.objects.get(pk=slackaccount_pk)
    response = requests.post(
        '%s%s' % (settings.HEATHERR_RELAY, 'disconnect'),
        auth=(slackaccount.bot_user_id, slackaccount.bot_access_token))

    response.raise_for_status()
    slackaccount.bot_enabled = False
    slackaccount.bot_status = 'offline'
    slackaccount.save()


@celery_app.task(ignore_result=True)
def ensure_bots_connected():
    enabled = SlackAccount.objects.filter(bot_enabled=True)
    slackaccounts = enabled.filter(
        Q(bot_checkin__isnull=True) | Q(bot_checkin__lte=timezone.now()))

    for slackaccount in slackaccounts:
        connect_bot(slackaccount.pk)
