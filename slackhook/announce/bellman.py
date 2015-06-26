from .models import Group, Person
from django.views.decorators.csrf import csrf_exempt


class Bellman:

    def __init__(self, text, user_name, user_id):
        temp_command, space, self.text = text.partition(' ')
        self.command = temp_command.lower()
        self.user_name = user_name
        self.user_id = user_id
        self.response_text = ''
        print '********************************************'
        print self.command
        print self.user_name
        print self.user_id

    # list groups
    def list_groups(self):
        print 'Listing groups'
        self.response_text = 'List of groups: \n'
        for group in Group.objects.all():
            self.response_text += (str(group) + '\n')

    # people-in-group
    def people_in_group(self):
        group_name, space, self.text = self.text.partition(' ')
        if self.group_exists(group_name):
            for person in (
                    Group.objects
                    .get(group_name=group_name)
                    .person_set
                    .all()):
                self.response_text += (str(person) + '\n')
        else:
            self.response_text = 'That group doesn\'t exist'

    # list-my-groups
    def list_my_groups(self):
        self.update_user_info()
        # iterate through groups that person belongs to
        for group in (
                Person.objects
                .get(person_id=self.user_id)
                .groups
                .all()):
            self.response_text += (str(group) + '\n')
        # check if there are no groups
        if self.response_text == '':
            self.response_text = ('You don\'t seem'
                                  ' to belong to any groups. Use the '
                                  '\'opt-in\' '
                                  'command to join a group, '
                                  'or use \'help\' to get more info')
        else:
            self.response_text = (
                'Groups you belong to:\n' + self.response_text)

    # opt-in
    @csrf_exempt
    def opt_in(self):
        group_name, space, self.text = self.text.partition(' ')
        self.update_user_info()
        # check group exists
        if self.group_exists(group_name):
            # check if person belongs to group
            if not self.user_in_group(group_name):
                # add person to the group
                group = Group.objects.get(group_name=group_name)
                group.person_set.add(
                    Person.objects.get(person_id=self.user_id))
                group.save()
                self.response_text = 'You\'ve been added to ' + group_name
            else:
                self.response_text = 'You\'re already part of ' + group_name
        else:
            self.response_text = ('The group \'' + group_name +
                                  '\' doesn\'t exist')

    # opt-out
    def opt_out(self):
        pass

    # announce
    def announce(self):
        pass

    # help - autoresponse
    def help(self):
        pass

    # HELPER FUNCTIONS

    # execute (works out what function to run, based on command)
    @csrf_exempt
    def execute(self):
        if (self.command == 'list-groups' or
                self.command == 'list_groups'):
            self.list_groups()
        elif (self.command == 'people-in-group' or
                self.command == 'people_in_group'):
            self.people_in_group()
        elif (self.command == 'list-my-groups' or
                self.command == 'list-my-group' or
                self.command == 'list_my_groups' or
                self.command == 'list_my_group'):
            self.list_my_groups()
        elif (self.command == 'opt-in' or
                self.command == 'opt_in'):
            self.opt_in()
        elif (self.command == 'opt-out' or
                self.command == 'opt_out'):
            self.opt_out()
        elif self.command == 'announce':
            self.announce()
        elif self.command == 'help':
            self.help()
        else:
            self.response_text = 'Sorry, I didn\'t',
            'understand your command of: \'', self.command, '\'\n\n'
            self.help()

    @csrf_exempt
    def update_user_info(self):
        # check if user is new/if they exist
        if self.person_exists():
            if self.name_changed():
                # update user name
                p = Person.objects.get(person_id=self.user_id)
                p.person_name = self.user_name
                p.save()
        else:
            p = Person(person_id=self.user_id, person_name=self.user_name)
            p.save()

    def group_exists(self, group_name):
        return Group(group_name=group_name) in Group.objects.all()

    def person_exists(self):
        return Person(person_id=self.user_id) in Person.objects.all()

    def name_changed(self):
        return self.user_name != (Person.objects
                                        .get(person_id=self.user_id)
                                        .person_name)

    def user_in_group(self, group_name):
        return ((Person.objects
                .get(person_id=self.user_id))
                in
                (Group.objects
                    .get(group_name=group_name)
                    .person_set
                    .all()))

    @csrf_exempt
    def make_group(self, group_name):
        print 'running make_group'
        g = Group(group_name=group_name)
        g.save()

    def message_group_created(self, user_name, group_name):
        return 'Thanks ', user_name, ' you created the group: ', group_name

    def get_response(self):
        return self.response_text
