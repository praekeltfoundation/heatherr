import json

from twisted.trial.unittest import TestCase
from twisted.internet import reactor
from twisted.internet.defer import succeed, inlineCallbacks, returnValue
from twisted.internet.endpoints import serverFromString
from twisted.test.proto_helpers import StringTransport
from twisted.web.client import HTTPConnectionPool
from twisted.web.http_headers import Headers
from twisted.internet.task import Clock

from heatherr.relay.relay import Relay, RelaySite, RelayProtocol, RelayFactory

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
        r.get_protocol = Mock()
        r.get_protocol.return_value = succeed(RelayProtocol({
            'self': {
                'id': 'the-user-id'
            }
        }))

        response = yield treq.post(
            '%s/connect' % (url,),
            auth=('bot-id', 'bot-token'),
            pool=self.pool)
        data = yield response.json()
        self.assertEqual(data, {
            'self': {
                'id': 'the-user-id',
            },
        })
        r.get_protocol.assert_called_with(
            bot_id='bot-id', bot_token='bot-token')

    @inlineCallbacks
    def test_disconnect(self):
        url, r = yield self.mk_relay()
        protocol = RelayProtocol({
            'self': {
                'id': 'the-user-id'
            }
        })
        protocol.transport = StringTransport()
        protocol.transport.loseConnection = Mock()
        protocol.transport.loseConnection.return_value = None

        r.connections['bot-id'] = protocol

        yield treq.post(
            '%s/disconnect' % (url,),
            auth=('bot-id', 'bot-token'),
            pool=self.pool)

        protocol.transport.loseConnection.assert_called_with()

    @inlineCallbacks
    def test_get_protocol(self):
        _, r = yield self.mk_relay()
        mock_proto = RelayProtocol({
            'self': {
                'id': 'the-user-id'
            },
        })
        r.rtm_start = Mock()
        r.rtm_start.return_value = succeed(mock_proto)

        protocol = yield r.get_protocol('bot-id', 'bot-token')
        self.assertEqual(protocol, mock_proto)
        self.assertEqual(r.connections, {
            'bot-id': mock_proto
        })
        r.rtm_start.assert_called_with('bot-token')

    @inlineCallbacks
    def test_get_protocol_cached(self):
        _, r = yield self.mk_relay()
        r.connections['bot-id'] = 'Cached Protocol Value'
        protocol = yield r.get_protocol('bot-id', 'bot-token')
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
        mock_connect_ws.assert_called_with({'foo': 'bar'})

    @patch.object(treq, 'post')
    @inlineCallbacks
    def test_relay(self, mock_post):
        mock_response = Mock()
        mock_response.headers
        mock_response.headers = Headers({
            'Content-Type': ['application/json']
        })

        mock_response.json = Mock()
        mock_response.json.return_value = succeed([])

        mock_post.return_value = succeed(mock_response)

        _, r = yield self.mk_relay('http://username:password@example.com/foo')
        r.relay('user-id', {'foo': 'bar'})

        mock_post.assert_called_with(
            'http://example.com/foo',
            auth=('username', 'password'),
            data='{"foo": "bar"}',
            headers={
                'Content-Type': 'application/json',
                'X-Bot-User-Id': 'user-id',
            },
            timeout=2)

    @patch.object(treq, 'post')
    @inlineCallbacks
    def test_relay_with_inline_response(self, mock_post):
        mock_response = Mock()
        mock_response.headers
        mock_response.headers = Headers({
            'Content-Type': ['application/json']
        })

        mock_response.json = Mock()
        mock_response.json.return_value = succeed([{
            'text': 'the-outbound-reply'
        }])

        mock_post.return_value = succeed(mock_response)

        _, r = yield self.mk_relay('http://username:password@example.com/foo')

        mock_protocol = Mock()
        mock_protocol.send_message = Mock()
        mock_protocol.send_message.return_value = None

        r.connections['user-id'] = mock_protocol

        yield r.relay('user-id', {'foo': 'bar'})

        mock_protocol.send_message.assert_called_with({
            'text': 'the-outbound-reply'
        })

    @inlineCallbacks
    def test_send_rtm(self):
        mock_protocol = Mock()
        mock_protocol.send_message = Mock()
        mock_protocol.send_message.return_value = None

        url, r = yield self.mk_relay()
        r.get_protocol = Mock()
        r.get_protocol.return_value = succeed(mock_protocol)

        yield treq.post(
            '%s/rtm' % (url,),
            data=json.dumps({'foo': 'bar'}),
            auth=('bot-id', 'bot-token'),
            pool=self.pool)
        mock_protocol.send_message.assert_called_with({
            'foo': 'bar'
        })
        r.get_protocol.assert_called_with(bot_id='bot-id',
                                          bot_token='bot-token')

    def test_protocol_relay(self):
        relay = Mock()
        relay.relay = Mock()

        protocol = RelayProtocol({
            'self': {
                'id': 'the-user-id',
            }
        })
        protocol.relay = relay
        protocol.bot_user_id = 'the-user-id'
        protocol.onMessage('{"foo": "bar"}', False)
        relay.relay.assert_called_with('the-user-id', {"foo": "bar"})

    @inlineCallbacks
    def test_protocol_close(self):
        _, r = yield self.mk_relay()

        protocol = RelayProtocol({
            'self': {
                'id': 'the-user-id',
            },
        })
        protocol.factory = Mock()
        protocol.bot_user_id = 'bot-user-id'
        protocol.relay = r

        r.set_protocol('bot-user-id', protocol)

        protocol.onClose(True, None, None)
        self.assertEqual(r.connections, {})

    def test_ping(self):
        protocol = RelayProtocol({
            'self': {
                'id': 'the-user-id',
            },
        })
        protocol.clock = Clock()
        protocol.factory = Mock()
        protocol.sendMessage = Mock()

        protocol.onOpen()
        protocol.clock.advance(3)
        protocol.sendMessage.assert_has_calls([
            call('{"type": "ping"}'),
            call('{"type": "ping"}')])

    def test_factory(self):
        factory = RelayFactory('dummy relay', {
            'url': 'wss://foo/',
            'self': {
                'id': 'bot-user-id'
            }
        })
        protocol = factory.buildProtocol('addr')
        self.assertEqual(protocol.factory, factory)
        self.assertEqual(protocol.bot_user_id, 'bot-user-id')
