from heatherr.groups.models import Group, Person
from heatherr.tests import HeatherrTestCase, CommandTestMixin


class GroupsCommandTestCase(HeatherrTestCase, CommandTestMixin):

    def setUp(self):
        self.slackaccount = self.get_slack_account()

    def test_list(self):
        Group.objects.create(
            group_name='Group Name', slackaccount=self.slackaccount)
        self.assertCommandResponse('/bellman list', '\n'.join([
            'Groups:',
            '- Group Name',
        ]))

    def test_empty_list(self):
        self.assertCommandResponse('/bellman list', 'No groups exist')

    def test_list_member(self):
        group = Group.objects.create(
            group_name='group-name', slackaccount=self.slackaccount)
        person = Person.objects.create(
            person_id=self.default_user_id, slackaccount=self.slackaccount)
        person.groups.add(group)
        self.assertCommandResponse('/bellman list', '\n'.join([
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
            '/bellman members my-group',
            'People in my-group: Example Person')

    def test_members_empty(self):
        Group.objects.create(
            group_name='my-group', slackaccount=self.slackaccount)
        self.assertCommandResponse(
            '/bellman members my-group',
            'There are no people in my-group.')

    def test_members_nonexistent(self):
        self.assertCommandResponse(
            '/bellman members my-group',
            'The group my-group does not exist.')

    def test_create(self):
        self.assertEqual(
            Group.objects.filter(group_name='my-group',
                                 slackaccount=self.slackaccount).count(), 0)
        self.assertCommandResponse(
            '/bellman create my-group',
            'The group my-group has been created.')
        self.assertEqual(
            Group.objects.filter(group_name='my-group',
                                 slackaccount=self.slackaccount).count(), 1)

    def test_create_existing(self):
        Group.objects.create(
            group_name='my-group', slackaccount=self.slackaccount)
        self.assertCommandResponse(
            '/bellman create my-group',
            'The group my-group already exists.')

    def test_join_nonexistent(self):
        self.assertCommandResponse(
            '/bellman join my-group',
            'The group my-group does not exist.')

    def test_join(self):
        Group.objects.create(
            group_name='my-group', slackaccount=self.slackaccount)
        self.assertCommandResponse(
            '/bellman join my-group',
            ('You\'ve joined my-group and will start receiving '
             'announcements for this group.'),
            response_type='ephemeral')

    def test_leave_nonexistent(self):
        self.assertCommandResponse(
            '/bellman leave my-group',
            'The group my-group does not exist.')

    def test_leave(self):
        group = Group.objects.create(
            group_name='my-group', slackaccount=self.slackaccount)
        person = Person.objects.create(
            person_id=self.default_user_id, slackaccount=self.slackaccount)
        person.groups.add(group)
        self.assertCommandResponse(
            '/bellman leave my-group',
            'You\'ve been removed from my-group.')
        self.assertEqual(person.groups.count(), 0)

    def test_announce(self):
        group = Group.objects.create(
            group_name='my-group', slackaccount=self.slackaccount)
        person = Person.objects.create(
            person_id=self.default_user_id, slackaccount=self.slackaccount)
        person.groups.add(group)
        self.assertCommandResponse(
            '/bellman announce my-group hello world!',
            '\n'.join([
                'Message from <@announcing-user-id> to `my-group`:',
                '<@%s>' % (person.person_id,),
                'hello world!'
            ]),
            user_id='announcing-user-id')

    def test_announce_nonexistent(self):
        self.assertCommandResponse(
            '/bellman announce my-group hullo!',
            'The group my-group does not exist.')
