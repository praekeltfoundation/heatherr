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
                'I\'ll prompt you daily for a <#channel_id|channel_name>'
                ' team check-in'),
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
                'I\'ll prompt you weekly for a <#channel_id|channel_name> '
                'team check-in'),
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
            ("Cool, I've removed your weekly reminders for "
             "<#channel_id|channel_name>"))
        self.assertEqual(checkins.count(), 0)

    def test_checkin_list(self):
        self.mk_checkin(interval=Checkin.WEEKLY,
                        channel_id='channel-1',
                        channel_name='channel-name-1')
        self.mk_checkin(interval=Checkin.DAILY,
                        channel_id='channel-2',
                        channel_name='channel-name-2')
        self.assertCommandResponse(
            '/checkin list',
            '\n'.join([
                'You have the following checkins set:',
                '- #1, a weekly checkin for <#channel-1|channel-name-1>',
                '- #2, a daily checkin for <#channel-2|channel-name-2>',
            ]))

    def test_remove(self):
        self.mk_checkin(interval=Checkin.WEEKLY,
                        channel_id='channel-1',
                        channel_name='channel-name-1')
        self.mk_checkin(interval=Checkin.DAILY,
                        channel_id='channel-2',
                        channel_name='channel-name-2')
        checkins = Checkin.objects.filter(slackaccount=self.slackaccount)
        self.assertEqual(checkins.count(), 2)
        self.assertCommandResponse(
            '/checkin remove 1',
            'Daily for <#%s|%s> was removed.' % (
                'channel-1', 'channel-name-1'))
        checkins = Checkin.objects.filter(slackaccount=self.slackaccount)
        self.assertEqual(checkins.count(), 1)

    def test_checkin_stop_non_existent(self):
        self.assertCommandResponse(
            '/checkin remove 1',
            "Sorry, that reminder doesn't exist")
