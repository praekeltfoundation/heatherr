from django.db import models

import arrow


class Checkin(models.Model):

    DAILY = 'daily'
    WEEKLY = 'weekly'

    slackaccount = models.ForeignKey('heatherr.SlackAccount')
    channel_id = models.CharField(blank=True, max_length=255)
    user_id = models.CharField(blank=True, max_length=255)
    interval = models.CharField(blank=True, max_length=255, choices=[
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
    ])
    last_checkin = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(blank=True, auto_now=True)

    def get_user_info(self):
        data = self.slackaccount.api_call('users.info', user=self.user_id)
        return data['user']

    def needs_checkin(self, interval, current_time=None):
        current_time = arrow.get(current_time or arrow.utcnow())

        days = {
            Checkin.DAILY: 1,
            Checkin.WEEKLY: 7,
        }[interval]

        yesterday = current_time - timedelta(days=1)
        local_time = current_time.to(user_info['tz'])
        return (
            ((self.last_checkin - yesterday).hours) > 24 and
            (8 < local_time.hour < 9))
