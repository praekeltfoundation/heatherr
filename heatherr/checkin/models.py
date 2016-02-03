from datetime import timedelta

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

    def required(self, current_time=None, target_hour=9, users={}):
        current_time = arrow.get(current_time or arrow.utcnow())

        days = {
            Checkin.DAILY: 1,
            Checkin.WEEKLY: 7,
        }[self.interval]

        user_info = users.get(self.user_id) or self.get_user_info()
        yesterday = current_time - timedelta(days=1)
        local_time = current_time.to(user_info['tz'])

        if local_time.hour != target_hour:
            return False

        if self.last_checkin is None:
            return True

        return (self.last_checkin - yesterday).days <= -days
