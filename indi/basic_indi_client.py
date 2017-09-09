#!/usr/bin/env python
# changes by Michael Würtenberger 08/2017
# due to PEP8 coding style
"""
A basic INDI client.

Hazen 02/17

"""

import socket
import time
from xml.etree import ElementTree

import indi.indi_xml as indiXML


class BasicIndiClient(object):

    def __init__(self, ip_address, port, timeout=0.5):
        socket.setdefaulttimeout(timeout)
        self.a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.a_socket.connect((ip_address, port))
        self.device = None
        self.message_string = None
        self.timeout = 0.1

    def close(self):
        self.a_socket.close()

    def getMessages(self):
        """
        This will return 'None' if there were no messages, or no complete
        messages. The expectation is that this will then be called again
        after some timeout to get the rest of message.
        """
        # Add starting tag if this is a new message.
        if self.message_string is None:
            self.message_string = "<data>"
        # Get as much data as we can from the socket.
        try:
            while True:
                response = self.a_socket.recv(2**20)
                self.message_string += response.decode("latin1")
        except socket.timeout:
            pass
        # Add closing tag.
        self.message_string += "</data>"
        # Try and parse the message.
        messages = None
        try:
            etree_messages = ElementTree.fromstring(self.message_string)
            self.message_string = None
            messages = []
            for etree_message in etree_messages:
                xml_message = indiXML.parseETree(etree_message)
                # Filter message is self.device is not None.
                if self.device is not None:
                    if self.device == xml_message.getAttr("device"):
                        messages.append(xml_message)
                # Otherwise just keep them all.
                else:
                    messages.append(xml_message)

        # Reset if the message could not be parsed.
        except ElementTree.ParseError:
            self.message_string = self.message_string[:-len("</data>")]
        return messages

    def sendMessage(self, indi_elt):
        self.a_socket.send(indi_elt.toXML() + b'\n')

    def setDevice(self, device=None):
        self.device = device

    def waitMessages(self):
        """
        This will block until all messages are received.

        FIXME: Add maximum wait time / attempts?
        """
        messages = self.getMessages()
        while messages is None:
            time.sleep(self.timeout)
            messages = self.getMessages()
        return messages

if __name__ == "__main__":

    import numpy
    import indi.simple_fits as simpleFits

    bic = BasicIndiClient('127.0.0.1', 7624, 3)
    device = 'CCD Simulator'
    device = 'ASCOM Simulator Camera'
    # Query device
    print("querying..")
    bic.sendMessage(indiXML.clientGetProperties(indi_attr={"version": "1.0", "device": device}))
    # Connect to user requested device.
    print("connecting..")
    bic.sendMessage(indiXML.newSwitchVector([indiXML.oneSwitch("On", indi_attr={"name": "CONNECT"})],
                                            indi_attr={"name": "CONNECTION", "device": device}))
    # Get all the XML that was sent in response to the above.
    messages = bic.waitMessages()
    # Print the messages.
    for message in messages:
        print(message)

    bic.sendMessage(indiXML.enableBLOB("Also", indi_attr={"device": device}))

    # Request a picture.
    print("Starting capture")
    bic.sendMessage(indiXML.newNumberVector([indiXML.oneNumber(3, indi_attr={"name": "CCD_EXPOSURE_VALUE"})],
                                            indi_attr={"name": "CCD_EXPOSURE", "device": device}))
    time.sleep(1)

    # Wait for image.
    print("Waiting for image")
    np_image = None
    while True:
        messages = bic.waitMessages()
        for message in messages:
            if isinstance(message, indiXML.SetBLOBVector):
                np_image = simpleFits.FitsImage(fits_string=message.getElt(0).getValue()).getImage().astype(numpy.uint16)
            else:
                print(message)
        if np_image is not None:
            break
    print('Closing connection')
    # Close the connection.
    bic.close()
