from django.http import HttpResponse

from announce.bellman import Bellman


class AnnounceCommand(object):

    def handle(self, request):
        app = Bellman(
            text=request.POST['text'],
            user_name=request.POST['user_name'],
            user_id=request.POST['user_id'])
        app.execute()
        return HttpResponse(app.get_response())
