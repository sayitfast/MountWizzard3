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


class MountIpDirect:
    logger = logging.getLogger(__name__)                                                                                    # enable logging

    def __init__(self, app):
        self.app = app
        self.connected = False                                                                                              # init of connection status
        self.value_azimuth = 0
        self.value_altitude = 0
        self.sendCommandLock = threading.Lock()

    def connect(self):                                                                                                      # runnable of the thread
        try:
            self.connected = True                                                                                           # setting connection status from driver
        except Exception as e:                                                                                              # error handling
            self.logger.error('connect Driver -> Driver COM Error in dispatchMount: {0}'.format(e))                         # to logger
            self.connected = False                                                                                          # connection broken
        finally:                                                                                                            # we don't stop, but try it again
            pass

    def disconnect(self):
        try:
            self.connected = False
        except Exception as e:                                                                                              # error handling
            self.logger.error('disconnect Driv-> Driver COM Error in dispatchMount: {0}'.format(e))                         # to logger
            self.connected = False                                                                                          # connection broken
        finally:                                                                                                            # we don't stop, but try it again
            pass

    def mountIP(self):
        value = self.app.ui.le_mountIP.text().split('.')
        if len(value) != 4:
            self.logger.error('formatIP       -> wrong input value:{0}'.format(value))
            self.app.messageQueue.put('Wrong IP configuration for mount, please check!')
            return
        v = []
        for i in range(0, 4):
            v.append(int(value[i]))
        ip = '{0:d}.{1:d}.{2:d}.{3:d}'.format(v[0], v[1], v[2], v[3])
        return ip

    def commandBlind(self, command):
        pass

    def commandString(self, command):
        return 0

    def sendCommand(self, command):                                                                                         # core routine for sending commands to mount
        reply = ''                                                                                                          # reply is empty
        self.sendCommandLock.acquire()
        if self.connected:
            try:                                                                                                            # all with error handling
                if command in ['AP', 'hP', 'PO', 'RT0', 'RT1', 'RT2', 'RT9', 'STOP', 'U2']:                                 # these are the commands, which do not expect a return value
                    self.commandBlind(command)                                                                              # than do blind command
                else:                                                                                                       #
                    reply = self.commandString(command)                                                                     # with return value do regular command
            except Exception as e:                                                                                          # error handling
                self.app.messageQueue.put('Driver COM Error in sendCommand')                                                # gui
                self.logger.error('sendCommand Mount -> error: {0} command:{1}  reply:{2} '.format(e, command, reply))      # logger
                self.connected = False                                                                                      # in case of error, the connection might be broken
            finally:                                                                                                        # we don't stop
                if len(reply) > 0:                                                                                          # if there is a reply
                    value = reply.rstrip('#').strip()                                                                       # return the value
                    if command == 'CMS':
                        self.logger.debug('sendCommand    -> Return Value Add Model Point: {0}'.format(reply))
                else:                                                                                                       #
                    if command in ['AP', 'hP', 'PO', 'RT0', 'RT1', 'RT2', 'RT9', 'STOP', 'U2']:                             # these are the commands, which do not expect a return value
                        value = ''                                                                                          # nothing
                    else:
                        value = '0'
        else:
            value = None
        self.sendCommandLock.release()
        return value
