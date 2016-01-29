from __future__ import absolute_import

from heatherr.models import SlackAccount
from heatherr.views import dispatcher


timezone = dispatcher.command('/time')

@timezone.respond('r^for (.+)$')
def for_(request, match):
    print match
    return 'not sure yet'
