############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017
#
# Licence APL2.0
#
############################################################

# import basic stuff
import logging
import threading
import socket
import time

from tkinter import *
# matplotlib
import matplotlib
#matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.image as img
import numpy as np

class Handcontroller:
    logger = logging.getLogger(__name__)                                                                                    # enable logging
    PORT = 3491
    MOUNTIP = '192.168.2.15'

    def __init__(self, app):
        self.app = app
        self.connected = False
        self.socket = None
        self.value_azimuth = 0
        self.value_altitude = 0
        self.sendCommandLock = threading.Lock()

    def mountIP(self):
        # value = self.app.ui.le_mountIP.text().split('.')
        value = '192.168.2.15'.split('.')
        if len(value) != 4:
            self.logger.error('formatIP       -> wrong input value:{0}'.format(value))
            self.app.messageQueue.put('Wrong IP configuration for mount, please check!')
            return
        v = []
        for i in range(0, 4):
            v.append(int(value[i]))
        ip = '{0:d}.{1:d}.{2:d}.{3:d}'.format(v[0], v[1], v[2], v[3])
        return ip

    def connect(self):                                                                                                      # runnable of the thread
        try:
            if self.socket is None:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(60)
            self.socket.connect((self.MOUNTIP, self.PORT))
            self.connected = True                                                                                           # setting connection status from driver
        except Exception as e:                                                                                              # error handling
            self.logger.error('connect TCP    -> Socket connect error: {0}'.format(e))                                      # to logger
            self.socket = None
            self.connected = False                                                                                          # connection broken
        finally:                                                                                                            # we don't stop, but try it again
            pass

    def disconnect(self):
        try:
            self.connected = False
            if self.socket:
                self.socket.shutdown(1)
                self.socket.close()
                self.socket = None
        except Exception as e:                                                                                              # error handling
            self.logger.error('disconnect TCP -> Socket disconnect error: {0}'.format(e))                                   # to logger
            self.connected = False                                                                                          # connection broken
        finally:                                                                                                            # we don't stop, but try it again
            pass

    def commandBlind(self, command):
        totalSent = 0
        command = (':' + command + '#').encode()
        try:
            while totalSent < len(command):
                sent = self.socket.send(command[totalSent:])
                if sent == 0:
                    raise RuntimeError("Socket connection broken")
                totalSent = totalSent + sent
        except Exception as e:                                                                                              # error handling
            self.logger.error('commandBlind   -> Socket send error: {0}'.format(e))                                         # to logger
            self.disconnect()                                                                                               # connection broken
        finally:                                                                                                            # we don't stop, but try it again
            pass

    def commandString(self, command):
        self.commandBlind(command)
        try:
            chunks = []
            while True:
                chunk = self.socket.recv(1024)
                if chunk == b'':
                    raise RuntimeError("Socket connection broken")
                chunks.append(chunk)
                if chunk[len(chunk)-1] == 3:
                    break
        except Exception as e:                                                                                              # error handling
            self.logger.error('commandBlind   -> Socket receive error: {0}'.format(e))                                      # to logger
            self.disconnect()                                                                                               # connection broken
        finally:                                                                                                            # we don't stop, but try it again
            # noinspection PyUnboundLocalVariable
            print(chunks)
            print(type(chunks))
            print(len(chunks))
            return chunks


if __name__ == "__main__":

    a = Handcontroller(None)
    a.connect()
    matplotlib.interactive(True)
    while True:
        test = np.array(a.commandString('GS'))
        b = np.reshape(test, (256, 128))
        # test = np.zeros((256, 128))
        plt.imshow(b)
        break
    time.sleep(3)
    a.disconnect()
