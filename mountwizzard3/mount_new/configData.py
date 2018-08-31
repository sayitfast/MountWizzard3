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
import numpy
import skyfield.api
# local imports

__all__ = [
    'stringToDegree',
    'stringToDegreeDEC',
]


# conversion from HA value, which is
# HH:MM:SS.SS format to decimal value
def stringToDegree(value):
    value = value.split(':')
    if len(value) != 3:
        return None
    value = [float(x) for x in value]
    value = value[0] + value[1] / 60 + value[2] / 3600
    return value


# conversion from value, which is
# +dd*mm:ss.s format to decimal value
def stringToDegreeDEC(value):
    if value.count('*') != 1:
        return None
    value = value.replace('*', ':')
    _sign = value[0]
    if _sign == '-':
        _sign = - 1.0
    else:
        _sign = 1.0
    value = value[1:]
    value = value.split(':')
    if len(value) != 3:
        return None
    value = [float(x) for x in value]
    value = value[0] + value[1] / 60 + value[2] / 3600
    value = _sign * value
    return value


class Data(object):
    """
    The class Data inherits all informations and handling of internal states an
    their attributes of the connected mount and provides the abstracted interface
    to a 10 micron mount.

        >>> fw = Data(
        >>>           pathToTS=pathToTS,
        >>>           verbose=False,
        >>>           expire=True,
        >>>           )

    The Data class generates the central timescale from skyfield.api which is
    needed by all calculations related to time. As it build its own loader it
    needs to know where to store the data and with which parameters the
    timescale data should be addressed
    """

    __all__ = ['Data',
               'fw',
               'setting',
               'site',
               'model',
               'ts',
               'expire',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    def __init__(self,
                 pathToTS=None,
                 verbose=False,
                 expire=True,
                 ):

        self._expire = expire
        self.pathToTS = pathToTS
        self.verbose = verbose
        self.ts = None

        self.loadTimescale()

        # instantiating the other necessary data objects / classes
        self.fw = Firmware()
        self.setting = Setting()
        self.site = Site(self.ts)
        self.model = Model()

    @property
    def expire(self):
        return self._expire

    @expire.setter
    def expire(self, value):
        if isinstance(value, bool):
            self._expire = value
        else:
            self.logger.error('wrong type value: {0}'.format(value))

    def loadTimescale(self):
        # generate timescale data
        if self.pathToTS:
            # normally there should be a path given
            load = skyfield.api.Loader(self.pathToTS,
                                       verbose=self.verbose,
                                       expire=self.expire,
                                       )
            self.ts = load.timescale()
        else:
            self.ts = skyfield.api.load.timescale()
            self.logger.info('no path for timescale given, using default')


class Firmware(object):
    """
    The class Firmware inherits all informations and handling of firmware
    attributes of the connected mount and provides the abstracted interface
    to a 10 micron mount.

        >>> fw = Firmware()
    """

    __all__ = ['Firmware',
               'productName',
               'numberString',
               'hwVersion',
               'fwtime',
               'fwdate',
               'checkNewer'
               'number',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    def __init__(self):

        self._productName = ''
        self._numberString = ''
        self._number = 0
        self._hwVersion = ''
        self._fwdate = ''
        self._fwtime = ''

    @property
    def productName(self):
        return self._productName

    @productName.setter
    def productName(self, value):
        self._productName = value

    @property
    def numberString(self):
        return self._numberString

    @property
    def number(self):
        return self._number

    @numberString.setter
    def numberString(self, value):
        self._numberString = value
        if value.count('.') == 2:
            _parts = value.split('.')
            self._number = int(_parts[0]) * 10000 + int(_parts[1]) * 100 + int(_parts[2])
        else:
            self._number = 0
            self.logger.error('malformed value: {0}'.format(value))

    @property
    def hwVersion(self):
        return self._hwVersion

    @hwVersion.setter
    def hwVersion(self, value):
        self._hwVersion = value

    @property
    def fwdate(self):
        return self._fwdate

    @fwdate.setter
    def fwdate(self, value):
        self._fwdate = value

    @property
    def fwtime(self):
        return self._fwtime

    @fwtime.setter
    def fwtime(self, value):
        self._fwtime = value

    def checkNewer(self, number):
        """
        Checks if the provided FW number is newer than the one of the mount

        :param number:      fw number to test as int
        :return:            True if newer / False
        """

        return number > self._number

    def __str__(self):
        output = 'Prod: {0}, FW: {1}, HW: {2}'
        value = output.format(self._productName,
                              self._numberString,
                              self._hwVersion,
                              )
        return value


class Site(object):
    """
    The class Site inherits all informations and handling of site data
    attributes of the connected mount and provides the abstracted interface
    to a 10 micron mount.

        >>> site = Site(
        >>>             ts=ts,
        >>>             location=(0, 0, 0),
        >>>             )

    The Site class needs as parameter a ts object from skyfield.api to
    be able to make all the necessary calculations about time from and to mount
    """

    __all__ = ['Site',
               'location',
               'timeJD',
               'timeSidereal',
               'raJNow',
               'decJNow',
               'pierside',
               'Alt',
               'Az',
               'status',
               'statusSlew',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    def __init__(self,
                 ts=None,
                 location=None,
                 ):

        self.ts = ts
        self._location = location
        self._timeJD = None
        self._timeSidereal = None
        self._raJNow = None
        self._decJNow = None
        self._pierside = None
        self._Alt = None
        self._Az = None
        self._status = None
        self._statusSlew = None

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        if not value:
            return
        if isinstance(value, skyfield.api.Topos):
            self._location = value
            return
        if not isinstance(value, list):
            self.logger.error('malformed value: {0}'.format(value))
            return
        if len(value) != 3:
            self.logger.error('malformed value: {0}'.format(value))
            return
        lat, lon, elev = value
        if all(isinstance(x, str) for x in value):
            lon = stringToDegree(lon)
            if not lon:
                self.logger.error('malformed value: {0}'.format(value))
                return
            lat = stringToDegree(lat)
            if not lat:
                self.logger.error('malformed value: {0}'.format(value))
                return
            elev = float(elev)
        elif all(isinstance(x, (int, float)) for x in value):
            lon = skyfield.api.Angle(degrees=lon)
            lat = skyfield.api.Angle(degrees=lat)
        else:
            self.logger.error('malformed value: {0}'.format(value))
            return
        self._location = skyfield.api.Topos(longitude=lon,
                                            latitude=lat,
                                            elevation_m=elev)

    @property
    def timeJD(self):
        return self._timeJD

    @timeJD.setter
    def timeJD(self, value):
        if isinstance(value, float):
            self._timeJD = self.ts.tt_jd(value)
        else:
            self._timeJD = self.ts.tt_jd(float(value))

    @property
    def timeSidereal(self):
        return self._timeJD

    @timeSidereal.setter
    def timeSidereal(self, value):
        if isinstance(value, str):
            self._timeSidereal = value
        else:
            self._timeSidereal = str(value)

    @property
    def raJNow(self):
        return self._raJNow

    @raJNow.setter
    def raJNow(self, value):
        if isinstance(value, skyfield.api.Angle):
            self._raJNow = value
        elif isinstance(value, str):
            value = float(value)
            self._raJNow = skyfield.api.Angle(degrees=value)
        elif isinstance(value, float):
            self._raJNow = skyfield.api.Angle(degrees=value)
        elif isinstance(value, int):
            self._raJNow = skyfield.api.Angle(degrees=float(value))
        else:
            self._raJNow = skyfield.api.Angle(degrees=0)
            self.logger.error('malformed value: {0}'.format(value))

    @property
    def decJNow(self):
        return self._decJNow

    @decJNow.setter
    def decJNow(self, value):
        if isinstance(value, skyfield.api.Angle):
            self._decJNow = value
        elif isinstance(value, str):
            value = float(value)
            self._decJNow = skyfield.api.Angle(degrees=value)
        elif isinstance(value, float):
            self._decJNow = skyfield.api.Angle(degrees=value)
        elif isinstance(value, int):
            self._decJNow = skyfield.api.Angle(degrees=float(value))
        else:
            self._decJNow = skyfield.api.Angle(degrees=0)
            self.logger.error('malformed value: {0}'.format(value))

    @property
    def pierside(self):
        return self._pierside

    @pierside.setter
    def pierside(self, value):
        if value in ['E', 'W']:
            self._pierside = value
        else:
            self._pierside = 'E'
            self.logger.error('malformed value: {0}'.format(value))

    @property
    def Alt(self):
        return self._Alt

    @Alt.setter
    def Alt(self, value):
        if isinstance(value, skyfield.api.Angle):
            self._Alt = value
        elif isinstance(value, str):
            self._Alt = skyfield.api.Angle(degrees=float(value))
        elif isinstance(value, float):
            self._Alt = skyfield.api.Angle(degrees=value)
        elif isinstance(value, int):
            self._Alt = skyfield.api.Angle(degrees=float(value))
        else:
            self._Alt = skyfield.api.Angle(degrees=0)
            self.logger.error('malformed value: {0}'.format(value))

    @property
    def Az(self):
        return self._Az

    @Az.setter
    def Az(self, value):
        if isinstance(value, skyfield.api.Angle):
            self._Az = value
        elif isinstance(value, str):
            self._Az = skyfield.api.Angle(degrees=float(value))
        elif isinstance(value, float):
            self._Az = skyfield.api.Angle(degrees=value)
        elif isinstance(value, int):
            self._Az = skyfield.api.Angle(degrees=float(value))
        else:
            self._Az = skyfield.api.Angle(degrees=0)
            self.logger.error('malformed value: {0}'.format(value))

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def statusSlew(self):
        return self._statusSlew

    @statusSlew.setter
    def statusSlew(self, value):
        if isinstance(value, bool):
            self._statusSlew = value
        else:
            self._statusSlew = bool(value)

    def __str__(self):
        output = 'Lat: {0}, Lon: {1}, Elev: {2}'
        value = output.format(self._location.latitude,
                              self._location.longitude,
                              self._location.elevation.m,
                              )
        return value


class Setting(object):
    """
    The class Setting inherits all informations and handling of settings
    attributes of the connected mount and provides the abstracted interface
    to a 10 micron mount.

        >>> settings = Settings(
        >>>                     )

    """

    __all__ = ['Setting',
               'slewRate',
               'timeToFlip',
               'timeToMeridian',
               'meridianLimitGuide',
               'meridianLimitSlew',
               'refractionTemperature',
               'refractionPressure',
               'trackingRate',
               'telescopeTempDEC',
               'statusRefraction',
               'statusUnattendedFlip',
               'statusDualAxisTracking',
               'currentHorizonLimitHigh',
               'currentHorizonLimitLow',
               'UTCDataValid',
               'UTCDataExpirationDate',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    def __init__(self,
                 ):

        self._slewRate = None
        self._timeToFlip = None
        self._meridianLimitGuide = None
        self._meridianLimitSlew = None
        self._refractionTemperature = None
        self._refractionPressure = None
        self._trackingRate = None
        self._telescopeTempDEC = None
        self._statusRefraction = None
        self._statusUnattendedFlip = None
        self._statusDualAxisTracking = None
        self._currentHorizonLimitHigh = None
        self._currentHorizonLimitLow = None
        self._UTCDataValid = None
        self._UTCDataExpirationDate = None
        self._timeToMeridian = None

    @property
    def slewRate(self):
        return self._slewRate

    @slewRate.setter
    def slewRate(self, value):
        if isinstance(value, float):
            self._slewRate = value
        else:
            self._slewRate = float(value)

    @property
    def timeToFlip(self):
        return self._timeToFlip

    @timeToFlip.setter
    def timeToFlip(self, value):
        if isinstance(value, float):
            self._timeToFlip = value
        else:
            self._timeToFlip = float(value)

    @property
    def meridianLimitGuide(self):
        return self._meridianLimitGuide

    @meridianLimitGuide.setter
    def meridianLimitGuide(self, value):
        if isinstance(value, float):
            self._meridianLimitGuide = value
        else:
            self._meridianLimitGuide = float(value)

    @property
    def meridianLimitSlew(self):
        return self._meridianLimitSlew

    @meridianLimitSlew.setter
    def meridianLimitSlew(self, value):
        if isinstance(value, float):
            self._meridianLimitSlew = value
        else:
            self._meridianLimitSlew = float(value)

    @property
    def timeToMeridian(self):
        self._timeToMeridian = int(self._timeToFlip - self._meridianLimitGuide/360*24*60)
        return self._timeToMeridian

    @property
    def refractionTemperature(self):
        return self._refractionTemperature

    @refractionTemperature.setter
    def refractionTemperature(self, value):
        if isinstance(value, float):
            self._refractionTemperature = value
        else:
            self._refractionTemperature = float(value)

    @property
    def refractionPressure(self):
        return self._refractionPressure

    @refractionPressure.setter
    def refractionPressure(self, value):
        if isinstance(value, float):
            self._refractionPressure = value
        else:
            self._refractionPressure = float(value)

    @property
    def trackingRate(self):
        return self._trackingRate

    @trackingRate.setter
    def trackingRate(self, value):
        if isinstance(value, float):
            self._telescopeTempDEC = value
        else:
            self._telescopeTempDEC = float(value)

    @property
    def telescopeTempDEC(self):
        return self._telescopeTempDEC

    @telescopeTempDEC.setter
    def telescopeTempDEC(self, value):
        if isinstance(value, float):
            self._telescopeTempDEC = value
        else:
            self._telescopeTempDEC = float(value)

    @property
    def statusRefraction(self):
        return self._statusRefraction

    @statusRefraction.setter
    def statusRefraction(self, value):
        if isinstance(value, bool):
            self._refractionPressure = value
        else:
            self._refractionPressure = bool(value)

    @property
    def statusUnattendedFlip(self):
        return self._statusUnattendedFlip

    @statusUnattendedFlip.setter
    def statusUnattendedFlip(self, value):
        if isinstance(value, bool):
            self._statusUnattendedFlip = value
        else:
            self._statusUnattendedFlip = bool(value)

    @property
    def statusDualAxisTracking(self):
        return self._statusDualAxisTracking

    @statusDualAxisTracking.setter
    def statusDualAxisTracking(self, value):
        if isinstance(value, bool):
            self._statusDualAxisTracking = value
        else:
            self._statusDualAxisTracking = bool(value)

    @property
    def currentHorizonLimitHigh(self):
        return self._currentHorizonLimitHigh

    @currentHorizonLimitHigh.setter
    def currentHorizonLimitHigh(self, value):
        if isinstance(value, float):
            self._currentHorizonLimitHigh = value
        else:
            self._currentHorizonLimitHigh = float(value)

    @property
    def currentHorizonLimitLow(self):
        return self._currentHorizonLimitLow

    @currentHorizonLimitLow.setter
    def currentHorizonLimitLow(self, value):
        if isinstance(value, float):
            self._currentHorizonLimitLow = value
        else:
            self._currentHorizonLimitLow = float(value)

    @property
    def UTCDataValid(self):
        return self._UTCDataValid

    @UTCDataValid.setter
    def UTCDataValid(self, value):
        if isinstance(value, bool):
            self._UTCDataValid = value
        else:
            self._UTCDataValid = bool(value)

    @property
    def UTCDataExpirationDate(self):
        return self._UTCDataExpirationDate

    @UTCDataExpirationDate.setter
    def UTCDataExpirationDate(self, value):
        if isinstance(value, str):
            self._UTCDataExpirationDate = value
        else:
            self._UTCDataExpirationDate = str(value)


class Model(object):
    """
    The class Model inherits all informations and handling of the actual
    alignment model used by the mount and the data, which models are stored
    in the mount and provides the abstracted interface to a 10 micron mount.

        >>> settings = Model(
        >>>                 )

    But mostly the command will be:

        >>> settings = Model()
    """

    __all__ = ['Model',
               'starList',
               'numberStars',
               'numberNames',
               'addStar',
               'delStar',
               'addName',
               'delName',
               'checkStarListOK',
               'checkNameListOK',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    def __init__(self,
                 ):

        self._numberNames = 0
        self._numberStars = 0
        self._starList = list()
        self._nameList = list()

    @property
    def starList(self):
        return self._starList

    @starList.setter
    def starList(self, value):
        if isinstance(value, list) and len(value) > 0:
            self._starList = value
        else:
            self._starList = list()

    @property
    def numberStars(self):
        return self._numberStars

    @numberStars.setter
    def numberStars(self, value):
        if isinstance(value, str):
            value = int(value)
        self._numberStars = value

    def addStar(self, value):
        """
        Adds a star to the list of stars. Type of name should be class ModelStar.

        :param value: name as type ModelStar
        :return: nothing
        """

        if isinstance(value, ModelStar):
            self._starList.insert(len(self._starList), value)
        elif len(value) == 4:
            _point, _err, _number = value
            value = ModelStar(_point, _err, _number)
            self._starList.extend(value)
        else:
            self.logger.error('malformed value: {0}'.format(value))

    def delStar(self, value):
        """
        Deletes a name from the list of stars at position value. The numbering
        is from 0 to len -1 of list.

        :param value: position as int
        """

        value = int(value)
        if value < 0 or value > len(self._starList) - 1:
            self.logger.error('invalid value: {0}'.format(value))
            return
        self._starList.pop(value)

    def checkStarListOK(self):
        """
        Make a check if the actual alignment star count by polling gets the same
        number of stars compared to the number of stars in the list.
        Otherwise something was changed.

        :return: True if same size
        """
        if self._numberStars == len(self._starList):
            return True
        else:
            return False

    @property
    def nameList(self):
        return self._nameList

    @nameList.setter
    def nameList(self, value):
        if isinstance(value, list) and len(value) > 0:
            self._nameList = value
        else:
            self._nameList = list()

    @property
    def numberNames(self):
        return self._numberNames

    @numberNames.setter
    def numberNames(self, value):
        if isinstance(value, str):
            value = int(value)
        self._numberNames = value

    def addName(self, value):
        """
        Adds a name to the list of names. Type of name should be str.

        :param value: name as str
        :return: nothing
        """

        if isinstance(value, str):
            self._nameList.insert(len(self._nameList), value)
        else:
            self.logger.error('malformed value: {0}'.format(value))

    def delName(self, value):
        """
        Deletes a name from the list of names at position value. The numbering
        is from 0 to len -1 of list.

        :param value: position as int
        :return: nothing
        """

        value = int(value)
        if value < 0 or value > len(self._nameList) - 1:
            self.logger.error('invalid value: {0}'.format(value))
            return
        self._nameList.pop(value)

    def checkNameListOK(self):
        """
        Make a check if the actual model name count by polling gets the same
        number of names compared to the number of names in the list.
        Otherwise something was changed.

        :return: True if same size
        """
        if self._numberNames == len(self._nameList):
            return True
        else:
            return False


class ModelStar(object):
    """
    The class ModelStar inherits all informations and handling of one star in
    the alignment model used by the mount and the data in the mount and provides the
    abstracted interface to a 10 micron mount.
    The coordinates are in JNow topocentric

        >>> settings = ModelStar(
        >>>                     point=None,
        >>>                     errorRMS=0,
        >>>                     errorAngle=0,
        >>>                     number=0,
        >>>                     )

    point could be from type skyfield.api.Star or just a tuple of (ha, dec) where
    the format should be float or the 10micron string format.

    Command protocol (from2.8.15 onwards):
    "HH:MM:SS.SS,+dd*mm:ss.s,eeee.e,ppp#" where HH:MM:SS.SS is the hour angle of the
    alignment star in hours, minutes, seconds and hundredths of second (from 0h to
    23h59m59.99s), +dd*mm:ss.s is the declination of the alignment star in degrees,
    arcminutes, arcseconds and tenths of arcsecond, eeee.e is the error between the star
    and the alignment model in arcseconds, ppp is the polar angle of the measured star
    with respect to the modeled star in the equatorial system in degrees from 0 to 359
    (0 towards the north pole, 90 towards east).
    """

    __all__ = ['ModelStar',
               'point',
               'errorRMS',
               'errorAngle',
               'errorRA',
               'errorDEC',
               'number',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    def __init__(self,
                 point=None,
                 errorRMS=None,
                 errorAngle=None,
                 number=None,
                 ):

        self.point = point
        self.errorRMS = errorRMS
        self.errorAngle = errorAngle
        self.number = number

    @property
    def point(self):
        return self._point

    @point.setter
    def point(self, value):
        if isinstance(value, skyfield.api.Star):
            self._point = value
        elif not isinstance(value, tuple):
            self.logger.error('malformed value: {0}'.format(value))
            self._point = skyfield.api.Star(ra_hours=0,
                                            dec_degrees=0)
        _ha, _dec = value
        if all(isinstance(x, str) for x in value):
            _ha = stringToDegree(_ha)
            if not _ha:
                self.logger.error('malformed value: {0}'.format(value))
                return
            _dec = stringToDegreeDEC(_dec)
            if not _dec:
                self.logger.error('malformed value: {0}'.format(value))
                return
            self._point = skyfield.api.Star(ra_hours=_ha,
                                            dec_degrees=_dec)
        else:
            print('problem')

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, value):
        self._number = int(value)

    @property
    def errorRMS(self):
        return self._errorRMS

    @errorRMS.setter
    def errorRMS(self, value):
        self._errorRMS = float(value)

    @property
    def errorAngle(self):
        return self._errorAngle

    @errorAngle.setter
    def errorAngle(self, value):
        if isinstance(value, skyfield.api.Angle):
            self._errorAngle = value
        elif isinstance(value, str):
            value = float(value)
            self._errorAngle = skyfield.api.Angle(degrees=value)
        else:
            self.logger.error('malformed value: {0}'.format(value))
            self._errorAngle = skyfield.api.Angle(degrees=0)

    @property
    def errorRA(self):
        return self._errorRMS * numpy.sin(self._errorAngle.radians)

    @property
    def errorDEC(self):
        return self._errorRMS * numpy.cos(self._errorAngle.radians)

    def __str__(self):
        output = 'Star {0:2d}: HA: {1}, DEC: {2}, Error: {3}'
        value = output.format(self._number,
                              self._point.ra.hms,
                              self._point.dec.dms,
                              self.errorRMS,
                              )
        return value
