from autobahn.twisted.websocket import (
    WebSocketClientProtocol, WebSocketClientFactory, connectWS)


class RTMProtocol(WebSocketClientProtocol):
    pass

class RTMFactory(WebSocketClientFactory):
    protocol = RTMProtocol
