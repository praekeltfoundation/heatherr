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
        self.response_text = 'list of groups: \n'
        for group in Group.objects.all():
            self.response_text += (str(group) + '\n')

    # people-in-group
    def people_in_group(self):
        pass

    # list-my-groups
    def list_my_groups(self):
        pass

    # opt-in
    def opt_in(self):
        pass

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

    def update_user_info(self, user_id, user_name):
        p = Person(person_id=user_id, person_name=user_name)
        # check if user is new/if they exist
        if self.person_exists(user_id):
            # check if username is the same
            if self.name_changed(user_id, user_name):
                p.save()
        else:
            p.save()

    def group_exists(self, group_name):
        print 'running group_exists'
        print 'Existing Groups:'
        for group in Group.objects.all():
            print group
        test_group = Group(group_name=group_name)
        if test_group in Group.objects.all():
            print "group exists!"
        else:
            print "group does not exist"
        return test_group in Group.objects.all()

    def person_exists(self, user_id):
        return Person.object(person_id=user_id) in Person.objects.all()

    def name_changed(self, user_id, user_name):
        return user_name != Person.objects.get(person_id=user_id).person_name

    @csrf_exempt
    def make_group(self, group_name):
        print 'running make_group'
        g = Group(group_name=group_name)
        g.save()

    def message_group_created(self, user_name, group_name):
        return 'Thanks ', user_name, ' you created the group: ', group_name

    def get_response(self):
        return self.response_text
