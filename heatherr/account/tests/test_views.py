import responses

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings

from heatherr.models import SlackAccount


class TestAccountViews(TestCase):

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

    def test_new_profile(self):
        self.client.login(username='username', password='password')
        response = self.client.get(reverse('accounts:profile'))
        self.assertTemplateUsed(response, 'account/new_profile.html')

    def test_existing_profile(self):
        self.client.login(username='username', password='password')
        SlackAccount.objects.create(user=self.user)
        response = self.client.get(reverse('accounts:profile'))
        self.assertTemplateUsed(response, 'account/profile.html')

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
