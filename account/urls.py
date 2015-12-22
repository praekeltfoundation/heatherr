from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^login/', views.login_view, name='login'),
    url(r'^logout/', views.logout_view, name='logout'),
    url(r'^profile/', views.profile, name='profile'),
    url(r'^authorize/', views.authorize, name='authorize'),
    url(
        r'^integration/(?P<pk>[0-9]+)/$',
        views.SlackAccountDetailView.as_view(),
        name='slack-detail'),
]
