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
import skyfield.api
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
        >>>                   host=('mount.fritz.box', 3492),
        >>>                   data=data,
        >>>                   )
    """

    __all__ = ['Command',
               'workaroundAlign',
               'pollSlow',
               'pollMed',
               'pollFast',
               'pollModelNames',
               'pollModelStars',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    # 10 microns have 3492 as default port
    DEFAULT_PORT = 3492

    def __init__(self,
                 host=(None, None),
                 data=None
                 ):

        self.host = host
        self.data = data

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        # checking format
        if not value:
            self._host = None
            self.logger.error('wrong host value: {0}'.format(value))
            return
        if not isinstance(value, (tuple, str)):
            self.logger.error('wrong host value: {0}'.format(value))
            return
        # now we got the right format
        if isinstance(value, str):
            __host = (value, self.DEFAULT_PORT)
        else:
            __host = value
        self._host = __host

    def _parseWorkaroundAlign(self, response, numberOfChunks):
        """
        Parsing the workaround command set defined by Filippo Riccio from 10micron
        to be able to access the model before having interaction with the handcontroller

        :param response:        data load from mount
               numberOfChunks:  amount of parts
        :return: success:       True if ok, False if not
        """

        if len(response) != numberOfChunks:
            self.logger.error('workaround command failed')
            return False
        if response[0] != 'V' or response[1] != 'E':
            self.logger.error('workaround command failed')
            return False
        return True

    def workaroundAlign(self):
        """
        Sending the workaround command set defined by Filippo Riccio from 10micron
        to be able to access the model before having interaction with the handcontroller

        :return: success:   True if ok, False if not
        """

        conn = Connection(self.host)
        commandString = ':newalig#:endalig#'
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        suc = self._parseWorkaroundAlign(response, chunks)
        return suc

    def _parseSlow(self, response, numberOfChunks):
        """
        Parsing the polling slow command.

        :param response:        data load from mount
               numberOfChunks:  amount of parts
        :return: success:       True if ok, False if not
        """

        if len(response) != numberOfChunks:
            self.logger.error('wrong number of chunks')
            return False
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
            self.logger.error('{0}'.format(e))
            return False
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
            self.logger.error('{0}'.format(e))
            return False
        finally:
            pass
        return True

    def pollSlow(self):
        """
        Sending the polling slow command. As the mount need polling the data, I send
        a set of commands to get the data back to be able to process and store it.

        :return: success:   True if ok, False if not
        """

        conn = Connection(self.host)
        commandString = ':U2#:Gev#:Gg#:Gt#:GVD#:GVN#:GVP#:GVT#:GVZ#'
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        suc = self._parseSlow(response, chunks)
        return suc

    def _parseMed(self, response, numberOfChunks):
        """
        Parsing the polling med command.

        :param response:        data load from mount
               numberOfChunks:  amount of parts
        :return: success:       True if ok, False if not
        """

        if len(response) != numberOfChunks:
            self.logger.error('wrong number of chunks')
            return False
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
        return True

    def pollMed(self):
        """
        Sending the polling med command. As the mount need polling the data, I send
        a set of commands to get the data back to be able to process and store it.

        :return: success:   True if ok, False if not
        """

        conn = Connection(self.host)
        cs1 = ':GMs#:Gmte#:Glmt#:Glms#:GRTMP#:GRPRS#:GT#:GTMP1#:GREF#:Guaf#'
        cs2 = ':Gdat#:Gh#:Go#:modelcnt#:getalst#'
        cs3 = ':GDUTV#'
        if self.data.fw.checkNewer(21500):
            commandString = ''.join((cs1, cs2, cs3))
        else:
            commandString = ''.join((cs1, cs2))
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        suc = self._parseMed(response, chunks)
        return suc

    def _parseFast(self, response, numberOfChunks):
        """
        Parsing the polling fast command.

        :param response:        data load from mount
               numberOfChunks:  amount of parts
        :return: success:       True if ok, False if not
        """

        if len(response) != numberOfChunks:
            self.logger.error('wrong number of chunks')
            return False
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
        return True

    def pollFast(self):
        """
        Sending the polling fast command. As the mount need polling the data, I send
        a set of commands to get the data back to be able to process and store it.

        :return: success:   True if ok, False if not
        """

        conn = Connection(self.host)
        commandString = ':U2#:GS#:Ginfo#:'
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        suc = self._parseFast(response, chunks)
        return suc

    def _parseModelNames(self, response, numberOfChunks):
        """
        Parsing the model names cluster. The command <:modelnamN#> returns:
            - the string "#" if N is not valid
            - the name of model N, terminated by the character "#"

        :param response:        data load from mount
               numberOfChunks:  amount of parts
        :return: success:       True if ok, False if not
        """

        if len(response) != numberOfChunks:
            self.logger.error('wrong number of chunks')
            return False
        for name in response:
            if not name:
                continue
            self.data.model.addName(name)
        return True

    def _parseNumberNames(self, response, numberOfChunks):
        """
        Parsing the model star number. The command <:modelcnt#> returns:
            - the string "nnn#", where nnn is the number of models available

        :param response:        data load from mount
               numberOfChunks:  amount of parts
        :return: success:       True if ok, False if not
        """

        if len(response) != numberOfChunks:
            self.logger.error('wrong number of chunks')
            return False
        self.data.model.numberNames = response[0]
        return True

    def pollModelNames(self):
        """
        Sending the polling ModelNames command. It collects for all the known names
        the string. The number of names have to be collected first, than it gathers
        all name at once.

        :return: success:   True if ok, False if not
        """

        conn = Connection(self.host)
        # alternatively we know already the number, and skip the gathering
        commandString = ':modelcnt#'
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        suc = self._parseNumberNames(response, chunks)
        if not suc:
            return False
        # now the real gathering of names
        commandString = ''
        for i in range(1, self.data.model.numberNames + 1):
            commandString += (':modelnam{0:d}#'.format(i))
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        suc = self._parseModelNames(response, chunks)
        return suc

    def _parseModelStars(self, response, numberOfChunks):
        """
        Parsing the model names cluster. The command <:getalpN#> returns:
            - the string "E#" if N is out of range
            - otherwise a string formatted as follows
                "HH:MM:SS.SS,+dd*mm:ss.s,eeee.e,ppp#"
        where
        -   HH:MM:SS.SS is the hour angle of the alignment star in hours, minutes, seconds
            and hundredths of second (from 0h to 23h59m59.99s),
        -   +dd*mm:ss.s is the declination of the alignment star in degrees, arcminutes,
            arcseconds and tenths of arcsecond, eeee.e is the error between the star and
            the alignment model in arcseconds,
        -   ppp is the polar angle of the measured star with respect to the modeled star
            in the equatorial system in degrees from 0 to 359 (0 towards the north pole,
            90 towards east)

        :param response:        data load from mount
               numberOfChunks:  amount of parts
        :return: success:       True if ok, False if not
        """

        if len(response) != numberOfChunks:
            self.logger.error('wrong number of chunks')
            return False
        for star in response:
            if not star:
                continue
            self.data.model.addStar(star)
        return True

    def _parseNumberStars(self, response, numberOfChunks):
        """
        Parsing the model star number. The command <:getalst#> returns:
            - the number of alignment stars terminated by '#'

        :param response:        data load from mount
               numberOfChunks:  amount of parts
        :return: success:       True if ok, False if not
        """

        if len(response) != numberOfChunks:
            self.logger.error('wrong number of chunks')
            return False
        self.data.model.numberStars = response[0]
        return True

    def pollModelStars(self):
        """
        Sending the polling ModelNames command. It collects for all the known names
        the string. The number of names have to be collected first, than it gathers
        all name at once.

        :return: success:   True if ok, False if not
        """

        conn = Connection(self.host)
        # alternatively we know already the number, and skip the gathering
        commandString = ':getalst#'
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        suc = self._parseNumberStars(response, chunks)
        if not suc:
            return False
        # now the real gathering of names
        commandString = ''
        for i in range(1, self.data.model.numberStars + 1):
            commandString += (':getalp{0:d}#'.format(i))
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        suc = self._parseModelStars(response, chunks)
        return suc

    def slewAltAz(self, alt, az):
        """
        Slew AltAz unpark the mount sets the targets for alt and az and then
        issue the slew command.

        the unpark command is:
            :PO#
        and returns nothing

        setting alt target is the following:
            :SzDDD*MM# or :SzDDD*MM:SS# or :SzDDD*MM:SS.S#, we use the last one
            :SzDDD*MM:SS.S#

        setting az target is the following:
            :SasDD*MM# or :SasDD*MM:SS# or :SasDD*MM:SS.S#, we use the last one
            :SasDD*MM:SS.S#

        the slew command moves the mount and keeps tracking at the end of the move.
        in the command protocol it is written, that the targets should be ra / dec,
        but it works for targets defined with alt / az commands

        the command is:
            :MS#
        and returns:
            0 no error
                if the target is below the lower limit: the string
            “1Object Below Horizon #”
                if the target is above the high limit: the string
            “2Object Below Higher #”
                if the slew cannot be performed due to another cause: the string
            “3Cannot Perform Slew #”
                if the mount is parked: the string
            “4Mount Parked #”
                if the mount is restricted to one side of the meridian and the object
                is on the other side: the string
            “5Object on the other side #”

        but we don't parse the results as it has sometimes end markers, sometimes not.

        :param alt:     altitude in type Angle
        :param az:      azimuth in type Angle
        :return:        success
        """

        if not isinstance(alt, skyfield.api.Angle):
            return False
        if not isinstance(az, skyfield.api.Angle):
            return False
        if alt.signed_dms()[0] < 0:
            return False
        conn = Connection(self.host)
        # conversion, as we only have positive alt, we set the '+' as standard.
        _altFormat = ':Sa+{0:02.0f}*{1:02.0f}:{2:04.1f}#'
        _azFormat = ':Sz{0:03.0f}*{1:02.0f}:{2:04.1f}#'
        _setAlt = _altFormat.format(*alt.dms())
        _setAz = _azFormat.format(*az.dms())
        _slew = ':MS#'
        _unpark = ':PO#'
        commandString = ''.join((_unpark, _setAlt, _setAz, _slew))
        print(commandString)
        suc, response, chunks = conn.communicate(commandString)
        return suc

    def slewRaDec(self, ra, dec):
        """
        Slew RaDec unpark the mount sets the targets for ra and dec and then
        issue the slew command.

        the unpark command is:
            :PO#
        and returns nothing

        setting ra target is the following:
            :SrHH:MM.T# or :SrHH:MM:SS# or :SrHH:MM:SS.S# or :SrHH:MM:SS.SS#
                , we use the last one
            :SrHH:MM:SS.SS#

        setting dec target is the following:
            :SdsDD*MM# or :SdsDD*MM:SS# or :Sd sDD*MM:SS.S#, we use the last one
            :SdsDD*MM:SS.S#

        the slew command moves the mount and keeps tracking at the end of the move.
        in the command protocol it is written, that the targets should be ra / dec,
        but it works for targets defined with alt / az commands

        the command is:
            :MS#
        and returns:
            0 no error
                if the target is below the lower limit: the string
            “1Object Below Horizon #”
                if the target is above the high limit: the string
            “2Object Below Higher #”
                if the slew cannot be performed due to another cause: the string
            “3Cannot Perform Slew #”
                if the mount is parked: the string
            “4Mount Parked #”
                if the mount is restricted to one side of the meridian and the object
                is on the other side: the string
            “5Object on the other side #”

        but we don't parse the results as it has sometimes end markers, sometimes not.

        :param ra:     right ascension in type Angle
        :param dec:    declination in type Angle
        :return:       success
        """

        if not isinstance(ra, skyfield.api.Angle):
            return False
        if not isinstance(dec, skyfield.api.Angle):
            return False
        conn = Connection(self.host)
        # conversion, we have to find out the sign
        if dec.signed_dms()[0] > 0:
            _sign = '+'
        else:
            _sign = '-'
        _raFormat = ':Sa+{0:02.0f}*{1:02.0f}:{2:04.1f}#'
        _decFormat = ':Sz{0:03.0f}*{1:02.0f}:{2:04.1f}#'
        _setRa = _altFormat.format(*alt.dms())
        _setDec = _azFormat.format(*az.dms())
        _slew = ':MS#'
        _unpark = ':PO#'
        commandString = ''.join((_unpark, _setRa, _setDec, _slew))
        print(commandString)
        suc, response, chunks = conn.communicate(commandString)
        return suc

    def boot(self):
        pass

    def shutdown(self):
        pass

    def setSite(self):
        pass

    def setSlewRate(self):
        pass

    def setRefractionTemperature(self):
        pass

    def setRefractionPressure(self):
        pass

    def setRefraction(self):
        pass

    def setUnattendedFlip(self):
        pass

    def setDualAxisTracking(self):
        pass

    def setMeridianLimitHigh(self):
        pass

    def setMeridianLimitLow(self):
        pass

    def setHorizonLimitHigh(self):
        pass

    def setHorizonLimitLow(self):
        pass

    def setTrackingRate(self):
        pass

    def setTracking(self):
        pass

    def park(self):
        pass

    def unpark(self):
        pass

    def stop(self):
        pass

    def flip(self):
        pass

    def clearModel(self):
        pass

    def deletePoint(self):
        pass

    def storeModel(self):
        pass

    def loadModel(self):
        pass

    def deleteModel(self):
        pass
