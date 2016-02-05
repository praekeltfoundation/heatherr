import json

from twisted.trial.unittest import TestCase
from twisted.internet import reactor
from twisted.internet.defer import succeed, inlineCallbacks, returnValue
from twisted.internet.endpoints import serverFromString
from twisted.web.client import HTTPConnectionPool
from twisted.internet.task import Clock

from heatherr.relay.relay import Relay, RelaySite, RelayProtocol

import treq

from mock import patch, call, Mock


class RelayTest(TestCase):

    def setUp(self):
        self.pool = HTTPConnectionPool(reactor, persistent=False)
        self.addCleanup(self.pool.closeCachedConnections)

    @inlineCallbacks
    def mk_relay(self, heatherr_url='http://www.example.org'):
        endpoint = serverFromString(reactor, 'tcp:0')
        relay = Relay(heatherr_url)
        site = relay.app.resource()
        port = yield endpoint.listen(RelaySite(site))
        url = 'http://127.0.0.1:%s' % (port.getHost().port,)
        self.addCleanup(port.loseConnection)
        returnValue((url, relay))

    def test_auth(self):
        r = Relay('http://username:password@example.org')
        self.assertEqual(r.heatherr_url, 'http://example.org')
        self.assertEqual(r.auth, ('username', 'password'))

    def test_no_auth(self):
        r = Relay('http://example.org')
        self.assertEqual(r.heatherr_url, 'http://example.org')
        self.assertEqual(r.auth, None)

    @inlineCallbacks
    def test_connect_patched(self):
        url, r = yield self.mk_relay()
        r.get_protocol = lambda *a, **kw: succeed(RelayProtocol({
            'this': 'is session-data',
        }))
        response = yield treq.post(
            '%s/connect' % (url,),
            headers={
                'X-Bot-Access-Token': 'foo',
            },
            pool=self.pool)
        data = yield response.json()
        self.assertEqual(data, {
            'this': 'is session-data',
        })

    @inlineCallbacks
    def test_get_protocol(self):
        _, r = yield self.mk_relay()
        mock_proto = RelayProtocol({
            'this': 'is session-data',
        })
        r.rtm_start = lambda *a, **kw: succeed(mock_proto)

        protocol = yield r.get_protocol('token')
        self.assertEqual(protocol, mock_proto)
        self.assertEqual(r.connections, {
            'token': mock_proto
        })

    @inlineCallbacks
    def test_get_protocol_cached(self):
        _, r = yield self.mk_relay()
        r.connections['foo'] = 'Cached Protocol Value'
        protocol = yield r.get_protocol('foo')
        self.assertEqual(protocol, 'Cached Protocol Value')

    @inlineCallbacks
    def test_remove_protocol(self):
        _, r = yield self.mk_relay()
        r.connections['foo'] = 'Cached Protocol Value'
        protocol = yield r.remove_protocol('foo')
        self.assertEqual(protocol, 'Cached Protocol Value')
        self.assertEqual(r.connections, {})

    @patch.object(treq, 'post')
    @patch.object(Relay, 'connect_ws')
    @inlineCallbacks
    def test_rtm_start(self, mock_connect_ws, mock_post):
        mock_response = Mock()
        mock_response.json = lambda: succeed({'foo': 'bar'})
        mock_post.return_value = succeed(mock_response)

        mock_connect_ws.return_value = succeed('dummy return value')

        _, r = yield self.mk_relay()
        resp = yield r.rtm_start('token')
        self.assertEqual(resp, 'dummy return value')
        mock_connect_ws.assert_called_with(
            {'foo': 'bar'}, 'token')

    @patch.object(treq, 'post')
    @inlineCallbacks
    def test_relay(self, mock_post):
        mock_response = Mock()
        mock_response.json = lambda: succeed({})
        mock_post.return_value = succeed(mock_response)

        _, r = yield self.mk_relay('http://username:password@example.com/foo')
        r.relay({'foo': 'bar'})

        mock_post.assert_called_with(
            'http://example.com/foo',
            auth=('username', 'password'),
            data='{"foo": "bar"}',
            headers={'Content-Type': 'application/json'})

    @inlineCallbacks
    def test_send_rtm(self):
        mock_protocol = Mock()
        mock_protocol.send_message = Mock()
        mock_protocol.send_message.return_value = None

        url, r = yield self.mk_relay()
        r.get_protocol = lambda *a, **kw: succeed(mock_protocol)
        response = yield treq.post(
            '%s/rtm' % (url,),
            data=json.dumps({'foo': 'bar'}),
            headers={'X-Bot-Access-Token': 'token'},
            pool=self.pool)
        mock_protocol.send_message.assert_called_with({
            'foo': 'bar'
        })

    def test_protocol_relay(self):
        relay = Mock()
        relay.relay = Mock()

        protocol = RelayProtocol({
            'this': 'is session-data',
        })
        protocol.relay = relay
        protocol.onMessage('{"foo": "bar"}', False)
        relay.relay.assert_called_with({"foo": "bar"})

    @inlineCallbacks
    def test_protocol_close(self):
        _, r = yield self.mk_relay()

        protocol = RelayProtocol({
            'this': 'is session-data',
        })
        protocol.factory = Mock()
        protocol.factory.token = 'the-token'
        protocol.relay = r

        r.set_protocol('the-token', protocol)

        protocol.onClose(True, None, None)
        self.assertEqual(r.connections, {})

    def test_ping(self):
        protocol = RelayProtocol({
            'this': 'is session-data',
        })
        protocol.clock = Clock()
        protocol.factory = Mock()
        protocol.send_message = Mock()

        protocol.onOpen()
        protocol.clock.advance(3)
        protocol.send_message.assert_has_calls([
            call({'type': 'ping'}),
            call({'type': 'ping'})])
