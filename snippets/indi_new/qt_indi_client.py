#!/usr/bin/env python
"""
A PyQt5 (client) interface to an INDI server. This will only work
in the context of a PyQt application.
"""

from xml.etree import ElementTree
from PyQt5 import QtCore, QtNetwork

import snippets.indi_new.indi_xml as indiXML


class QtINDIClientException(Exception):
    pass


class QtINDIClient(QtCore.QObject):
    received = QtCore.pyqtSignal(object)  # Received messages as INDI Python objects.

    def __init__(self,
                 host='192.168.2.164',
                 port=7624,
                 verbose=True,
                 **kwds):
        super().__init__(**kwds)

        self.device = None
        self.message_string = ""
        self.host = host
        self.port = port
        self.connected = False

        # Create socket.
        self.socket = QtNetwork.QTcpSocket()
        self.socket.disconnected.connect(self.handleDisconnect)
        self.socket.readyRead.connect(self.handleReadyRead)

        self.socket.hostFound.connect(self.handleHostFound)
        self.socket.connected.connect(self.handleConnected)
        self.socket.stateChanged.connect(self.handleStateChanged)
        self.socket.error.connect(self.handleError)

        # if not self.socket.waitForConnected():
        #    print("Cannot connect to indiserver at " + address + ", port " + str(port))

    def handleDisconnect(self):
        print('handleDisconnect')
        self.connected = False
        self.socket.disconnectFromHost()

    def handleHostFound(self):
        print('handleHostFound')

    def handleConnected(self):
        print('handleConnected')
        print("Connect to indiserver at " + self.host + ", port " + str(self.port))
        self.connected = True

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

    def handleReadyRead(self):

        # Add starting tag if this is new message.
        if (len(self.message_string) == 0):
            self.message_string = "<data>"

        # Get message from socket.
        while self.socket.bytesAvailable():
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
                    if (self.device == xml_message.getAttr("device")):
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
        if (self.socket.state() == QtNetwork.QAbstractSocket.ConnectedState):
            self.socket.write(indi_command.toXML() + b'\n')
        else:
            print("Socket is not connected.")


if (__name__ == "__main__"):

    import sys
    import time

    from PyQt5 import QtWidgets


    class Widget(QtWidgets.QWidget):

        def __init__(self):
            QtWidgets.QWidget.__init__(self)

            self.client = QtINDIClient()
            self.client.received.connect(self.handleReceived)

        def handleReceived(self, message):
            print(message)

        def send(self, message):
            self.client.sendMessage(message)


    app = QtWidgets.QApplication(sys.argv)
    widget = Widget()
    widget.show()

    # Get a list of devices.
    # widget.send(indiXML.clientGetProperties(indi_attr={"version": "1.0"}))

    # Connect to the CCD simulator.
    # widget.send(indiXML.newSwitchVector([indiXML.oneSwitch("On", indi_attr={"name": "CONNECT"})], indi_attr={"name": "CONNECTION", "device": "CCD Simulator"}))

    while True:
        time.sleep(1)
        QtWidgets.QApplication.processEvents()
        if not widget.client.connected and widget.client.socket.state() == 0:
            print('try to connect to', widget.client.host)
            widget.client.socket.connectToHost(widget.client.host, widget.client.port)
        # Enable BLOB mode.
        # widget.send(indiXML.enableBLOB("Also", indi_attr={"device": "CCD Simulator"}))

        # Request image.
        # widget.send(indiXML.newNumberVector([indiXML.oneNumber(1, indi_attr={"name": "CCD_EXPOSURE_VALUE"})], indi_attr={"name": "CCD_EXPOSURE", "device": "CCD Simulator"}))

    sys.exit(app.exec_())