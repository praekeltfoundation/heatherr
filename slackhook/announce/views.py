from django.http import HttpResponse  # JsonResponse
from .models import Group, Person
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from bellman import Bellman
# Create your views here.


def check_token_safe(token):
    return token == settings.SLACK_TOKEN

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

    # security check
    if request.method == 'POST' and check_token_safe(request.POST['token']):
        
        # Checker statements (to be deleted)
        print 'POST from northhq slack'
        print request.POST
        user_name = request.POST['user_name']
        args = request.POST['text'].split()
        print 'args:', args
        num_of_args = len(args)
        print 'num_of_args:', num_of_args

        #check that POST has the correct form?

        bellman = Bellman(
            text=request.POST['text'], 
            user_name=request.POST['user_name'], 
            user_id=request.POST['user_id'])

        bellman.

    return HttpResponse(response_text)
