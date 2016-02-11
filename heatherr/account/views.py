from uuid import uuid4

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.views.generic.edit import UpdateView

from heatherr.models import SlackAccount
from heatherr.tasks import connect_bot, disconnect_bot

import requests


def login_view(request):
    return render(request, "account/login.html")


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out. See you again soon!')
    return redirect(reverse('accounts:login'))


@login_required
def profile(request):
    request.session['authorize_state'] = uuid4().hex
    request.session['authorize_request_uri'] = '%s://%s%s' % (
        ('https' if request.is_secure() else 'http'),
        get_current_site(request).domain,
        reverse('accounts:authorize'))

    return render(request, "account/profile.html", {
        'SLACK_CLIENT_ID': settings.SLACK_CLIENT_ID,
        'SLACK_SCOPES': settings.SLACK_SCOPES,
        'user': request.user,
    })


@login_required
def authorize(request):
    if request.session['authorize_state'] != request.GET['state']:
        return render(request, "account/authorize_fail.html", {
            "error": "Invalid state token.",
        })

    response = requests.post('https://slack.com/api/oauth.access', data={
        'client_id': settings.SLACK_CLIENT_ID,
        'client_secret': settings.SLACK_CLIENT_SECRET,
        'code': request.GET['code'],
        'redirect_uri': request.session['authorize_request_uri'],
    })
    data = response.json()

    account, created = SlackAccount.objects.update_or_create(
        user=request.user, team_id=data['team_id'], defaults={
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

    messages.success(request, "Heatherr is now linked to %s." % (
        account.team_name,))
    return redirect(reverse('accounts:profile'))


class SlackAccountUpdateView(UpdateView):
    model = SlackAccount
    fields = ['bot_enabled']

    def get_context_data(self, **kwargs):
        context = super(
            SlackAccountUpdateView, self).get_context_data(**kwargs)
        context['SLACK_CLIENT_ID'] = settings.SLACK_CLIENT_ID
        context['SLACK_SCOPES'] = settings.SLACK_SCOPES
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Successfully updated.')
        if form.cleaned_data['bot_enabled']:
            connect_bot.delay(self.object.pk)
        else:
            disconnect_bot.delay(self.object.pk)
        return super(SlackAccountUpdateView, self).form_valid(form)
