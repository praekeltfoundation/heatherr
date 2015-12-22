from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^connect/', views.connect, name='connect'),
    url(r'^authorize/', views.authorize, name='authorize'),
]
