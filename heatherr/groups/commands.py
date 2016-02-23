from __future__ import absolute_import

from django.http import JsonResponse

from heatherr.groups.models import Group, Person
from heatherr.models import SlackAccount
from heatherr.views import dispatcher


bellman = dispatcher.command('/bellman')


@bellman.respond(r'^list$')
def list(request, match):
    """
    List the known groups::

        /bellman list

    Returns::

        Groups:
        - testing (member)

    """
    groups = Group.objects.filter(
        slackaccount__team_id=request.POST['team_id'])
    slackaccount = SlackAccount.objects.get(team_id=request.POST['team_id'])
    person, _ = Person.objects.get_or_create(
        person_id=request.POST['user_id'],
        slackaccount=slackaccount)
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


@bellman.respond(r'^create (?P<group_name>[\w-]+)$')
def create(request, match):
    """
    Create a new group::

        /bellman create foo

    Returns::

        The group foo has been created.

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


@bellman.respond(r'^join (?P<group_name>[\w-]+)$')
def join(request, match):
    """
    Join a group::

        /bellman join foo

    Returns::

        You've joined foo and will start receiving announcements for
        this group.

    """
    (group_name,) = match.groups()
    slackaccount = SlackAccount.objects.get(team_id=request.POST['team_id'])
    person, _ = Person.objects.get_or_create(
        person_id=request.POST['user_id'],
        slackaccount=slackaccount)
    try:
        person.person_name = request.POST['user_name']
        person.save()

        group = slackaccount.group_set.get(group_name=group_name)
        group.person_set.add(person)
        return JsonResponse({
            "response_type": "ephemeral",
            "text": (
                "You've joined %s and will start receiving announcements"
                " for this group.") % (group_name,)
        })
    except Group.DoesNotExist:
        return JsonResponse({
            "response_type": "ephemeral",
            "text": 'The group %s does not exist.' % (group_name,)
        })


@bellman.respond(r'^leave (?P<group_name>[\w-]+)$')
def leave(request, match):
    """
    Leave a group::

        /bellman leave foo

    Returns::

        You've been removed from foo.

    """
    (group_name,) = match.groups()
    slackaccount = SlackAccount.objects.get(team_id=request.POST['team_id'])
    person, _ = Person.objects.get_or_create(
        person_id=request.POST['user_id'],
        slackaccount=slackaccount)
    try:
        group = slackaccount.group_set.get(group_name=group_name)
        group.person_set.remove(person)
        return "You've been removed from %s." % (group_name,)
    except Group.DoesNotExist:
        return 'The group %s does not exist.' % (group_name,)


@bellman.respond(r'^members (?P<group_name>[\w-]+)$')
def members(request, match):
    """
    List the members in a group::

        /bellman members foo

    Returns::

        There are no people in foo.

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


@bellman.respond(r'^announce (?P<group_name>[\w-]+) (?P<message>.+)$')
def announce(request, match):
    """
    Broadcast a message to all the members in a group::

        /bellman announce foo hello world!


    """
    (group_name, message) = match.groups()
    slackaccount = SlackAccount.objects.get(team_id=request.POST['team_id'])
    person, _ = Person.objects.get_or_create(
        person_id=request.POST['user_id'],
        slackaccount=slackaccount)
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
