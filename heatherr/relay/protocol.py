from autobahn.twisted.websocket import (
    WebSocketClientProtocol, WebSocketClientFactory)


class RTMProtocol(WebSocketClientProtocol):
    pass


class RTMFactory(WebSocketClientFactory):
    protocol = RTMProtocol
    noisy = False
