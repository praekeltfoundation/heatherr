from announce.models import Group, Person
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import logging
import urllib2
import json


logger = logging.getLogger("bellman.bellman")


class Bellman(object):

    def __init__(self, text, user_name, user_id):
        temp_command, space, self.text = text.partition(" ")
        self.command = temp_command.lower()
        self.user_name = user_name
        self.user_id = user_id
        self.response_text = ""

    # list groups
    def list_groups(self):
        self.response_text = "List of groups: \n"
        for group in Group.objects.all():
            self.response_text += (str(group) + "\n")

    # people-in-group
    def people_in_group(self):
        group_name, space, self.text = self.text.partition(" ")
        if group_name != "":
            if self.group_exists(group_name):
                for person in (
                        Group.objects
                        .get(group_name=group_name)
                        .person_set
                        .all()):
                    self.response_text += (str(person) + "\n")
                # Check if there are people in group
                if self.response_text == "":
                    self.response_text = (
                        "There are currently no people in {0}"
                        .format(group_name))
                # otherwise insert header message
                else:
                    self.response_text = (
                        "People in `{0}`:\n{1}".format(group_name,
                                                       self.response_text))
            else:
                self.response_text = ("The group `{0}` doesn't exist"
                                      .format(group_name))
        else:
            self.response_text = ("Please give me a group name in your bellman"
                                  " command:\n"
                                  "```/bellman people-in-group GROUP_NAME```")

    # list-my-groups
    def list_my_groups(self):
        self.update_user_info()
        # iterate through groups that person belongs to
        for group in (
                Person.objects
                .get(person_id=self.user_id)
                .groups
                .all()):
            self.response_text += (str(group) + "\n")
        # check if there are no groups
        if self.response_text == "":
            self.response_text = ("You don't seem"
                                  " to belong to any groups. Use the "
                                  "'opt-in' "
                                  "command to join a group:\n"
                                  " ```/bellman opt-in GROUP_NAME``` "
                                  "or use 'help' to get more info:\n"
                                  "```/bellman help```")
        # otherwise insert header message
        else:
            self.response_text = (
                "Groups you belong to:\n{0}".format(self.response_text))

    # opt-in
    @csrf_exempt
    def opt_in(self):
        group_name, space, self.text = self.text.partition(" ")
        self.update_user_info()
        if group_name != "":
            # check group exists
            if self.group_exists(group_name):
                # check if person belongs to group
                if not self.user_in_group(group_name):
                    # add person to the group
                    group = Group.objects.get(group_name=group_name)
                    group.person_set.add(
                        Person.objects.get(person_id=self.user_id))
                    group.save()
                    self.response_text = ("You've been added to {0}"
                                          .format(group_name))
                else:
                    self.response_text = ("You're already part of {0}"
                                          .format(group_name))
            else:
                self.response_text = ("The group `{0}` doesn't exist"
                                      .format(group_name))
        else:
            self.response_text = ("Please give me a group name in your bellman"
                                  " command:\n"
                                  "```/bellman opt-in GROUP_NAME```")

    # opt-out
    def opt_out(self):
        group_name, space, self.text = self.text.partition(" ")
        self.update_user_info()
        if group_name != "":
            # check group exists
            if self.group_exists(group_name):
                # check if person belongs to group
                if self.user_in_group(group_name):
                    # remove person from the group
                    person = Person.objects.get(person_id=self.user_id)
                    (person.groups
                           .remove(Group.objects.get(group_name=group_name)))
                    person.save()
                    self.response_text = ("You've been removed from {0}"
                                          .format(group_name))
                else:
                    self.response_text = "You're not in {0}".format(group_name)
            else:
                self.response_text = ("The group `{0}` doesn't exist"
                                      .format(group_name))
        else:
            self.response_text = ("Please give me a group name in your bellman"
                                  " command:\n"
                                  "```/bellman opt-out GROUP_NAME```")

    # create
    def create(self):
        group_name, space, self.text = self.text.partition(" ")
        self.update_user_info()
        if group_name != "":
            # check group exists
            if not self.group_exists(group_name):
                # create and save the group
                group = Group(group_name=group_name)
                group.save()
                self.response_text = ("The group `{0}` has"
                                      " been created.\n"
                                      "To join the group, run the following "
                                      "command:\n"
                                      "```/bellman opt-in {0}"
                                      "```".format(group_name))
            else:
                self.response_text = ("The group `{0}` already exists"
                                      .format(group_name))
        else:
            self.response_text = ("Please give me a group name in your bellman"
                                  " command:\n"
                                  "```/bellman create GROUP_NAME```")

    # announce
    def announce(self):
        group_name, space, self.text = self.text.partition(" ")
        self.update_user_info()
        if group_name != "":
            # check group exists
            if self.group_exists(group_name):
                # check that the announcer belongs to the group
                if self.user_in_group(group_name):
                    # check is there is a message
                    if self.text != "":
                        self.text = "\n".join([
                            self.get_ping_tags(group_name),
                            self.text,
                        ])
                        self.send_announcement()
                        self.response_text = ("The group `{0}` "
                                              "has been sent your message in"
                                              " the bellman channel"
                                              .format(group_name))
                    else:
                        self.response_text = ("Please give me a message in "
                                              "your bellman command:\n"
                                              "```/bellman announce "
                                              "GROUP_NAME MESSAGE```")
                else:
                    self.response_text = ("You do not belong to the group "
                                          "`{0}`".format(group_name))
            else:
                self.response_text = ("The group `{0}` doesn't exist"
                                      .format(group_name))
        else:
            self.response_text = ("Please give me a group name in your bellman"
                                  " command:\n"
                                  "```/bellman announce GROUP_NAME MESSAGE```")

    # help - autoresponse
    def help(self):
        self.response_text = ("LIST THE GROUPS THAT EXIST\n\n"
                              "```/bellman list-groups```\n\n"
                              "SEE THE PEOPLE WHO BELONG TO A PARTICULAR "
                              "GROUP\n\n"
                              "```/bellman people-in-group <group>```\n\n"
                              "LIST THE GROUPS YOU BELONG TO\n\n"
                              "```/bellman list-my-groups```\n\n"
                              "JOIN A GROUP\n\n"
                              "```/bellman opt-in <group name>```\n\n"
                              "OPT-OUT OF A GROUP\n\n"
                              "```/bellman opt-out <group name>```\n\n"
                              "CREATE A GROUP\n\n"
                              "```/bellman create <group name>```\n\n"
                              "SEND MESSAGE TO A GROUP\n\n"
                              "```/bellman announce <group name> <message>```")

    # execute (works out what function to run, based on command)
    @csrf_exempt
    def execute(self):
        if (self.command == "list-groups" or
                self.command == "list_groups"):
            self.list_groups()
        elif (self.command == "people-in-group" or
                self.command == "people_in_group"):
            self.people_in_group()
        elif (self.command == "list-my-groups" or
                self.command == "list-my-group" or
                self.command == "list_my_groups" or
                self.command == "list_my_group"):
            self.list_my_groups()
        elif (self.command == "opt-in" or
                self.command == "opt_in"):
            self.opt_in()
        elif (self.command == "opt-out" or
                self.command == "opt_out"):
            self.opt_out()
        elif (self.command == "create" or
                self.command == "create_group" or
                self.command == "create-group"):
            self.create()
        elif self.command == "announce":
            self.announce()
        elif (self.command == "help" or
                self.command == ""):
            self.help()
        else:
            self.response_text = ("Sorry, I didn't"
                                  " understand your command of"
                                  " ```{0}```\n\n".format(self.command))
            self.help()

    # HELPER FUNCTIONS

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
        return Group.objects.filter(group_name=group_name).exists()

    def person_exists(self):
        return Person.objects.filter(person_id=self.user_id).exists()

    def name_changed(self):
        return self.user_name != (Person.objects
                                        .get(person_id=self.user_id)
                                        .person_name)

    def user_in_group(self, group_name):
        return Group.objects.filter(person__person_id=self.user_id,
                                    group_name=group_name).exists()

    @csrf_exempt
    def make_group(self, group_name):
        g = Group(group_name=group_name)
        g.save()

    def send_announcement(self):
        data = {
            "text": self.text
        }
        url = settings.SLACK_INCOMING_WEBHOOK_URL
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(url, data=json.dumps(data))
        request.add_header("Content-Type", "application/json")
        opener.open(request)
        logger.debug("Sent reply: %r" % (data,))

    def get_ping_tags(self, group_name):
        tag_text = ("Message from <@{0}> to `{1}`:\n"
                    .format(self.user_id, group_name))
        for person in (Group.objects
                       .get(group_name=group_name)
                       .person_set
                       .all()):
            if(person.person_id != self.user_id):
                tag_text += ("<@{0}> ".format(person.person_id))
        return tag_text

    def get_response(self):
        return self.response_text
