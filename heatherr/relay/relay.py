from __future__ import absolute_import

import json

from klein import Klein

from treq import post

from twisted.internet import reactor, ssl
from twisted.internet.endpoints import SSL4ClientEndpoint
from twisted.internet.defer import succeed
from twisted.web import server
from twisted.python import log

from .protocol import RTMProtocol, RTMFactory, connectWS


class RelaySite(server.Site):

    verbose = False

    def log(self, request):
        if self.verbose:
            server.Site.log(self, request)


class RelayProtocol(RTMProtocol):

    def __init__(self, session_data):
        RTMProtocol.__init__(self)
        self.session_data = session_data

    def send_message(self, data):
        return self.sendMessage(json.dumps(data))


class RelayFactory(RTMFactory):

    protocol = RelayProtocol

    def __init__(self, session_data, debug=False):
        RTMFactory.__init__(self, session_data['url'], debug=debug)
        self.session_data = session_data

    def buildProtocol(self, addr):
        p = self.protocol(self.session_data)
        p.factory = self
        return p


class Relay(object):
    """
    Relay, an RTM to HTTP relay server.
    """

    app = Klein()
    clock = reactor
    timeout = 5

    def __init__(self, heatherr_url, debug=False):
        self.connections = {}
        self.debug = debug
        self.heatherr_url = heatherr_url

    @app.handle_errors(KeyError)
    def key_error(self, request, failure):
        exception = failure.check(KeyError)
        request.setResponseCode(400)
        return json.dumps({
            'exception': '%s.%s' % (exception.__module__, exception.__name__),
            'message': failure.getErrorMessage(),
            'traceback': failure.getBriefTraceback(),
        }, indent=2)

    @app.route('/connect', methods=['POST'])
    def connect(self, request):
        request.setHeader('Content-Type', 'application/json')
        d = self.get_session(token=request.getHeader('X-Bot-Access-Token'))
        d.addCallback(lambda p: json.dumps({}))
        return d

    @app.route('/channels', methods=['GET'])
    def channels(self, request):
        request.setHeader('Content-Type', 'application/json')
        d = self.get_session(token=request.getHeader('X-Bot-Access-Token'))
        d.addCallback(
            lambda session: json.dumps(session.session_data, indent=2))
        return d

    @app.route('/im.open', methods=['POST'])
    def im_open(self, request):
        d = post('https://slack.com/api/im.open', data={
            'token': request.getHeader('X-Bot-Access-Token'),
            'user': request.args.get('user'),
        })
        d.addCallback(lambda response: response.content())
        return d

    @app.route('/rtm', methods=['POST'])
    def send_rtm(self, request):
        request.setHeader('Content-Type', 'application/json')
        data = json.dumps(json.load(request.content))
        d = self.get_session(token=request.getHeader('X-Bot-Access-Token'))
        d.addCallback(
            lambda session: session.send_message(data))
        return d

    def set_session(self, token, session):
        self.connections[token] = session
        return session

    def remove_session(self, session):
        for key, value in self.connections.items():
            if value == session:
                return self.connections.pop(session)

    def get_session(self, token, **kwargs):
        if token in self.connections:
            return succeed(self.connections[token])

        d = self.rtm_start(token, **kwargs)
        d.addCallback(
            lambda session: self.set_session(token, session))
        return d

    def rtm_start(self, token, **kwargs):
        params = {
            'token': token
        }
        params.update(kwargs)
        d = post('https://slack.com/api/rtm.start',
                 params=params)
        d.addCallback(lambda response: response.json())
        d.addCallback(self.connect_ws)
        return d

    def connect_ws(self, data):
        from autobahn.websocket.protocol import parseWsUrl
        (isSecure, host, port, resource, path, params) = parseWsUrl(
            data['url'])

        endpoint = SSL4ClientEndpoint(
            self.clock, host, port, ssl.ClientContextFactory())
        return endpoint.connect(RelayFactory(data, debug=self.debug))
