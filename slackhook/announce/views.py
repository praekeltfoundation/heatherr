from django.http import HttpResponse  # JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from bellman import Bellman
# Create your views here.


def check_token_safe(token):
    return token == settings.SLACK_TOKEN


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
        args = request.POST['text'].split()
        print 'args:', args
        num_of_args = len(args)
        print 'num_of_args:', num_of_args

        # check that POST has the correct form?

        bellman = Bellman(
            text=request.POST['text'],
            user_name=request.POST['user_name'],
            user_id=request.POST['user_id'])

        bellman.execute()

    return HttpResponse(response_text)
