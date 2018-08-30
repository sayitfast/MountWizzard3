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
import logging
# external packages
# local imports
from .connection import Connection


class Command(object):
    """
    The class Command provides the abstracted command and reply interface to a 10 micron
    mount.
    There should be all commands and their return values be sent to the mount via
    IP and the responses parsed accordingly.

    The class itself need parameters for the host and port to be able to interact
    with the mount. In addition it needs the storage classes, where the settings,
    firmware and site parameters are handled.

        >>> command = Command(
        >>>                   host='mount.fritz.box',
        >>>                   port=3492,
        >>>                   data=data,
        >>>                   )
    """

    __all__ = ['Command',
               'workaroundAlign',
               'pollSlow',
               'pollMed',
               'pollFast',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    def __init__(self,
                 host=None,
                 port=None,
                 data=None
                 ):

        self.host = host
        self.port = port
        self.data = data
        self.connection = Connection(self.host,
                                     self.port,
                                     )

    @staticmethod
    def _parseWorkaroundAlign(response, numberOfChunks):
        """
        Parsing the workaround command set defined by Filippo Riccio from 10micron
        to be able to access the model before having interaction with the handcontroller

        :param response:        data load from mount
               numberOfChunks:  amount of parts
        :return: success:       True if ok, False if not
                 message:       text message what happened
        """

        message = 'ok'
        if len(response) != 2 or len(response) != numberOfChunks:
            message = 'workaround command failed'
            return False, message
        if response[0] != 'V' or response[1] != 'E':
            message = 'workaround command failed'
            return False, message
        return True, message

    def workaroundAlign(self):
        """
        Sending the workaround command set defined by Filippo Riccio from 10micron
        to be able to access the model before having interaction with the handcontroller

        :return: success:   True if ok, False if not
                 message:   text message what happened
        """

        message = 'ok'
        commandString = ':newalig#:endalig#'
        suc, mes, response, chunks = self.connection.communicate(commandString)
        if not suc:
            message = mes
            return False, message
        suc, mes = self._parseWorkaroundAlign(response, chunks)
        if suc:
            return True, message
        else:
            message = mes
            return False, message

    def _parseSlow(self, response, numberOfChunks):
        """
        Parsing the polling slow command.

        :param response:        data load from mount
               numberOfChunks:  amount of parts
        :return: success:       True if ok, False if not
                 message:       text message what happened
        """

        message = 'ok'
        if len(response) != 8 or len(response) != numberOfChunks:
            message = 'wrong number of chunks'
            return False, message
        # doing observer settings update
        try:
            elev = response[0]
            # due to compatibility to LX200 protocol east is negative, so we change that
            if response[1] == '-':
                lon = response[1].replace('-', '+')
            else:
                lon = response[1].replace('+', '-')
            lat = response[2]
            # storing it to the skyfield Topos unit
            self.data.site.location = [lat, lon, elev]
        except Exception as e:
            message = e
            return False, message
        finally:
            pass

        # doing version settings update
        try:
            self.data.fw.fwdate = response[3]
            self.data.fw.numberString = response[4]
            self.data.fw.productName = response[5]
            self.data.fw.fwtime = response[6]
            self.data.fw.hwVersion = response[7]
        except Exception as e:
            message = e
            return False, message
        finally:
            pass
        return True, message

    def pollSlow(self):
        """
        Sending the polling slow command. As the mount need polling the data, I send
        a set of commands to get the data back to be able to process and store it.

        :return: success:   True if ok, False if not
                 message:   text message what happened
        """

        message = 'ok'
        commandString = ':U2#:Gev#:Gg#:Gt#:GVD#:GVN#:GVP#:GVT#:GVZ#'
        suc, mes, response, chunks = self.connection.communicate(commandString)
        if not suc:
            message = mes
            return False, message
        suc, mes = self._parseSlow(response, chunks)
        if not suc:
            message = mes
            return False, message
        return True, message

    def _parseMed(self, response, numberOfChunks):
        """
        Parsing the polling med command.

        :param response:        data load from mount
               numberOfChunks:  amount of parts
        :return: success:       True if ok, False if not
                 message:       text message what happened
        """

        message = 'ok'
        if len(response) != 13 or len(response) != numberOfChunks:
            message = 'wrong number of chunks'
            return False, message

        self.data.setting.slewRate = response[0]
        self.data.setting.timeToFlip = response[1]
        self.data.setting.meridianLimitGuide = response[2]
        self.data.setting.meridianLimitSlew = response[3]
        self.data.setting.refractionTemperature = response[4]
        self.data.setting.refractionPressure = response[5]
        self.data.setting.TrackingRate = response[6]
        self.data.setting.TelescopeTempDEC = response[7]
        self.data.setting.statusRefraction = (response[8][0] == '')
        self.data.setting.statusUnattendedFlip = (response[8][1] == '')
        self.data.setting.statusDualAxisTracking = (response[8][2] == '')
        self.data.setting.currentHorizonLimitHigh = response[8][3:6]
        self.data.setting.currentHorizonLimitLow = response[9][0:3]
        if self.data.fw.checkNewer(21500):
            valid, expirationDate = response[12].split(',')
            self.data.setting.UTCDataValid = (valid == 'V')
            self.data.setting.UTCDataExpirationDate = expirationDate
        self.data.model.numberModelNames = response[10]
        self.data.model.numberAlignmentStars = response[11]

        return True, message

    def pollMed(self):
        """
        Sending the polling med command. As the mount need polling the data, I send
        a set of commands to get the data back to be able to process and store it.

        :return: success:   True if ok, False if not
                 message:   text message what happened
        """

        message = 'ok'
        cs1 = ':GMs#:Gmte#:Glmt#:Glms#:GRTMP#:GRPRS#:GT#:GTMP1#:GREF#:Guaf#'
        cs2 = ':Gdat#:Gh#:Go#:modelcnt#:getalst#'
        cs3 = ':GDUTV#'
        if self.data.fw.checkNewer(21500):
            commandString = ''.join((cs1, cs2, cs3))
        else:
            commandString = ''.join((cs1, cs2))
        suc, mes, response, chunks = self.connection.communicate(commandString)
        if not suc:
            message = mes
            return False, message
        suc, mes = self._parseMed(response, chunks)
        if not suc:
            message = mes
            return False, message
        return True, message

    def _parseFast(self, response, numberOfChunks):
        """
        Parsing the polling fast command.

        :param response:        data load from mount
               numberOfChunks:  amount of parts
        :return: success:       True if ok, False if not
                 message:       text message what happened
        """

        message = 'ok'
        if len(response) != 2 or len(response) != numberOfChunks:
            message = 'wrong number of chunks'
            return False, message

        self.data.site.timeSidereal = response[0]
        responseSplit = response[1].split(',')
        self.data.site.raJNow = responseSplit[0]
        self.data.site.decJNow = responseSplit[1]
        self.data.site.pierside = responseSplit[2]
        self.data.site.apparentAz = responseSplit[3]
        self.data.site.apparentAlt = responseSplit[4]
        self.data.site.timeJD = responseSplit[5]
        self.data.site.status = responseSplit[6]
        self.data.site.statusSlew = (responseSplit[7] == '1')

        return True, message

    def pollFast(self):
        """
        Sending the polling fast command. As the mount need polling the data, I send
        a set of commands to get the data back to be able to process and store it.

        :return: success:   True if ok, False if not
                 message:   text message what happened
        """

        message = 'ok'
        commandString = ':U2#:GS#:Ginfo#:'
        suc, mes, response, chunks = self.connection.communicate(commandString)
        if not suc:
            message = mes
            return False, message
        suc, mes = self._parseFast(response, chunks)
        if not suc:
            message = mes
            return False, message
        return True, message
