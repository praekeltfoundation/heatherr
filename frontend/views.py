from uuid import uuid4

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.shortcuts import render

from account.models import Account

import requests


def index(request):
    request.session['authorize_state'] = uuid4().hex
    request.session['authorize_request_uri'] = '%s://%s%s' % (
        ('https' if request.is_secure() else 'http'),
        get_current_site(request).domain,
        reverse('frontend:authorize'))
    return render(request, "frontend/index.html")


def authorize(request):
    if request.session['authorize_state'] != request.GET['state']:
        return render(request, "frontend/authorize_fail.html", {
            "error": "Invalid state token.",
        })

    response = requests.post('https://slack.com/api/oauth.access', data={
        'client_id': settings.SLACK_CLIENT_ID,
        'client_secret': settings.SLACK_CLIENT_SECRET,
        'code': request.GET['code'],
        'redirect_uri': request.session['authorize_request_uri'],
    })
    data = response.json()

    from pprint import pprint
    pprint(data)

    account, created = Account.objects.update_or_create(
        team_id=data['team_id'], defaults={
            'access_token': data['access_token'],
            'scope': data['scope'],
            'team_name': data['team_name'],
            'incoming_webhook_url': data['incoming_webhook']['url'],
            'incoming_webhook_channel': data['incoming_webhook']['channel'],
            'incoming_webhook_configuration_url': (
                data['incoming_webhook']['configuration_url']),
            'bot_user_id': data['bot']['bot_user_id'],
            'bot_access_token': data['bot']['bot_access_token'],
        }
    )

    return render(request, "frontend/authorize.html", {
        'account': account,
        'created': created,
    })
