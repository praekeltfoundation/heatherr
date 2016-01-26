from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from bellman.groups.models import Group, Person
from bellman.models import SlackAccount


class CommandTestCase(TestCase):

    default_user_name = 'username'
    default_team_id = 'team_id'
    default_user_id = 'user_id'

    def get_user_account(self, username=None):
        user, _ = User.objects.get_or_create(
            username=(username or self.default_user_name))
        user.is_active = True
        user.save()
        return user

    def get_slack_account(self, username=None, team_id=None):
        user = self.get_user_account(username)
        slackaccount, _ = SlackAccount.objects.get_or_create(
            user=user, team_id=(team_id or self.default_team_id))
        return slackaccount

    def assertCommandResponse(self, command_str, expected_response,
                              team_id=None, user_id=None, token=None):
        team_id = team_id or self.default_team_id
        user_id = user_id or self.default_user_id
        token = token or settings.SLACK_TOKEN
        command, _, text = command_str.partition(' ')
        parameters = {
            'token': token,
            'command': command,
            'text': text,
            'team_id': team_id,
            'user_id': user_id,
        }
        response = self.client.post(reverse('dispatcher'), parameters)
        self.assertEqual(response.json(), {
            'text': expected_response,
        })


class GroupsCommandTestCase(CommandTestCase):

    def setUp(self):
        self.slackaccount = self.get_slack_account()

    def test_list(self):
        Group.objects.create(
            group_name='Group Name', slackaccount=self.slackaccount)
        self.assertCommandResponse('/announce list', '\n'.join([
            'Groups:',
            '- Group Name',
        ]))

    def test_empty_list(self):
        self.assertCommandResponse('/announce list', 'No groups exist')

    def test_list_member(self):
        group = Group.objects.create(
            group_name='group-name', slackaccount=self.slackaccount)
        person = Person.objects.create(
            person_id=self.default_user_id, slackaccount=self.slackaccount)
        person.groups.add(group)
        self.assertCommandResponse('/announce list', '\n'.join([
            'Groups:',
            '- group-name (member)',
        ]))

    def test_members(self):
        group = Group.objects.create(
            group_name='my-group', slackaccount=self.slackaccount)
        person = Person.objects.create(
            person_name='Example Person',
            person_id=self.default_user_id, slackaccount=self.slackaccount)
        person.groups.add(group)
        self.assertCommandResponse(
            '/announce members my-group',
            'People in my-group: Example Person')

    def test_create(self):
        self.assertEqual(
            Group.objects.filter(group_name='my-group',
                                 slackaccount=self.slackaccount).count(), 0)
        self.assertCommandResponse(
            '/announce create my-group',
            'The group my-group has been created.')
        self.assertEqual(
            Group.objects.filter(group_name='my-group',
                                 slackaccount=self.slackaccount).count(), 1)

    def test_join_nonexistent(self):
        self.assertCommandResponse(
            '/announce join my-group',
            'The group my-group does not exist.')

    def test_join(self):
        Group.objects.create(
            group_name='my-group', slackaccount=self.slackaccount)
        self.assertCommandResponse(
            '/announce join my-group',
            'You\'ve been added to my-group.')

    def test_leave_nonexistent(self):
        self.assertCommandResponse(
            '/announce leave my-group',
            'The group my-group does not exist.')

    def test_leave(self):
        group = Group.objects.create(
            group_name='my-group', slackaccount=self.slackaccount)
        person = Person.objects.create(
            person_id=self.default_user_id, slackaccount=self.slackaccount)
        person.groups.add(group)
        self.assertCommandResponse(
            '/announce leave my-group',
            'You\'ve been removed from my-group.')
        self.assertEqual(person.groups.count(), 0)

    def test_announce(self):
        group = Group.objects.create(
            group_name='my-group', slackaccount=self.slackaccount)
        person = Person.objects.create(
            person_id=self.default_user_id, slackaccount=self.slackaccount)
        person.groups.add(group)
        self.assertCommandResponse(
            '/announce announce my-group hello world!',
            '\n'.join([
                'Message from <@announcing-user-id> to `my-group`:',
                '<@%s>' % (person.person_id,),
                'hello world!'
            ]),
            user_id='announcing-user-id')
