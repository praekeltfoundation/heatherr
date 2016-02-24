from django.db import models


class Acronym(models.Model):
    slackaccount = models.ForeignKey('heatherr.SlackAccount')
    acronym = models.CharField(blank=True, max_length=100)
    definition = models.TextField(blank=True)

    def __unicode__(self):
        return self.acronym
