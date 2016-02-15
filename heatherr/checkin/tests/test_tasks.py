import json
import pkg_resources

from urllib import unquote_plus, unquote

from heatherr.checkin.models import Checkin
from heatherr.checkin.tests.base import CheckinTestCase
from heatherr.checkin import tasks

from freezegun import freeze_time

import responses

from mock import patch


class TasksTest(CheckinTestCase):

    @responses.activate
    def test_slackaccount_checkins(self):
        slackaccount = self.get_slack_account()
        checkin1 = self.mk_checkin(
            slackaccount=slackaccount, user_id='user-1',
            interval=Checkin.DAILY)
        checkin2 = self.mk_checkin(
            slackaccount=slackaccount, user_id='user-2',
            interval=Checkin.DAILY)

        self.mock_api_call('users.list', {
            'ok': True,
            'members': [{
                'id': checkin1.user_id,
                'tz': 'Europe/Amsterdam',
            }, {
                'id': checkin2.user_id,
                'tz': 'Africa/Johannesburg',
            }],
        })

        # NOTE: we're creating two checkins, but only 1 should be called for
        #       the time given, Amsterdam at 9AM at 8AM UTC during DST.
        with patch.object(tasks, 'check_checkin') as patched_checkin:
            with freeze_time('2016-02-03 08:00:00'):
                tasks.check_all_checkins()
            patched_checkin.assert_called_with(checkin1)

    @responses.activate
    def test_checkin(self):

        responses.add(
            responses.POST, 'https://slack.com/api/files.upload',
            content_type='application/json',
            body=json.dumps({}))

        slackaccount = self.get_slack_account()
        checkin = self.mk_checkin(
            slackaccount=slackaccount, user_id='user-1',
            interval=Checkin.DAILY,
            user_channel_id='the-user-channel-id')
        tasks.check_checkin(checkin)
        [call] = responses.calls
        self.assertEqual(
            call.request.url, 'https://slack.com/api/files.upload')

        args = unquote(unquote_plus(call.request.body))
        self.assertTrue(
            pkg_resources.resource_string(
                'heatherr.checkin', 'templates/checkin-daily-template.txt')
            in args)
        self.assertTrue('channels=%s' % (checkin.user_channel_id,) in args)
        self.assertTrue('/checkin stop daily' in args)
