from __future__ import absolute_import

import json
from urlparse import urlparse, urlunparse

from klein import Klein

import treq

from twisted.internet import reactor, ssl
from twisted.internet.endpoints import SSL4ClientEndpoint
from twisted.internet.defer import succeed, inlineCallbacks
from twisted.internet.task import LoopingCall
from twisted.web import server
from twisted.python import log

from .protocol import RTMProtocol, RTMFactory

from twisted.web import client
client._HTTP11ClientFactory.noisy = False


class RelaySite(server.Site):

    verbose = False

    def log(self, request):
        if self.verbose:
            server.Site.log(self, request)


class RelayProtocol(RTMProtocol):

    clock = reactor

    def __init__(self, session_data):
        RTMProtocol.__init__(self)
        self.session_data = session_data
        self.bot_user_id = session_data['self']['id']
        self.lc = None
        self.relay = None

    def onOpen(self):
        self.relay = self.factory.relay
        self.lc = LoopingCall(self.send_ping)
        self.lc.clock = self.clock
        self.lc.start(3, now=True)

    def onClose(self, wasClean, code, reason):
        if self.relay is not None:
            self.relay.remove_protocol(self.bot_user_id)

        if self.lc is not None:
            self.lc.stop()

    def onMessage(self, payload, isBinary):
        data = json.loads(payload)
        self.relay.relay(self.bot_user_id, data)

    def send_ping(self):
        return self.send_message({
            "type": "ping",
        })

    def send_message(self, data):
        return self.sendMessage(json.dumps(data))


class RelayFactory(RTMFactory):

    protocol = RelayProtocol

    def __init__(self, relay, session_data, debug=False):
        RTMFactory.__init__(self, session_data['url'], debug=debug)
        self.relay = relay
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
        pr = urlparse(heatherr_url)
        if pr.username or pr.password:
            self.auth = (pr.username, pr.password)
            self.heatherr_url = urlunparse((
                pr.scheme,
                '%s%s' % (pr.hostname,
                          (':%s' % (pr.port,) if pr.port else '')),
                pr.path,
                pr.params,
                pr.query,
                pr.fragment,
            ))
        else:
            self.auth = None

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
        d = self.get_protocol(bot_id=request.getUser(),
                              bot_token=request.getPassword())
        d.addCallback(
            lambda protocol: json.dumps(protocol.session_data, indent=2))
        return d

    @app.route('/rtm', methods=['POST'])
    def send_rtm(self, request):
        request.setHeader('Content-Type', 'application/json')
        data = json.load(request.content)
        d = self.get_protocol(bot_id=request.getUser(),
                              bot_token=request.getPassword())
        d.addCallback(
            lambda protocol: protocol.send_message(data))
        return d

    def set_protocol(self, bot_id, protocol):
        self.connections[bot_id] = protocol
        return protocol

    def remove_protocol(self, bot_id):
        log.msg('Removing protocol for %s' % (bot_id,))
        return self.connections.pop(bot_id, None)

    def get_protocol(self, bot_id, bot_token, **kwargs):
        if bot_id in self.connections:
            return succeed(self.connections[bot_id])

        d = self.rtm_start(bot_token, **kwargs)
        d.addCallback(
            lambda protocol: self.set_protocol(bot_id, protocol))
        return d

    def rtm_start(self, bot_token, **kwargs):
        params = {
            'token': bot_token
        }
        params.update(kwargs)
        d = treq.post('https://slack.com/api/rtm.start',
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
        return endpoint.connect(
            RelayFactory(self, data, debug=self.debug))

    @inlineCallbacks
    def relay(self, bot_user_id, payload):
        response = yield treq.post(
            self.heatherr_url,
            auth=self.auth,
            data=json.dumps(payload),
            headers={
                'Content-Type': 'application/json',
                'X-Bot-User-Id': bot_user_id,
            },
            timeout=2)
        headers = response.headers
        if headers.getRawHeaders('Content-Type') == ['application/json']:
            data = yield response.json()
            protocol = self.connections.get(bot_user_id)

            if protocol is None:
                log.err('Protocol gone missing while trying to reply.')
                return

            for message in data:
                protocol.send_message(message)
