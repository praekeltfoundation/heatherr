import responses

from heatherr.tests import CommandTestCase
from heatherr.checkin.models import Checkin


class CheckinTest(CommandTestCase):

    def setUp(self):
        self.slackaccount = self.get_slack_account()

    def test_check_daily(self):
        checkins = Checkin.objects.filter(slackaccount=self.slackaccount)
        self.assertEqual(checkins.count(), 0)
        response = self.send_command('/checkin daily')
        self.assertEqual(response.json(), {
            'in_channel': True,
            'text': (
                'I\'ll prompt you daily for a #channel_name team check-in'),
        })
        [checkin] = checkins
        self.assertEqual(checkin.interval, Checkin.DAILY)
        self.assertEqual(checkin.user_id, self.default_user_id)
        self.assertEqual(checkin.channel_id, self.default_channel_id)
        self.assertEqual(checkin.last_checkin, None)

    def test_check_weekly(self):
        response = self.send_command('/checkin weekly')
        self.assertEqual(response.json(), {
            'in_channel': True,
            'text': (
                'I\'ll prompt you weekly for a #channel_name team check-in'),
        })
        [checkin] = Checkin.objects.filter(slackaccount=self.slackaccount)
        self.assertEqual(checkin.interval, Checkin.WEEKLY)
        self.assertEqual(checkin.user_id, self.default_user_id)
        self.assertEqual(checkin.channel_id, self.default_channel_id)
        self.assertEqual(checkin.last_checkin, None)
