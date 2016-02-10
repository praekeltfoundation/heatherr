from datetime import timedelta

from django.db import models

import arrow


class Checkin(models.Model):

    DAILY = 'daily'
    WEEKLY = 'weekly'

    slackaccount = models.ForeignKey('heatherr.SlackAccount')
    channel_id = models.CharField(blank=True, max_length=255)
    user_id = models.CharField(blank=True, max_length=255)
    user_channel_id = models.CharField(blank=True, max_length=255, null=True)
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

    def get_user_channel_id(self):
        if self.user_channel_id:
            return self.user_channel_id

        response = requests.post(
            'https://slack.com/api/im.open',
            data = {
                'token': self.slackaccount.bot_access_token,
                'user': self.user_id,
            })

        data = response.json()
        channel_id = data['channel']['id']
        self.user_channel_id = channel_id
        self.save()

        return self.user_channel_id

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


class CheckinItem(models.Model):

    slackaccount = models.ForeignKey('heatherr.SlackAccount')
    user_id = models.CharField(blank=True, max_length=255)
    created_at = models.DateTimeField(blank=True, auto_now_add=True)
