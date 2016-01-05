from django.conf.urls import url

from bellman.commands import dispatcher

urlpatterns = [
    url(r'^$', dispatcher.view, name='dispatcher'),
]
