from heatherr.checkin.tests.base import CheckinTestCase
from heatherr.tests.base import CommandTestCase
from heatherr.checkin.models import Checkin


class CheckinTest(CheckinTestCase, CommandTestCase):

    def setUp(self):
        self.slackaccount = self.get_slack_account()

    def test_check_daily(self):
        checkins = Checkin.objects.filter(slackaccount=self.slackaccount)
        self.assertEqual(checkins.count(), 0)
        response = self.send_command('/checkin daily')
        self.assertEqual(response.json(), {
            'text': (
                'I\'ll prompt you daily for a <#channel_id> team check-in'),
        })
        [checkin] = checkins
        self.assertEqual(checkin.interval, Checkin.DAILY)
        self.assertEqual(checkin.user_id, self.default_user_id)
        self.assertEqual(checkin.channel_id, self.default_channel_id)
        self.assertEqual(checkin.last_checkin, None)

    def test_check_weekly(self):
        response = self.send_command('/checkin weekly')
        self.assertEqual(response.json(), {
            'text': (
                'I\'ll prompt you weekly for a <#channel_id> team check-in'),
        })
        [checkin] = Checkin.objects.filter(slackaccount=self.slackaccount)
        self.assertEqual(checkin.interval, Checkin.WEEKLY)
        self.assertEqual(checkin.user_id, self.default_user_id)
        self.assertEqual(checkin.channel_id, self.default_channel_id)
        self.assertEqual(checkin.last_checkin, None)

    def test_checkin_stop(self):
        self.mk_checkin(interval=Checkin.WEEKLY)
        checkins = Checkin.objects.filter(slackaccount=self.slackaccount)
        self.assertEqual(checkins.count(), 1)
        self.assertCommandResponse(
            '/checkin stop weekly',
            "Cool, I've removed your weekly reminders for <#channel_id>")
        self.assertEqual(checkins.count(), 0)

    def test_checkin_stop_non_existent(self):
        self.assertCommandResponse(
            '/checkin stop weekly',
            ("Sorry, I don't have any weekly check-ins to remove for "
             "you in <#channel_id>"))
