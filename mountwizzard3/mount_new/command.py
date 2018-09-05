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
               'slewAltAz',
               'slewRaDec',
               'boot',
               'shutdown',
               'setSiteCoordinates',
               'setSlewRate',
               'setRefractionTemp',
               'setRefractionPress',
               'setRefraction',
               'setUnattendedFlip',
               'setDualAxisTracking',
               'setMeridianLimitTrack',
               'setMeridianLimitSlew',
               'setHorizonLimitHigh',
               'setHorizonLimitLow',
               'startTracking',
               'stopTracking',
               'setLunarTracking',
               'setSiderealTracking',
               'setSolarTracking',
               'park',
               'unpark',
               'stop',
               'flip',
               'clearModel',
               'deletePoint',
               'storeName',
               'loadName',
               'deleteName',
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

    def _parseWorkaround(self, response, numberOfChunks):
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
        suc = self._parseWorkaround(response, chunks)
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
            # in class we would like to keep the correct sign for east is positive
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
        self.data.setting.meridianLimitTrack = response[2]
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
        for number, starData in enumerate(response):
            if not starData:
                continue
            # mount counts stars from 1 beginning and adding the number (which is not provided by the response,
            # but counted in the mount computer for reference reasons
            modelStar = '{0:s}, {1}'.format(starData, number + 1)
            self.data.model.addStar(modelStar)
        return True

    def _parseNumberStars(self, response, numberOfChunks, canGetain):
        """
        Parsing the model star number. The command <:getalst#> returns:
            - the number of alignment stars terminated by '#'

        :param response:        data load from mount
               numberOfChunks:  amount of parts
               canGetain:       is this mount command supported?
        :return: success:       True if ok, False if not
        """

        if len(response) != numberOfChunks:
            self.logger.error('wrong number of chunks')
            return False
        self.data.model.numberStars = response[0]
        # if command present, we are set
        if not canGetain:
            return True
        # else we have to process the second chunk as well
        responseSplit = response[1].split(',')
        if len(responseSplit) == 1:
            self.logger.error('getain command not succeed')
            return False
        if len(responseSplit) != 9:
            self.logger.error('wrong number of chunks in getain')
            return False
        self.data.model.altitudeError = responseSplit[0]
        self.data.model.azimuthError = responseSplit[1]
        self.data.model.polarError = responseSplit[2]
        self.data.model.positionAngle = responseSplit[3]
        self.data.model.orthoError = responseSplit[4]
        self.data.model.altitudeTurns = responseSplit[5]
        self.data.model.azimuthTurns = responseSplit[6]
        self.data.model.terms = responseSplit[7]
        self.data.model.errorRMS = responseSplit[8]
        return True

    def pollModelStars(self):
        """
        Sending the polling ModelNames command. It collects for all the known names
        the string. The number of names have to be collected first, than it gathers
        all name at once.

        :return: success:   True if ok, False if not
        """

        conn = Connection(self.host)
        # getting numbers and data first
        _canGetain = self.data.fw.checkNewer(21500)
        if _canGetain:
            commandString = ':getalst#:getain#'
        else:
            commandString = ':getalst#'
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        suc = self._parseNumberStars(response, chunks, _canGetain)
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
        conn = Connection(self.host)
        # conversion, as we only have positive alt, we set the '+' as standard.
        _altFormat = ':Sa{sign}{0:02.0f}*{1:02.0f}:{2:04.1f}#'
        _setAlt = _altFormat.format(*alt.signed_dms()[1:4],
                                    sign='+' if alt.degrees > 0 else '-')
        _azFormat = ':Sz{0:03.0f}*{1:02.0f}:{2:04.1f}#'
        _setAz = _azFormat.format(*az.dms())
        commandString = ''.join((_setAlt, _setAz))
        # set coordinates
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if '0' in response:
            self.logger.error('coordinates could not be set, {0}'.format(response))
            return False
        # start slewing with first unpark and then slew command
        commandString = ''.join((':PO#', ':MS#'))
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if '#' in response:
            self.logger.error('slew could not be done, {0}'.format(response))
            return False
        return True

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
        _raFormat = ':Sr{0:02.0f}:{1:02.0f}:{2:05.2f}#'
        _setRa = _raFormat.format(*ra.dms())
        _decFormat = ':Sd{sign}{0:03.0f}*{1:02.0f}:{2:04.1f}#'
        _setDec = _decFormat.format(*dec.signed_dms()[1:4],
                                    sign='+' if dec.degrees > 0 else '-')
        commandString = ''.join((_setRa, _setDec))
        # set coordinates
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if '0' in response:
            self.logger.error('coordinates could not be set, {0}'.format(response))
            return False
        # start slewing with first unpark and slew command
        commandString = ''.join((':PO#', ':MS#'))
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if '#' in response:
            self.logger.error('slew could not be done, {0}'.format(response))
            return False
        return True

    def boot(self):
        pass

    def shutdown(self):
        """
        shutdown send the shutdown command to the mount. if succeeded it takes about 20
        seconds before you could switch off the power supply. please check red LED at mount

        :return:    success
        """

        conn = Connection(self.host)
        suc, response, chunks = conn.communicate(':shutdown#')
        if not suc:
            return False
        if response == 0:
            return False
        return True

    def setSiteCoordinates(self, value):
        pass

    def setSlewRate(self, value):
        """
        setSlewRate sends the command for setting the max slew rate to the mount.

        :param value:   float for max slew rate in degrees per second
        :return:        success
        """

        if value < 2:
            return False
        elif value > 15:
            return False
        conn = Connection(self.host)
        commandString = ':Sw{0:02.0f}#'.format(value)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True

    def setRefractionTemp(self, value):
        """
        setRefractionTemp sends the command for setting the temperature to the mount. the limit is set to
        -40 to +75, but there is not real documented limit.

        :param value:   float for temperature correction in Celsius
        :return:        success
        """

        if value < -40:
            return False
        elif value > 75:
            return False
        conn = Connection(self.host)
        commandString = ':SRTMP{0:+6.1f}#'.format(value)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True

    def setRefractionPress(self, value):
        """
        setRefractionPress sends the command for setting the pressure to the mount. the limit is set
        from 800 to 1200 hPa. no limit give from the mount

        :param value:   float for pressure correction
        :return:        success
        """

        if value < 800:
            return False
        elif value > 1200:
            return False
        conn = Connection(self.host)
        commandString = ':SRPRS{0:6.1f}#'.format(value)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True

    def setRefraction(self, status):
        """
        setRefraction sends the command to the mount.

        :param status:  bool for enable or disable refraction correction
        :return:        success
        """

        conn = Connection(self.host)
        commandString = ':SREF{0:1d}#'.format(1 if status else 0)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True

    def setUnattendedFlip(self, status):
        """
        setUnattendedFlip sends the  command to the mount. the command returns nothing.

        :param status:  bool for enable or disable unattended flip
        :return:        success
        """

        conn = Connection(self.host)
        commandString = ':Suaf{0:1d}#'.format(1 if status else 0)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        return True

    def setDualAxisTracking(self, status):
        """
        setDualAxisTracking sends the  command to the mount.

        :param status:  bool for enable or disable dual tracking
        :return:        success
        """

        conn = Connection(self.host)
        commandString = ':Sdat{0:1d}#'.format(1 if status else 0)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True

    def setMeridianLimitTrack(self, value):
        """
        setMeridianLimitTrack sends the command for setting flip limit to the mount. the limit is set from
        -20 to 20 degrees

        :param value:   float for degrees
        :return:        success
        """

        if value < -20:
            return False
        elif value > 20:
            return False
        conn = Connection(self.host)
        value = int(value)
        commandString = ':Slmt{0:02d}#'.format(value)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True

    def setMeridianLimitSlew(self, value):
        """
        setMeridianLimitSlew sends the command for setting flip limit to the mount. the limit is set
        to -20 to 20 degrees

        :param value:   float / int for degrees
        :return:        success
        """

        if value < -20:
            return False
        elif value > 20:
            return False
        conn = Connection(self.host)
        value = int(value)
        commandString = ':Slms{0:02d}#'.format(value)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True

    def setHorizonLimitHigh(self, value):
        """
        setHorizonLimitHigh sends the command for setting the limit to the mount. the limit is set
        from 0 to 90 degrees

        :param value:   float / int for degrees
        :return:        success
        """

        if value < 0:
            return False
        elif value > 90:
            return False
        conn = Connection(self.host)
        value = int(value)
        commandString = ':Sh+{0:02d}#'.format(value)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True

    def setHorizonLimitLow(self, value):
        """
        setHorizonLimitLow sends the command for setting the limit to the mount. the limit
        has to be between -5 and +45 degrees

        :param value:   float / int for degrees
        :return:        success
        """

        if value < -5:
            return False
        elif value > 45:
            return False
        conn = Connection(self.host)
        value = int(value)
        commandString = ':So{0:+02d}#'.format(value)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True

    def startTracking(self):
        """
        startTracking sends the start command to the mount. the command returns nothing.
        it is necessary to make that direct to unpark first, than start tracking

        :return:    success
        """

        conn = Connection(self.host)
        suc, response, chunks = conn.communicate(':PO#:AP#')
        if not suc:
            return False
        return True

    def stopTracking(self):
        """
        stopTracking sends the start command to the mount. the command returns nothing.

        :return:    success
        """

        conn = Connection(self.host)
        suc, response, chunks = conn.communicate(':RT9#')
        if not suc:
            return False
        return True

    def setLunarTracking(self):
        """
        setLunar sends the command for lunar tracking speed to the mount. the command
        returns nothing.

        :return:    success
        """

        conn = Connection(self.host)
        suc, response, chunks = conn.communicate(':RT0#')
        if not suc:
            return False
        return True

    def setSiderealTracking(self):
        """
        setLunar sends the command for sidereal tracking speed to the mount. the command
        returns nothing.

        :return:    success
        """

        conn = Connection(self.host)
        suc, response, chunks = conn.communicate(':RT1#')
        if not suc:
            return False
        return True

    def setSolarTracking(self):
        """
        setLunar sends the command for solar tracking speed to the mount. the command
        returns nothing.

        :return:    success
        """

        conn = Connection(self.host)
        suc, response, chunks = conn.communicate(':RT2#')
        if not suc:
            return False
        return True

    def park(self):
        """
        park sends the park command to the mount. the command returns nothing.

        :return:    success
        """

        conn = Connection(self.host)
        suc, response, chunks = conn.communicate(':hP#')
        if not suc:
            return False
        return True

    def unpark(self):
        """
        unpark sends the unpark command to the mount.

        :return:    success
        """

        conn = Connection(self.host)
        suc, response, chunks = conn.communicate(':PO#')
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True

    def stop(self):
        """
        stop sends the stop command to the mount. the command returns nothing.

        :return:    success
        """

        conn = Connection(self.host)
        suc, response, chunks = conn.communicate(':STOP#')
        if not suc:
            return False
        return True

    def flip(self):
        """
        flip sends the flip command to the mount.

        :return:    success
        """

        conn = Connection(self.host)
        suc, response, chunks = conn.communicate(':flip#')
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True

    def clearModel(self):
        """
        clear model sends the clear command to the mount and deletes the current alignment
        model and alignment stars

        :return:    success
        """

        conn = Connection(self.host)
        suc, response, chunks = conn.communicate(':delalig#')
        if not suc:
            return False
        if response.count('#') == 0:
            return False
        return True

    def deletePoint(self, number):
        """
        deletePoint deletes the point with number from the actual alignment model. the
        model will be recalculated by the mount computer afterwards. number has to be an
        existing point in the database. the counting is from 1 to N.

        :param      number: number of point in int / float
        :return:    success
        """

        number = int(number)
        conn = Connection(self.host)
        commandString = ':delalst{0:d}#'.format(number)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True

    def storeName(self, name):
        """
        storeName saves the actual alignment model to the database of the mount computer
        under the given name. the name is context sensitive and does contain maximum 15
        characters.

        :param      name: name of model as string
        :return:    success
        """

        if len(name) > 15:
            return
        conn = Connection(self.host)

        # as the mount does raise an error, if the name already exists, we delete it
        # anyway before saving to a name
        commandString = ':modeldel0{0}#:modelsv0{1}#'.format(name, name)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if len(response) != 2:
            return False
        if response[0] != '1':
            self.logger.info('model >{0}< overwritten'.format(name))
        if response[1] != '1':
            return False
        return True

    def loadName(self, name):
        """
        loadName loads from the database of the mount computer the model under the given
        name as the actual alignment model . the name is context sensitive and does contain
        maximum 15 characters.

        :param      name: name of model as string
        :return:    success
        """

        if len(name) > 15:
            return
        conn = Connection(self.host)
        commandString = ':modelld0{0}#'.format(name)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True

    def deleteName(self, name):
        """
        deleteName deletes the model from the database of the mount computer under the
        given name. the name is context sensitive and does contain maximum 15 characters.

        :param      name: name of model as string
        :return:    success
        """

        if len(name) > 15:
            return
        conn = Connection(self.host)
        commandString = ':modeldel0{0}#'.format(name)
        suc, response, chunks = conn.communicate(commandString)
        if not suc:
            return False
        if len(response) != 1:
            return False
        if response[0] != '1':
            return False
        return True
