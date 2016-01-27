"""heatherr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView
from heatherr import dispatcher


urlpatterns = [
    url(r'^$', RedirectView.as_view(url=settings.LOGIN_URL)),
    url(r'^', include('social.apps.django_app.urls', namespace='social')),
    url(r'^commands/', dispatcher.view, name='dispatcher'),
    # NOTE: This is here for backwards compatibility.
    url(r'^announce/', dispatcher.view, name='dispatcher'),
    url(r'^accounts/', include('heatherr.account.urls', namespace='accounts')),
    url(r'^admin/', include(admin.site.urls)),
]
