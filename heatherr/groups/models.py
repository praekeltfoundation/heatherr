from django.db import models


class Group(models.Model):
    group_name = models.CharField(max_length=200)
    slackaccount = models.ForeignKey('heatherr.SlackAccount')

    def __unicode__(self):
        return self.group_name


class Person(models.Model):
    slackaccount = models.ForeignKey('heatherr.SlackAccount')
    person_id = models.CharField(max_length=200)
    person_name = models.CharField(max_length=200)
    groups = models.ManyToManyField(Group)

    def __unicode__(self):
        return self.person_name
