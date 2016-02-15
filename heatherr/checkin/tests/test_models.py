from heatherr.checkin.models import Checkin
from heatherr.checkin.tests.base import CheckinTestCase


from django.utils import timezone

import responses

from freezegun import freeze_time


class CheckinModelTest(CheckinTestCase):

    def setUp(self):
        self.mock_api_call('users.info', {
            'ok': True,
            'user': {
                'tz': 'Africa/Johannesburg',
            }
        })
        self.mock_api_call('im.open', {
            'channel': {
                'id': 'channel-id'
            }
        })

    @responses.activate
    def test_get_user_info(self):
        checkin = self.mk_checkin()
        self.assertEqual(checkin.get_user_info(), {
            'tz': 'Africa/Johannesburg'
        })

    @responses.activate
    def test_get_user_channel_id(self):
        checkin = self.mk_checkin(user_channel_id=None)
        self.assertEqual(checkin.user_channel_id, None)
        self.assertEqual(checkin.get_user_channel_id(), 'channel-id')
        self.assertEqual(
            Checkin.objects.get(pk=checkin.pk).user_channel_id,
            'channel-id')
        self.assertEqual(
            Checkin.objects.get(pk=checkin.pk).get_user_channel_id(),
            'channel-id')

    @responses.activate
    def test_require_daily_first_time(self):
        with freeze_time('2016-02-03 06:00:00'):
            checkin = self.mk_checkin(interval=Checkin.DAILY)
            self.assertFalse(checkin.required())

        with freeze_time('2016-02-03 06:00:00'):
            checkin = self.mk_checkin(interval=Checkin.DAILY)
            self.assertTrue(checkin.required(target_hour=8))

    @responses.activate
    def test_require_weekly_first_time(self):
        with freeze_time('2016-02-03 06:00:00'):
            checkin = self.mk_checkin(interval=Checkin.WEEKLY)
            self.assertFalse(checkin.required())

        with freeze_time('2016-02-03 06:00:00'):
            checkin = self.mk_checkin(interval=Checkin.WEEKLY)
            self.assertTrue(checkin.required(target_hour=8))

    @responses.activate
    def test_require_with_previous_run(self):
        with freeze_time('2016-02-03 06:00:00'):
            weekly_checkin = self.mk_checkin(
                interval=Checkin.WEEKLY,
                last_checkin=timezone.now())
            daily_checkin = self.mk_checkin(
                interval=Checkin.DAILY,
                last_checkin=timezone.now())
            self.assertFalse(weekly_checkin.required(target_hour=8))
            self.assertTrue(daily_checkin.required(target_hour=8))

    def test_required_with_users(self):
        with freeze_time('2016-02-03 06:00:00'):
            checkin = self.mk_checkin(interval=Checkin.DAILY,
                                      last_checkin=timezone.now())
            self.assertTrue(
                checkin.required(target_hour=7, users={
                    checkin.user_id: {
                        'tz': 'Europe/Amsterdam',
                    }
                }))
