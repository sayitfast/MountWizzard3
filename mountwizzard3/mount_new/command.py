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
import logging
import sys

import PyQt5.QtCore

from .configData import Setting
from .configData import Firmware


class Command(object):
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

        >>> command = Command(
        >>>                   host='mount.fritz.box',
        >>>                   port=3492,
        >>>                   firmware=firmware,
        >>>                   setting=setting,
        >>>                   site=site,
        >>>                   )

    """

    __all__ = ['Command',
               'workaroundAlign',
               'pollSlow',
               'pollMed',
               'pollFast',
               ]
    version = '0.2'
    logger = logging.getLogger(__name__)

    def __init__(self,
                 firmware=None,
                 setting=None,
                 site=None,
                 ):

        self.firmware = firmware
        self.setting = setting
        self.site = site

    @staticmethod
    def _parseWorkaroundAlign(response):
        """
        Parsing the workaround command set defined by Filippo Riccio from 10micron
        to be able to access the model before having interaction with the handcontroller

        :param response:    data load from mount
        :return: success:   True if ok, False if not
                 message:   text message what happened
        """

        message = 'ok'
        if len(response) != 2:
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
        suc, mes, response = self._communicate(commandString)
        if not suc:
            message = mes
            return False, message
        suc, mes = self._parseWorkaroundAlign(response)
        if suc:
            return True, message
        else:
            message = mes
            return False, message

    def _parseSlow(self, response):
        """
        Parsing the polling slow command.

        :param response:    data load from mount
        :return: success:   True if ok, False if not
                 message:   text message what happened
        """

        message = 'ok'
        if len(response) != 8:
            message = 'wrong number of chunks from mount'
            return False, message
        # doing observer settings update
        self.site.siteLock.lockForWrite()
        # conversion
        try:
            elev = float(response[0])
            # due to compatibility to LX200 protocol east is negative, so we change that
            if response[1] == '-':
                lon = response[1].replace('-', '+')
            else:
                lon = response[1].replace('+', '-')
            lat = response[2]
            # storing it to the skyfield Topos unit
            self.site.location = (lat, lon, elev)
        except Exception as e:
            message = e
            return False, message
        finally:
            self.site.siteLock.unlock()
        # doing version settings update
        self.firmware.firmwareLock.lockForWrite()
        try:
            self.firmware.fwDate = response[3]
            self.firmware.fwNumber = response[4]
            self.firmware.productName = response[5]
            self.firmware.fwTime = response[6]
            self.firmware.hwVersion = response[7]
        except Exception as e:
            message = e
            return False, message
        finally:
            self.firmware.firmwareLock.unlock()
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
        suc, mes, response = self._communicate(commandString)
        if not suc:
            message = mes
            return False, message
        suc, mes = self._parseSlow(response)
        if not suc:
            message = mes
            return False, message
        return True, message

    def _parseMed(self, response, fw):
        """
        Parsing the polling med command.

        :param response:    data load from mount
        :return: success:   True if ok, False if not
                 message:   text message what happened
        """

        message = 'ok'
        self.setting.settingLock.lockForWrite()
        self._slewRate = int(response[0])
        self._timeToFlip = int(response[1])
        self._meridianLimitGuide = int(response[2])
        self._meridianLimitSlew = int(response[3])
        self._refractionTemperature = float(response[4])
        self._refractionPressure = float(response[5])
        self._TrackingRate = float(response[6])
        self._TelescopeTempDEC = float(response[7])
        self._statusRefraction = (response[8][0] == '')
        self._statusUnattendedFlip = (response[8][1] == '')
        self._statusDualAxisTracking = (response[8][2] == '')
        self._currentHorizonLimitHigh = float(response[8][3:6])
        self._currentHorizonLimitLow = float(response[9][0:3])
        self._numberModelNames = int(response[10])
        self._numberAlignmentStars = int(response[11])
        if fw > 21500:
            valid, expirationDate = response[12].split(',')
            self._UTCDataValid = (valid == 'V')
            self._UTCDataExpirationDate = expirationDate
        self.setting.settingLock.unlock()

        return True, message

    def pollMed(self, fw):
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
        if fw > 21500:
            commandString = ''.join((cs1, cs2, cs3))
        else:
            commandString = ''.join((cs1, cs2))
        suc, mes, response = self._communicate(commandString)
        if not suc:
            message = mes
            return False, message
        suc, mes = self._parseMed(response, fw)
        if not suc:
            message = mes
            return False, message
        return True, message

    def _parseFast(self, response):
        """
        Parsing the polling fast command.

        :param response:    data load from mount
        :return: success:   True if ok, False if not
                 message:   text message what happened
        """

        message = 'ok'
        self.site.siteLock.lockForWrite()
        self.site.timeSidereal = response[0]
        responseSplit = response[1].split(',')
        self.site.raJNow = float(responseSplit[0])
        self.site.decJNow = float(responseSplit[1])
        self.site.pierside = responseSplit[2]
        self.site.apparentAz = float(responseSplit[3])
        self.site.apparentAlt = float(responseSplit[4])
        self.site.timeJD = float(responseSplit[5])
        self.site.status = int(responseSplit[6])
        self.site.statusSlew = (responseSplit[7] == '1')
        self.site.siteLock.unlock()

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
        suc, mes, response = self._communicate(commandString)
        if not suc:
            message = mes
            return False, message
        suc, mes = self._parseFast(response)
        if not suc:
            message = mes
            return False, message
        return True, message