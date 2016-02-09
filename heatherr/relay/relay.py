from __future__ import absolute_import

import json
from urlparse import urlparse, urlunparse

from klein import Klein

import treq

from twisted.internet import reactor, ssl
from twisted.internet.endpoints import SSL4ClientEndpoint
from twisted.internet.defer import succeed
from twisted.internet.task import LoopingCall
from twisted.web import server
from twisted.python import log

from .protocol import RTMProtocol, RTMFactory


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
        self.counter = 0
        self.lc = None
        self.relay = None

    def onOpen(self):
        self.relay = self.factory.relay
        self.lc = LoopingCall(self.send_ping)
        self.lc.clock = self.clock
        self.lc.start(3, now=True)

    def onClose(self, wasClean, code, reason):
        if self.relay is not None:
            self.relay.remove_protocol(self.factory.token)

        if self.lc is not None:
            self.lc.stop()

    def onMessage(self, payload, isBinary):
        if isBinary:
            log.err("Binary message received: {0} bytes".format(len(payload)))

        data = json.loads(payload)
        if data["type"] == "message":
            self.relay.relay(data)

    def send_ping(self):
        return self.send_message({
            "type": "ping",
        })

    def send_message(self, data):
        return self.sendMessage(json.dumps(data))


class RelayFactory(RTMFactory):

    protocol = RelayProtocol

    def __init__(self, relay, token, session_data, debug=False):
        RTMFactory.__init__(self, session_data['url'], debug=debug)
        self.relay = relay
        self.token = token
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
        d = self.get_protocol(token=request.getHeader('X-Bot-Access-Token'))
        d.addCallback(
            lambda protocol: json.dumps(protocol.session_data, indent=2))
        return d

    @app.route('/im.open', methods=['POST'])
    def im_open(self, request):
        request.setHeader('Content-Type', 'application/json')
        d = treq.post('https://slack.com/api/im.open', data={
            'token': request.getHeader('X-Bot-Access-Token'),
            'user': request.args.get('user'),
        })
        d.addCallback(lambda response: response.content())
        return d

    @app.route('/rtm', methods=['POST'])
    def send_rtm(self, request):
        request.setHeader('Content-Type', 'application/json')
        data = json.load(request.content)
        d = self.get_protocol(token=request.getHeader('X-Bot-Access-Token'))
        d.addCallback(
            lambda protocol: protocol.send_message(data))
        return d

    def set_protocol(self, token, protocol):
        self.connections[token] = protocol
        return protocol

    def remove_protocol(self, token):
        log.msg('Removing protocol for %s' % (token,))
        return self.connections.pop(token, None)

    def get_protocol(self, token, **kwargs):
        if token in self.connections:
            return succeed(self.connections[token])

        d = self.rtm_start(token, **kwargs)
        d.addCallback(
            lambda protocol: self.set_protocol(token, protocol))
        return d

    def rtm_start(self, token, **kwargs):
        params = {
            'token': token
        }
        params.update(kwargs)
        d = treq.post('https://slack.com/api/rtm.start',
                      params=params)
        d.addCallback(lambda response: response.json())
        d.addCallback(self.connect_ws, token)
        return d

    def connect_ws(self, data, token):
        from autobahn.websocket.protocol import parseWsUrl
        (isSecure, host, port, resource, path, params) = parseWsUrl(
            data['url'])

        endpoint = SSL4ClientEndpoint(
            self.clock, host, port, ssl.ClientContextFactory())
        return endpoint.connect(
            RelayFactory(self, token, data, debug=self.debug))

    def relay(self, payload):
        d = treq.post(
            self.heatherr_url,
            auth=self.auth,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'})
        d.addCallback(lambda r: r.json())
        d.addCallback(lambda d: log.msg(d))
        return d
