# -*- coding: utf-8 -*-
"""

A PyQt5 (client) interface to an INDI server. This will only work
in the context of a PyQt application.

"""
import logging
from queue import Queue
from xml.etree import ElementTree
import PyQt5
from PyQt5 import QtCore, QtNetwork, QtWidgets
import indi.indi_xml as indiXML
import time


class QtINDIClient(PyQt5.QtCore.QThread):
    logger = logging.getLogger(__name__)
    received = QtCore.pyqtSignal(object)

    def __init__(self, ekos, host, port):
        super().__init__()

        self.INDIsendQueue = Queue()
        self.device = None
        self.ekos = ekos
        self.message_string = ""
        self.socket = None
        self.host = host
        self.port = port
        self.connected = False

    def run(self):
        self.socket = QtNetwork.QTcpSocket()
        self.socket.hostFound.connect(self.handleHostFound)
        self.socket.connected.connect(self.handleConnected)
        self.socket.readyRead.connect(self.handleReadyRead)
        self.socket.stateChanged.connect(self.handleStateChanged)
        self.socket.disconnected.connect(self.handleDisconnect)
        self.socket.error.connect(self.handleError)
        self.socket.connectToHost(self.host, self.port)

        while True:
            while not self.INDIsendQueue.empty():
                indi_command = self.INDIsendQueue.get()
                self.sendMessage(indi_command)
            QtWidgets.QApplication.processEvents()
            time.sleep(0.5)
            if not self.connected and self.socket.state() == 0:
                self.socket.connectToHost(self.host, self.port)
        self.terminate()

    def stop(self):
        pass

    def handleHostFound(self):
        pass

    def handleConnected(self):
        self.connected = True
        self.ekos.runConnected()

    def handleError(self, socketError):
        print(socketError)
        self.logger.error(self.socket.errorString())

    def handleStateChanged(self):
        pass

    def handleDisconnect(self):
        self.socket.disconnectFromHost()
        self.connected = False

    def handleReadyRead(self):
        # Add starting tag if this is new message.
        if len(self.message_string) == 0:
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
