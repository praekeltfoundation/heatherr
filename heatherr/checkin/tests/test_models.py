from heatherr.checkin.models import Checkin
from heatherr.checkin.tests.base import CheckinTestCase


from django.utils import timezone

import arrow
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

    @responses.activate
    def test_get_user_info(self):
        checkin = self.mk_checkin()
        self.assertEqual(checkin.get_user_info(), {
            'tz': 'Africa/Johannesburg'
        })

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
        checkin = self.mk_checkin(interval=Checkin.WEEKLY)
        with freeze_time('2016-02-03 06:00:00'):
            self.assertFalse(checkin.required())

        with freeze_time('2016-02-03 06:00:00'):
            self.assertTrue(checkin.required(target_hour=8))

    @responses.activate
    def test_require_with_previous_run(self):
        weekly_checkin = self.mk_checkin(
            interval=Checkin.WEEKLY,
            last_checkin=timezone.now())
        daily_checkin = self.mk_checkin(
            interval=Checkin.DAILY,
            last_checkin=timezone.now())
        with freeze_time('2016-02-03 06:00:00'):
            self.assertFalse(weekly_checkin.required(target_hour=8))
            self.assertTrue(daily_checkin.required(target_hour=8))

    def test_required_with_users(self):
        checkin = self.mk_checkin(interval=Checkin.DAILY,
                                  last_checkin=timezone.now())
        with freeze_time('2016-02-03 06:00:00'):
            self.assertTrue(
                checkin.required(target_hour=7, users={
                    checkin.user_id: {
                        'tz': 'Europe/Amsterdam',
                    }
                }))
