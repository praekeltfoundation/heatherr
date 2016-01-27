from __future__ import absolute_import

from django.http import JsonResponse

from heatherr.groups.models import Group, Person
from heatherr.models import SlackAccount
from heatherr.views import dispatcher


announce = dispatcher.command('/announce')


@announce.respond(r'^list$')
def list(request, match):
    """
    `list`

    List the known groups.
    """
    groups = Group.objects.filter(
        slackaccount__team_id=request.POST['team_id'])
    person, _ = Person.objects.get_or_create(person_id=request.POST['user_id'])
    if not groups.exists():
        return JsonResponse({
            'text': 'No groups exist'
        })

    return 'Groups:\n%s' % ('\n'.join([
        '- %s%s' % (
            unicode(group),
            (' (member)'
             if person.groups.filter(pk=group.pk).exists()
             else ''))
        for group in groups]),)


@announce.respond(r'^create (?P<group_name>[\w-]+)$')
def create(request, match):
    """
    `create <new-group-name>`

    Create a new group.
    """
    (group_name,) = match.groups()
    slackaccount = SlackAccount.objects.get(team_id=request.POST['team_id'])
    group, created = Group.objects.get_or_create(
        slackaccount=slackaccount,
        group_name=group_name)
    if created:
        return 'The group %s has been created.' % (group_name,)
    else:
        return 'The group %s already exists.' % (group_name,)


@announce.respond(r'^join (?P<group_name>[\w-]+)$')
def join(request, match):
    """
    `join <group-name>`

    Join a group.
    """
    (group_name,) = match.groups()
    slackaccount = SlackAccount.objects.get(team_id=request.POST['team_id'])
    person, _ = Person.objects.get_or_create(person_id=request.POST['user_id'])
    try:
        group = slackaccount.group_set.get(group_name=group_name)
        group.person_set.add(person)
        return "You've been added to %s." % (group_name,)
    except Group.DoesNotExist:
        return 'The group %s does not exist.' % (group_name,)


@announce.respond(r'^leave (?P<group_name>[\w-]+)$')
def leave(request, match):
    """
    `leave <group-name>`

    Leave a group
    """
    (group_name,) = match.groups()
    slackaccount = SlackAccount.objects.get(team_id=request.POST['team_id'])
    person, _ = Person.objects.get_or_create(person_id=request.POST['user_id'])
    try:
        group = slackaccount.group_set.get(group_name=group_name)
        group.person_set.remove(person)
        return "You've been removed from %s." % (group_name,)
    except Group.DoesNotExist:
        return 'The group %s does not exist.' % (group_name,)


@announce.respond(r'^members (?P<group_name>[\w-]+)$')
def members(request, match):
    """
    `members <group-name>`

    List the members in a group.
    """
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
        return 'The group %s does not exist.' % (group_name,)


@announce.respond(r'^announce (?P<group_name>[\w-]+) (?P<message>.+)$')
def announce(request, match):
    """
    `announce <group-name> <your message>`

    Broadcast a message to all the members in a group
    """
    (group_name, message) = match.groups()
    slackaccount = SlackAccount.objects.get(team_id=request.POST['team_id'])
    person, _ = Person.objects.get_or_create(person_id=request.POST['user_id'])
    try:
        group = slackaccount.group_set.get(group_name=group_name)
        return 'Message from <@%s> to `%s`:\n%s\n%s' % (
            person.person_id, group.group_name,
            ' '.join(['<@%s>' % (member.person_id,)
                      for member in group.person_set.all()]),
            message,
        )
    except Group.DoesNotExist:
        return 'The group %s does not exist.' % (group_name,)
