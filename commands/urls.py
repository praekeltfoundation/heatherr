from django.conf.urls import url

from commands import dispatcher

urlpatterns = [
    url(r'^$', dispatcher.view, name='dispatcher'),
]
