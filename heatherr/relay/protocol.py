from autobahn.twisted.websocket import (
    WebSocketClientProtocol, WebSocketClientFactory, connectWS)


class RTMProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        print("Server connected!!!!!: {0}".format(response.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))


class RTMFactory(WebSocketClientFactory):
    protocol = RTMProtocol
