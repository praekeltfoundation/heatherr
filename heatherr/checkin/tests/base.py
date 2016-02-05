from heatherr.tests import HeatherrTestCase

from heatherr.checkin.models import Checkin


class CheckinTestCase(HeatherrTestCase):

    def mk_checkin(self, slackaccount=None, interval=Checkin.DAILY,
                   last_checkin=None, user_id='user-id'):
        slackaccount = slackaccount or self.get_slack_account()
        return Checkin.objects.create(
            slackaccount=slackaccount,
            channel_id='channel-id',
            user_id=user_id,
            interval=interval,
            last_checkin=last_checkin)