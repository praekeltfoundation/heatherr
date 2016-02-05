import sys

from twisted.internet.endpoints import serverFromString
from twisted.internet import reactor
from twisted.python import log

from .relay import Relay, RelaySite
import click

@click.command()
@click.option('--listen',
              default='tcp:8001',
              help='The TCP port to listen on.')
@click.option('--heatherr-url',
              default='http://username:password@localhost:8000/relay/',
              help='Where to find heatherr.')
@click.option('--verbose/--no-verbose',
              default=False,
              help='Turn on verbose log output.')
@click.option('--debug/--no-debug',
              default=False,
              help='Turn on Websocket debugging output.')
@click.option('--logfile',
              help='Where to log output to.',
              type=click.File('a'),
              default=sys.stdout)
def run(listen, heatherr_url, verbose, debug, logfile):
    log.startLogging(logfile)

    endpoint = serverFromString(reactor, str(listen))
    site = RelaySite(Relay(heatherr_url, debug=debug).app.resource())
    site.verbose = verbose
    endpoint.listen(site)
    reactor.run()


if __name__ == '__main__':
    run()
