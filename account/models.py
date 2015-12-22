from django.db import models


class SlackAccount(models.Model):
    user = models.ForeignKey('auth.user', null=True)
    access_token = models.CharField(max_length=255)
    scope = models.CharField(max_length=255)
    team_name = models.CharField(max_length=255)
    team_id = models.CharField(max_length=255)
    incoming_webhook_url = models.CharField(max_length=255)
    incoming_webhook_channel = models.CharField(max_length=255)
    incoming_webhook_configuration_url = models.CharField(max_length=255)
    bot_user_id = models.CharField(max_length=255)
    bot_access_token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s (%s)' % (self.team_name, self.team_id)
