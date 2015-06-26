from django.http import HttpResponse  # JsonResponse
from .models import Group, Person
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
# Create your views here.


def check_token_safe(token):
    return token == settings.SLACK_TOKEN


def group_exists(group_name):
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


def person_exists(user_id):
    return Person.object(person_id=user_id) in Person.objects.all()


def name_changed(user_id, user_name):
    return user_name != Person.objects.get(person_id=user_id).person_name


@csrf_exempt
def make_group(group_name):
    print 'running make_group'
    g = Group(group_name=group_name)
    g.save()


def message_group_created(user_name, group_name):
    return 'Thanks ', user_name, ' you created the group: ', group_name


def update_user_info(user_id, user_name):
    p = Person(person_id=user_id, person_name=user_name)
    # check if user is new/if they exist
    if person_exists(user_id):
        # check if username is the same
        if name_changed(user_id, user_name):
            p.save()
    else:
        p.save()


@csrf_exempt
def announce(request):
    print "---------------------------------------"
    # default empty text field will be ignored by slack
    response_text = ''
    if request.method == 'POST' and check_token_safe(request.POST['token']):
        print 'POST from northhq slack'
        print request.POST
        user_name = request.POST['user_name']
        args = request.POST['text'].split()
        print 'args:', args
        num_of_args = len(args)
        print 'num_of_args:', num_of_args
        if num_of_args > 0:
            # CREATE GROUP
            if args[0] == 'create':
                # is there an argument (i.e. a group name)
                if num_of_args > 1:
                    # Does the group already exist
                    if group_exists(args[1]):
                        response_text = "That group already exists"
                    else:
                        make_group(args[1])
                        response_text = message_group_created(
                            user_name, args[1])
                else:
                    response_text = 'Hey there NAME, you haven\'t given me a',
                    'group name to create'

            # LIST GROUPS
            elif args[0] == 'list-groups':
                response_text = 'list of groups: \n'
                for group in Group.objects.all():
                    response_text += (str(group) + '\n')

            # OPT-IN
            elif args[0] == 'opt-in':
                if num_of_args > 1:
                    # does the group exist?
                    if group_exists(args[1]):
                        # check if user exists and has the same user_name
                        update_user_info(
                            request.POST['user_id'], request.POST['user_name'])
                        person = Person.objects.get(
                            person_id=request.POST['user_id'])
                        group = Group.objects.get(group_name=args[1])

                        group.save()
                        person.groups.add(group)
                        person.save()
                else:
                    response_text = 'Hey there NAME, you haven\'t given me a',
                    'group name to opt-in to'
        else:
            response_text = 'Nothing has been accomplished'
    else:
        print "It's not legitimate"
    print response_text
    print "---------------------------------------"
    return HttpResponse(response_text)
