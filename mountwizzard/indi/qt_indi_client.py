# -*- coding: utf-8 -*-
"""

A PyQt5 (client) interface to an INDI server. This will only work
in the context of a PyQt application.

"""
import logging
from xml.etree import ElementTree
from PyQt5 import QtCore, QtNetwork
import indi.indi_xml as indiXML


class QtINDIClient(QtCore.QObject):
    logger = logging.getLogger(__name__)
    received = QtCore.pyqtSignal(object)

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.device = None
        self.message_string = ""
        self.socket = QtNetwork.QTcpSocket()
        self.socket.hostFound.connect(self.handleHostFound)
        self.socket.connected.connect(self.handleConnected)
        self.socket.readyRead.connect(self.handleReadyRead)
        self.socket.stateChanged.connect(self.handleStateChanged)
        self.socket.disconnected.connect(self.handleDisconnect)
        self.socket.error.connect(self.handleError)

    def connect(self, host, port):
        state = self.socket.state()
        print(state)
        if state == QtNetwork.QAbstractSocket.UnconnectedState:
            print('connectToHost')
            self.socket.connectToHost(host, port)
        if state == QtNetwork.QAbstractSocket.ConnectingState:
            pass
        if state == QtNetwork.QAbstractSocket.ConnectedState:
            pass

    def disconnect(self):
        self.socket.disconnectFromHost()

    def handleHostFound(self):
        pass

    def handleConnected(self):
        pass

    def handleError(self, socketError):
        print("The following error occurred: {0}".format(self.socket.errorString()))
        if socketError == QtNetwork.QAbstractSocket.RemoteHostClosedError:
            pass
        else:
            pass

    def handleStateChanged(self):
        print('State changed: {0}'.format(self.socket.state()))
        if self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState:
            pass
        else:
            pass

    def handleDisconnect(self):
        print('disconnected')
        self.socket.close()

    def handleReadyRead(self):
        print('read')
        # Add starting tag if this is new message.
        if len(self.message_string) == 0:
            self.message_string = "<data>"

        # Get message from socket.
        while self.socket.bytesAvailable():

            # FIXME: This does not work with Python2.
            tmp = str(self.socket.read(1000000), "ascii")
            self.message_string += tmp

        # Add closing tag.
        self.message_string += "</data>"

        # Try and parse the message.
        try:
            messages = ElementTree.fromstring(self.message_string)
            self.message_string = ""
            for message in messages:
                xml_message = indiXML.parseETree(message)

                # Filter message is self.device is not None.
                if self.device is not None:
                    if self.device == xml_message.getAttr("device"):
                        self.received.emit(xml_message)

                # Otherwise just send them all.
                else:
                    self.received.emit(xml_message)

        # Message is incomplete, remove </data> and wait..
        except ElementTree.ParseError:
            self.message_string = self.message_string[:-7]

    def setDevice(self, device=None):
        self.device = device

    def sendMessage(self, indi_command):
        if self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState:
            self.socket.write(indi_command.toXML() + b'\n')
        else:
            self.logger.warning('Socket not connected')
