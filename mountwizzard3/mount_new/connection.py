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


class Connection(object):
    """
    The class Command provides the command and reply interface to a 10 micron mount.
    There should be all commands and their return values be sent to the mount via
    IP and the responses parsed accordingly.

    Define the number of chunks for the return bytes in case of not having them in
    bulk mode this is needed, because the mount computer  doesn't support a
    transaction base like number of chunks to be expected. It's just plain data and
    I have to find out myself how much it is. there are three types of commands:

          a) no reply               this is ok -> COMMAND_A
          b) reply without '#'      this is the bad part, don't like it -> COMMAND_B
          c) reply ended with '#'   this is normal feedback -> no special treatment

    The class itself need parameters for the host and port to be able to interact
    with the mount. In addition it needs classes, where the settings, firmware and
    site parameters are handled.

        >>> command = Connection(
        >>>                   host='mount.fritz.box',
        >>>                   port=3492,
        >>>                   firmware=firmware,
        >>>                   setting=setting,
        >>>                   site=site,
        >>>                   )

    """

    version = '0.1'

    # I don't want so wait to long for a response. In average I see values
    # shorter than 0.5 sec, so 2 seconds should be good
    SOCKET_TIMEOUT = 2

    # Command list for commands which don't reply anything
    COMMAND_A = [':AP', ':AL', ':hP', ':PO', ':RT0', ':RT1', ':RT2', ':RT9', ':STOP', ':U2',
                 ':hS', ':hF', ':hP', ':KA', ':Me', ':Mn', ':Ms', ':Mw', ':EW', ':NS', ':Q',
                 'Suaf', ':TSOLAR', ':TQ']

    # Command list for commands which have a response, but have no end mark
    # mostly these commands response value of '0' or '1'
    COMMAND_B = [':FLIP', ':shutdown', ':GREF', ':GSC', ':Guaf', ':GTMPLT', ':GTRK',
                 ':GTTRK', ':GTsid', ':MA', ':MS', ':Sa', ':Sev', ':Sr', ':SREF', ':SRPRS',
                 ':SRTMP', ':Slmt', ':Slms', ':St', ':Sw', ':Sz', ':Sdat', ':Gdat']

    def __init__(self,
                 host='192.168.2.15',
                 port=3492,
                 firmware=None,
                 setting=None,
                 site=None,
                 ):

        self.host = host
        self.port = port
        self.firmware = firmware
        self.setting = setting
        self.site = site

    def _analyseCommand(self, commandString):
        """
        analyseCommand parses the provided commandString against the two command
        type A and B to evaluate if a response is expected and how many chunks of
        data show be received.

        :param commandString:       string sent to the mount
        :return: chunksToReceive:   counted chunks
                 noResponse:        True, if we should not wait for receiving data
        """
        chunksToReceive = 0
        noResponse = True
        commandSet = commandString.split('#')[:-1]
        for command in commandSet:
            foundCOMMAND_A = False
            for key in self.COMMAND_A:
                if command.startswith(key):
                    foundCOMMAND_A = True
                    break
            if not foundCOMMAND_A:
                noResponse = False
                for keyBad in self.COMMAND_B:
                    if command.startswith(keyBad):
                        break
                else:
                    chunksToReceive += 1
        return chunksToReceive, noResponse

    def _communicate(self, commandString):
        """
        transfer open a socket to the mount, takes the command string for the mount,
        send it to the mount. If response expected, wait for the response and returns
        the data.

        :param commandString:
        :return: success:           True or False for full transfer
                 message:           resulting text message what happened
                 response:          the data load
                 numberOfChunks:    number of responses delimited with #
        """

        # analysing the command
        numberOfChunks, noResponse = self._analyseCommand(commandString)

        # build client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(self.SOCKET_TIMEOUT)
        response = ''
        message = 'ok'
        try:
            client.connect((self.host, self.port))
        except socket.timeout:
            message = 'socket error timeout connect'
            client.close()
            return False, message, response, numberOfChunks
        except socket.error:
            message = 'socket error general connect'
            client.close()
            return False, message, response, numberOfChunks
        # send data
        try:
            client.sendall(commandString.encode())
        except socket.timeout:
            message = 'socket error timeout send'
            client.close()
            return False, message, response, numberOfChunks
        except socket.error:
            message = 'socket error general send'
            client.close()
            return False, message, response, numberOfChunks
        # receive data
        try:
            while True:
                if noResponse:
                    break
                chunk = client.recv(4096).decode().strip()
                if not chunk:
                    break
                response += chunk
                if response.count('#') == numberOfChunks:
                    break
        except socket.timeout:
            message = 'socket error timeout response'
            response = ''
            return False, message, response, numberOfChunks
        except socket.error:
            message = 'socket error general response'
            response = ''
            return False, message, response, numberOfChunks
        else:
            response = response.split('#')[:-1]
            return True, message, response, numberOfChunks
        finally:
            client.close()
