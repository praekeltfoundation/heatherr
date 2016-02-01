from django.db import models


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
