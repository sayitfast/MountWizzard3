############################################################
# -*- coding: utf-8 -*-
#
#       #   #  #   #   #  ####
#      ##  ##  #  ##  #     #
#     # # # #  # # # #     ###
#    #  ##  #  ##  ##        #
#   #   #   #  #   #     ####
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.6.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
############################################################
import socket
import sys

import PyQt5.QtCore
import skyfield.api

from .configData import Setting
from .configData import Firmware


class MountCommand:

    versionLock = PyQt5.QtCore.QReadWriteLock()
    observerLock = PyQt5.QtCore.QReadWriteLock()
    mountTimeLock = PyQt5.QtCore.QReadWriteLock()
    settingsLock = PyQt5.QtCore.QReadWriteLock()

    SOCKET_TIMEOUT = 1.5

    # define the number of chunks for the return bytes in case of not having them in bulk mode
    # this is needed, because the mount computer  doesn't support a transaction base like
    # number of chunks to be expected. it's just plain data and i have to find out myself how
    # much it is. there are three types of commands:
    #       a) no reply                     this is ok -> COMMAND_A
    #       b) reply without '#'            this is the bad part, don't like it -> COMMAND_B
    #       c) reply ended with '#'         this is normal feedback -> no special treatment

    COMMAND_A = [':AP', ':AL', ':hP', ':PO', ':RT0', ':RT1', ':RT2', ':RT9', ':STOP', ':U2',
                 ':hS', ':hF', ':hP', ':KA', ':Me', ':Mn', ':Ms', ':Mw', ':EW', ':NS', ':Q',
                 'Suaf', ':TSOLAR', ':TQ']

    COMMAND_B = [':FLIP', ':shutdown', ':GREF', ':GSC', ':Guaf', ':GTMPLT', ':GTRK',
                 ':GTTRK', ':GTsid', ':MA', ':MS', ':Sa', ':Sev', ':Sr', ':SREF', ':SRPRS',
                 ':SRTMP', ':Slmt', ':Slms', ':St', ':Sw', ':Sz', ':Sdat', ':Gdat']

    firmware = Firmware(0)

    observer = None

    mountTime = {}

    settings = Setting()

    def __init__(self, host='192.168.2.15', port=3492):
        self.host = host
        self.port = port

    def analyseCommand(self, commandString):
        chunksToReceive = 0
        commandSet = commandString.split('#')[:-1]

        for command in commandSet:
            foundCOMMAND_A = False
            for key in self.COMMAND_A:
                if command.startswith(key):
                    foundCOMMAND_A = True
                    break
            if not foundCOMMAND_A:
                chunksToReceive += 1
                for keyBad in self.COMMAND_B:
                    if command.startswith(keyBad):
                        break
        return chunksToReceive

    def commandSend(self, command):
        numberOfChunks = self.analyseCommand(command)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(self.SOCKET_TIMEOUT)
        response = ''
        message = 'ok'

        try:
            client.connect((self.host, self.port))
        except socket.timeout:
            message = 'socket timeout connect'
            client.close()
            return False, message, response
        except socket.error:
            message = 'socket error connect'
            client.close()
            return False, message, response

        try:
            client.sendall(command.encode())
        except socket.timeout:
            message = 'socket timeout send'
            client.close()
            return False, message, response
        except socket.error:
            message = 'socket error send'
            client.close()
            return False, message, response

        try:
            while True:
                chunk = client.recv(4096).decode().strip()
                if not chunk:
                    break
                response += chunk
                if response.count('#') == numberOfChunks:
                    break
        except socket.timeout:
            message = 'socket timeout response'
            return False, message, response
        except socket.error:
            message = 'socket error response'
            return False, message, response
        else:
            return True, message, response
        finally:
            client.close()

    @staticmethod
    def parseWorkaroundAlign(response):
        message = 'ok'
        value = response.split('#')[:-1]
        if value[0] == 'V' and value[1] == 'E':
            return True, message
        else:
            message = 'workaround failed'
            return False, message

    def workaroundAlign(self):
        message = 'ok'
        commandString = ':newalig#:endalig#'
        suc, mes, response = self.commandSend(commandString)
        if not suc:
            message = mes
            return False, message
        suc, mes = self.parseWorkaroundAlign(response)
        if suc:
            return True, message
        else:
            message = mes
            return False, message

    def parseSlow(self, response):
        message = 'ok'
        value = response.split('#')[:-1]

        if len(value) != 8:
            message = 'wrong number of parameters'
            return False, message

        # doing observer settings update
        self.observerLock.lockForWrite()

        # due to compatibility to LX200 protocol east is negative, so we change that
        if value[1] == '-':
            lon = value[1].replace('-', '+')
        else:
            lon = value[1].replace('+', '-')
        lon = [float(x) for x in lon.split(':')]
        lon = lon[0] + lon[1] / 60 + lon[2] / 3600
        lon = skyfield.api.Angle(degrees=lon)
        lat = [float(x) for x in value[2].split(':')]
        lat = lat[0] + lat[1] / 60 + lat[2] / 3600
        lat = skyfield.api.Angle(degrees=lat)
        elev = float(value[0])

        # storing it to the skyfield Topos unit
        self.observer = skyfield.api.Topos(longitude=lon,
                                           latitude=lat,
                                           elevation_m=elev)
        self.observerLock.unlock()

        # doing version settings update
        self.versionLock.lockForWrite()
        if len(value[3]) > 0:
            self.version['FirmwareDate'] = value[3]
        if len(value[4]) > 0:
            self.version['FirmwareNumber'] = value[4]
            fw = self.version['FirmwareNumber'].split('.')
            if len(fw) == 3:
                self.version['FW'] = int(
                    float(fw[0]) * 10000 + float(fw[1]) * 100 + float(fw[2]))
            else:
                self.version['FW'] = 0
        if len(value[5]) > 0:
            self.version['FirmwareProductName'] = value[5]
        if len(value[6]) > 0:
            self.version['FirmwareTime'] = value[6]
        if len(value[7]) > 0:
            self.version['HardwareVersion'] = value[7]
        self.versionLock.unlock()

        return True, message

    def pullSlow(self):
        message = 'ok'
        commandString = ':U2#:Gev#:Gg#:Gt#:GVD#:GVN#:GVP#:GVT#:GVZ#'
        suc, mes, response = self.commandSend(commandString)
        if not suc:
            message = mes
            return False, message
        suc, mes = self.parseSlow(response)
        if not suc:
            message = mes
            return False, message
        return True, message

    def pullMed(self):
        message = 'ok'
        commandString = ':GMs#:Gmte#:Glmt#:Glms#:GRTMP#:GRPRS#:GT#:U2#:GTMP1#:GREF#:Guaf#:Gdat#:Gh#:Go#:modelcnt#:getalst#'
        commandString = ':GMs#:Gmte#:Glmt#:Glms#:GRTMP#:GRPRS#:GT#:U2#:GTMP1#:GREF#:Guaf#:Gdat#:Gh#:Go#:modelcnt#:getalst#:GDUTV#'
        return True, message

    def pullFast(self):
        message = 'ok'
        commandString = ':U2#:GS#:Ginfo#:'
        return True, message
