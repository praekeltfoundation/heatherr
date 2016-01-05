from __future__ import absolute_import

from django.http import HttpResponse, JsonResponse

from announce.bellman import Bellman
from announce.models import Group, Person
from account.models import SlackAccount
from commands import dispatcher


bellman = dispatcher.command('/bellman')


@bellman.respond(r'.*')
def bellman(request, match):
    app = Bellman(
        text=request.POST['text'],
        user_name=request.POST['user_name'],
        user_id=request.POST['user_id'])
    app.execute()
    return HttpResponse(app.get_response())

announce = dispatcher.command('/announce')


@announce.respond(r'^list-groups$', r'^list$')
def list_groups(request, match):
    groups = Group.objects.filter(
        slackaccount__team_id=request.POST['team_id'])
    if not groups.exists():
        return JsonResponse({
            'text': 'No groups exist'
        })

    return 'Groups: %s' % (
        '\n'.join([unicode(group) for group in groups]),)


@announce.respond(r'^list-my-groups$')
def list_my_groups(request, match):
    person, _ = Person.objects.get_or_create(person_id=request.POST['user_id'])
    groups = person.groups.all()
    if not groups.exists():
        return "You don't seem to belong to any groups."
    return "Groups you belong to: %s" % (
        ', '.join([unicode(group) for group in groups]))


@announce.respond(r'^create\s+(?P<group_name>[\w-]+)$')
def create_groups(request, match):
    (group_name,) = match.groups()
    slackaccount = SlackAccount.objects.get(team_id=request.POST['team_id'])
    group, created = Group.objects.get_or_create(
        slackaccount=slackaccount,
        group_name=group_name)
    if created:
        return 'The group %s has been created.' % (group_name,)
    else:
        return 'The group %s already exists.' % (group_name,)


@announce.respond(r'^opt-in\s+(?P<group_name>[\w-]+)$')
def opt_in(request, match):
    (group_name,) = match.groups()
    slackaccount = SlackAccount.objects.get(team_id=request.POST['team_id'])
    person, _ = Person.objects.get_or_create(person_id=request.POST['user_id'])
    try:
        group = slackaccount.group_set.get(group_name=group_name)
        group.person_set.add(person)
        return "You've been added to %s." % (group_name,)
    except Group.DoesNotExist:
        return 'The group %s does not exist.' % (group_name,)


@announce.respond(r'^opt-out\s+(?P<group_name>[\w-]+)$')
def opt_out(request, match):
    (group_name,) = match.groups()
    slackaccount = SlackAccount.objects.get(team_id=request.POST['team_id'])
    person, _ = Person.objects.get_or_create(person_id=request.POST['user_id'])
    try:
        group = slackaccount.group_set.get(group_name=group_name)
        group.person_set.remove(person)
        return "You've been removed from %s." % (group_name,)
    except Group.DoesNotExist:
        return 'The group %s does not exist.' % (group_name,)


@announce.respond(r'^people-in-group\s+(?P<group_name>[\w-]+)$')
def people_in_group(request, match):
    (group_name,) = match.groups()
    slackaccount = SlackAccount.objects.get(team_id=request.POST['team_id'])
    try:
        group = slackaccount.group_set.get(group_name=group_name)
        if not group.person_set.exists():
            return 'There are no people in %s.' % (group_name,)

        return 'People in %s: %s' % (
            group_name,
            ', '.join(
                [person.person_name for person in group.person_set.all()]))

    except Group.DoesNotExist:
        return 'The group %s does not exist.'
