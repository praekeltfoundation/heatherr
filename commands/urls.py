from django.conf.urls import url

from commands import views

urlpatterns = [
    url(r'^$', views.dispatcher.view, name='dispatcher'),
]
