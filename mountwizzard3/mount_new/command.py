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


class MountCommand:

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

    def __init__(self, host='192.168.2.15', port=3492):

        self.host = host
        self.port = port

    def analyseCommand(self, commandString):
        chunksToReceive = 0
        commandSet = commandString.split('#')
        # the last item is empty due to split command
        commandSet = commandSet[:-1]

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
        client.settimeout(1)
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

    def commandParse(self, response):
        pass


"""
    def startCommand(self):
        if self.socket.state() == PyQt5.QtNetwork.QAbstractSocket.ConnectedState:
            command = ':U2#:Gev#:Gg#:Gt#:GVD#:GVN#:GVP#:GVT#:GVZ#:newalig#:endalig#'
            # command = ':U2#:Gev#:Gg#:Gt#:GVD#:GVN#:GVP#:GVT#:GVZ#'
            self.sendCommandQueue.put(command)
            self.doRefractionUpdate()
            self.updateAlignmentStarPositions()
            self.app.workerMountDispatcher.signalAlignmentStars.emit()

    @PyQt5.QtCore.pyqtSlot()
    def handleReadyRead(self):
        # Get message from socket.
        while self.socket.bytesAvailable() and self.isRunning:
            self.messageString += self.socket.read(1024).decode()
        if self.messageString.count('#') < 10:
            return
        if self.messageString.count('#') != 10:
            self.logger.error('Receiving data got error:{0}'.format(self.messageString))
            self.messageString = ''
            messageToProcess = ''
        else:
            messageToProcess = self.messageString
            self.messageString = ''
        # Try and parse the message. In Slow we expect 6
        try:
            if len(messageToProcess) == 0:
                return
            self.app.sharedMountDataLock.lockForWrite()
            valueList = messageToProcess.strip('#').split('#')
            # +0580.9#-011:42:17.3#+48:02:01.6#Oct 25 2017#2.15.8#10micron GM1000HPS#16:58:31#Q-TYPE2012#
            # all parameters are delivered
            self.logger.debug('Slow raw: {0}'.format(messageToProcess))
            if len(valueList) >= 8:
                if len(valueList[0]) > 0:
                    self.data['SiteHeight'] = valueList[0]
                if len(valueList[1]) > 0:
                    lon1 = valueList[1]
                    # due to compatibility to LX200 protocol east is negative
                    if lon1[0] == '-':
                        self.data['SiteLongitude'] = lon1.replace('-', '+')
                    else:
                        self.data['SiteLongitude'] = lon1.replace('+', '-')
                if len(valueList[2]) > 0:
                    self.data['SiteLatitude'] = valueList[2]
                if len(valueList[3]) > 0:
                    self.data['FirmwareDate'] = valueList[3]
                if len(valueList[4]) > 0:
                    self.data['FirmwareNumber'] = valueList[4]
                    fw = self.data['FirmwareNumber'].split('.')
                    if len(fw) == 3:
                        self.data['FW'] = int(float(fw[0]) * 10000 + float(fw[1]) * 100 + float(fw[2]))
                    else:
                        self.data['FW'] = 0
                if len(valueList[5]) > 0:
                    self.data['FirmwareProductName'] = valueList[5]
                if len(valueList[6]) > 0:
                    self.data['FirmwareTime'] = valueList[6]
                if len(valueList[7]) > 0:
                    self.data['HardwareVersion'] = valueList[7]
                self.app.signalMountSiteData.emit(self.data['SiteLatitude'], self.data['SiteLongitude'], self.data['SiteHeight'])
            else:
                self.logger.warning('Parsing Status Slow combined command valueList is not OK: length:{0} content:{1}'.format(len(valueList), valueList))
        except Exception as e:
            self.logger.error('Problem parsing response, error: {0}, message:{1}'.format(e, messageToProcess))
        finally:
            self.logger.debug('{0} processed: {1}'.format(__name__, self.data))
            self.app.sharedMountDataLock.unlock()
        self.sendLock = False
"""
