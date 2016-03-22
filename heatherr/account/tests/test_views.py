import responses

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import override_settings

from heatherr.models import SlackAccount
from heatherr.tests.base import HeatherrTestCase


class TestAccountViews(HeatherrTestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            'username', 'user@examle.org', 'password')

    def test_login_view(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertContains(response, 'Login with Google')

    def test_logout_view(self):
        self.client.login(username='username', password='password')
        self.assertEqual(
            self.client.get(reverse('accounts:profile')).status_code,
            200)
        self.assertRedirects(
            self.client.get(reverse('accounts:logout')),
            reverse('accounts:login'))

    def test_profile(self):
        self.client.login(username='username', password='password')
        self.get_slack_account()
        response = self.client.get(reverse('accounts:profile'))
        self.assertTemplateUsed(response, 'account/profile.html')

    def test_authorize_fail(self):
        self.client.login(username='username', password='password')
        session = self.client.session
        session['authorize_state'] = 'foo'
        session.save()

        response = self.client.get('%s?state=bar' % (
            reverse('accounts:authorize'),))
        self.assertContains(response, 'Invalid state token')

    @responses.activate
    @override_settings(SLACK_CLIENT_ID='slack-client-id',
                       SLACK_CLIENT_SECRET='slack-client-secret')
    def test_authorize(self):
        responses.add(
            responses.POST, 'https://slack.com/api/oauth.access',
            json={
                'team_id': 'the-team-id',
                'access_token': 'the-access-token',
                'scope': 'the-scope',
                'team_name': 'the-team-name',
                'incoming_webhook': {
                    'url': 'http://incoming-webhook-url/',
                    'channel': 'incoming-webhook-channel',
                    'configuration_url': 'incoming-webhook-configuration-url',
                },
                'bot': {
                    'bot_user_id': 'bot-user-id',
                    'bot_access_token': 'bot-access-token',
                }
            })

        self.client.login(username='username', password='password')
        session = self.client.session
        session['authorize_state'] = 'authorize_state'
        session['authorize_request_uri'] = 'http://testserver/'
        session.save()

        self.assertFalse(self.user.slackaccount_set.exists())
        response = self.client.get('%s?state=authorize_state&code=code' % (
            reverse('accounts:authorize'),))
        self.assertRedirects(response, reverse('accounts:profile'))
        [slackaccount] = self.user.slackaccount_set.all()
        self.assertEqual(slackaccount.access_token, 'the-access-token')
        self.assertEqual(slackaccount.bot_user_id, 'bot-user-id')
        self.assertEqual(slackaccount.bot_access_token, 'bot-access-token')

    def test_account_view(self):
        self.client.login(username='username', password='password')
        slackaccount = self.get_slack_account()
        response = self.client.get(reverse('accounts:slack-update', kwargs={
            'pk': slackaccount.pk,
        }))
        self.assertTemplateUsed(response, 'heatherr/slackaccount_form.html')

    @responses.activate
    def test_bot_status_connect(self):
        responses.add(
            responses.POST, '%s%s' % (settings.HEATHERRD_URL, 'connect'),
            json={})

        self.client.login(username='username', password='password')
        slackaccount = self.get_slack_account()
        self.assertEqual(slackaccount.bot_enabled, False)
        with override_settings(CELERY_ALWAYS_EAGER=True):
            self.client.post(
                reverse('accounts:slack-update',
                        kwargs={'pk': slackaccount.pk}),
                data={'bot_enabled': True})

        reloaded = SlackAccount.objects.get(pk=slackaccount.pk)
        self.assertEqual(reloaded.bot_enabled, True)
        self.assertEqual(reloaded.bot_status, SlackAccount.CONNECTING)

    @responses.activate
    def test_bot_status_connect_fail(self):
        responses.add(
            responses.POST, '%s%s' % (settings.HEATHERRD_URL, 'connect'),
            json={}, status=404)

        self.client.login(username='username', password='password')
        slackaccount = self.get_slack_account()
        slackaccount.bot_error_count = settings.BOT_MAX_ERROR_COUNT
        slackaccount.save()

        with override_settings(CELERY_ALWAYS_EAGER=True):
            print self.client.post(
                reverse('accounts:slack-update',
                        kwargs={'pk': slackaccount.pk}),
                data={'bot_enabled': True})

        reloaded = SlackAccount.objects.get(pk=slackaccount.pk)
        self.assertEqual(reloaded.bot_enabled, False)
        self.assertEqual(reloaded.bot_status, SlackAccount.ERROR)

    @responses.activate
    def test_bot_status_disconnect(self):
        responses.add(
            responses.POST, '%s%s' % (settings.HEATHERRD_URL, 'disconnect'),
            json={})

        self.client.login(username='username', password='password')
        slackaccount = self.get_slack_account()
        slackaccount.bot_enabled = True
        slackaccount.save()

        with override_settings(CELERY_ALWAYS_EAGER=True):
            self.client.post(
                reverse('accounts:slack-update',
                        kwargs={'pk': slackaccount.pk}),
                data={'bot_enabled': False})

        reloaded = SlackAccount.objects.get(pk=slackaccount.pk)
        self.assertEqual(reloaded.bot_enabled, False)
        self.assertEqual(reloaded.bot_status, SlackAccount.OFFLINE)
