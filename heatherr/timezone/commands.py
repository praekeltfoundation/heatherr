from __future__ import absolute_import

from heatherr.models import SlackAccount
from heatherr.views import dispatcher


timezone = dispatcher.command('/time')

@timezone.respond(r'^for (?P<name>.+)$')
def for_(request, match):
    (group_name,) = match.groups()
    return 'not sure yet for %s' % (group_name,)
