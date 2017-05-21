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
                print(chunk)
                if chunk[len(chunk)-1] == 3:
                    break
        except Exception as e:                                                                                              # error handling
            self.logger.error('commandBlind   -> Socket receive error: {0}'.format(e))                                      # to logger
            self.disconnect()                                                                                               # connection broken
        finally:                                                                                                            # we don't stop, but try it again
            # noinspection PyUnboundLocalVariable
            return chunks


if __name__ == "__main__":

    test = b'\x02\x00\x80\xc0\xa0\x91\x82\x85\xd8\xf4\x90\x8a\xe6\xc3\xc6\xfc\xe0\xb1\x93\xcc\x86\xf2\x91\x80\xc0\xf6\x03\x02\x00\x80\xc0\xa0\xa1\x82\xc1\xde\xec\xb0\xdc\xc4\x86\x8b\xb1\xd2\xe7\xb7\x88\x8c\xd7\x93\xc8\xdc\xf0\x03\x02\x00\x80\xc0\xa0\xb1\x81\xc0\xe0\xb0\xef\xcc\x86\x92\xb9\xc8\xf0\xa2\x90\x88\x84\x82\x81\x80\xc0\x89\x03\x02\x00\x80\xc0\xa0\xc1\x82\xc1\x82\xa0\x99\x8c\xe6\x9d\xf9\xd0\xe0\xa7\x90\x88\x84\x82\x81\x80\xc0\x9d\x03\x02\x00\x80\xc0\xa0\xd1\x82\xd1\xde\xa0\xb1\xd9\xad\xe7\xa3\xc9\xca\xa0\xb8\x9b\xed\xc2\x83\x85\xf0\xc6\x03\x02\x00\x83\x80\x0b\x03\x02\x00\x8b\x9b\x80\x92\x03\x02\x00\x83\xc0\x9f\xf0.\x03\x02\x00\x83\xff\xe7\xf0i\x03'
    #a = Handcontroller(None)
    #a.connect()
    matplotlib.interactive(True)
    while True:
        #test = np.array(a.commandString('GS'))
        # b = np.reshape(test, (256, 128))
        b = np.zeros((256, 128))

        plt.imshow(b)
        break
    # time.sleep(3)
    # a.disconnect()
