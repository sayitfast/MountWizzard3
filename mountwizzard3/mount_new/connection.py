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
# standard libraries
import socket
import logging
# external packages
# local imports


class Connection(object):
    """
    The class Connection provides the command and reply interface to a 10 micron mount.
    There should be all commands and their return values be sent to the mount via
    IP and the responses.

    Define the number of chunks for the return bytes in case of not having them in
    bulk mode this is needed, because the mount computer  doesn't support a
    transaction base like number of chunks to be expected. It's just plain data and
    I have to find out myself how much it is. there are three types of commands:

          a) no reply               this is ok -> COMMAND_A
          b) reply without '#'      this is the bad part, don't like it -> COMMAND_B
          c) reply ended with '#'   this is normal feedback -> no special treatment

    The class itself need parameters for the host and port to be able to interact
    with the mount.

        >>> command = Connection(
        >>>                   host=('mount.fritz.box', 3492),
        >>>                   )

    """

    __all__ = ['Connection',
               'communicate']
    version = '0.1'
    logger = logging.getLogger(__name__)

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
                 ':SRTMP', ':Slmt', ':Slms', ':St', ':Sw', ':Sz', ':Sdat', ':Gdat',
                 ':So', ':Sh']

    def __init__(self,
                 host=None,
                 ):

        self.host = host

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

    def communicate(self, commandString):
        """
        transfer open a socket to the mount, takes the command string for the mount,
        send it to the mount. If response expected, wait for the response and returns
        the data.

        :param commandString:
        :return: success:           True or False for full transfer
                 response:          the data load
                 numberOfChunks:    number of responses delimited with #
        """

        # analysing the command
        numberOfChunks, noResponse = self._analyseCommand(commandString)
        self.logger.debug('com: {0}, resp: {1}, chunks: {2}'.format(commandString,
                                                                    noResponse,
                                                                    numberOfChunks))
        self.logger.debug('host: {0}'.format(self.host))

        # test if we have valid parameters
        response = ''
        if not self.host:
            message = 'no host defined'
            self.logger.warning('{0}'.format(message))
            return False, response, numberOfChunks
        if not isinstance(self.host, tuple):
            message = 'host entry malformed'
            self.logger.warning('{0}'.format(message))
            return False, response, numberOfChunks

        # build client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(self.SOCKET_TIMEOUT)
        try:
            client.connect(self.host)
        except socket.timeout:
            message = 'socket error timeout connect'
            client.close()
            self.logger.error('{0}'.format(message))
            return False, response, numberOfChunks
        except socket.error:
            message = 'socket error general connect'
            client.close()
            self.logger.error('{0}'.format(message))
            return False, response, numberOfChunks
        except Exception as e:
            client.close()
            self.logger.error('{0}'.format(e))
            return False, response, numberOfChunks

        # send data
        try:
            client.sendall(commandString.encode())
        except socket.timeout:
            message = 'socket error timeout send'
            client.close()
            self.logger.error('{0}'.format(message))
            return False, response, numberOfChunks
        except socket.error:
            message = 'socket error general send'
            client.close()
            self.logger.error('{0}'.format(message))
            return False, response, numberOfChunks
        except Exception as e:
            client.close()
            self.logger.error('{0}'.format(e))
            return False, response, numberOfChunks

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
            self.logger.error('{0}'.format(message))
            return False, response, numberOfChunks
        except socket.error:
            message = 'socket error general response'
            response = ''
            self.logger.error('{0}, response: {1}'.format(message, response))
            return False, response, numberOfChunks
        except Exception as e:
            response = ''
            self.logger.error('{0}, response: {1}'.format(e, response))
            return False, response, numberOfChunks
        else:
            response = response.rstrip('#').split('#')
            self.logger.debug('{0}'.format(response))
            return True, response, numberOfChunks
        finally:
            client.close()
