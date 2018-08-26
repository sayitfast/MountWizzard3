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
import numpy

import skyfield.api


class Data(object):
    """
    The class Data inherits all informations and handling of internal states an
    their attributes of the connected mount and provides the abstracted interface
    to a 10 micron mount.

        >>> fw = Data(
        >>>           pathToTimescaleData=pathToTimescaleData,
        >>>           verbose=False,
        >>>           expire=True,
        >>>           )

    The Data class generates the central timescale from skyfield.api which is
    needed by all calculations related to time. As it build its own loader it
    needs to know where to store the data and with which parameters the
    timescale data should be addressed
    """

    __all__ = ['Data',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    def __init__(self,
                 pathToTimescaleData=None,
                 verbose=False,
                 expire=True,
                 ):

        self.pathToTimescaleData = pathToTimescaleData
        self.verbose = verbose
        self.expire = expire

        # generate timescale data
        load = skyfield.api.Loader(self.pathToTimescaleData,
                                   verbose=self.verbose,
                                   expire=self.expire,
                                   )
        self.timeScale = load.timescale()
        self.fw = Firmware()
        self.setting = Setting()
        self.site = Site(self.timeScale)
        self.model = Model()


class Firmware(object):
    """
    The class Firmware inherits all informations and handling of firmware
    attributes of the connected mount and provides the abstracted interface
    to a 10 micron mount.

        >>> fw = Firmware()
    """

    __all__ = ['Firmware',
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
        return number > self._number

    def __str__(self):
        output = '<Product: {0}>   <Firmware: {1}>   <Hardware: {2}>'
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
        >>>             timescale=timescale)

    The Site class needs as parameter a timescale object from skyfield.api to
    be able to make all the necessary calculations about time from and to mount
    """

    __all__ = ['Site',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    def __init__(self, timeScale):

        self.timeScale = timeScale

        self._location = None
        self._timeJD = None
        self._timeSidereal = None
        self._raJNow = 0
        self._decJNow = 0
        self._pierside = ''
        self._apparentAlt = 0
        self._apparentAz = 0
        self._status = 0
        self._statusSlew = False

    def _stringToDegree(self, value):
        value = value.split(':')
        if len(value) != 3:
            self.logger.error('malformed value: {0}'.format(value))
            return 0
        value = [float(x) for x in value]
        value = value[0] + value[1] / 60 + value[2] / 3600
        return value

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        lat, lon, elev = value
        lon = skyfield.api.Angle(degrees=self._stringToDegree(lon))
        lat = skyfield.api.Angle(degrees=self._stringToDegree(lat))
        self._location = skyfield.api.Topos(longitude=lon,
                                            latitude=lat,
                                            elevation_m=elev)

    @property
    def timeJD(self):
        return self._timeJD

    @timeJD.setter
    def timeJD(self, value):
        self._timeJD = self.timeScale.tt_jd(value)

    @property
    def timeSidereal(self):
        return self._timeJD

    @timeSidereal.setter
    def timeSidereal(self, value):
        self._timeSidereal = value

    @property
    def raJNow(self):
        return self._raJNow

    @raJNow.setter
    def raJNow(self, value):
        self._raJNow = value

    @property
    def decJNow(self):
        return self._decJNow

    @decJNow.setter
    def decJNow(self, value):
        self._decJNow = value

    @property
    def pierside(self):
        return self._pierside

    @pierside.setter
    def pierside(self, value):
        self._pierside = value

    @property
    def apparentAlt(self):
        return self._apparentAlt

    @apparentAlt.setter
    def apparentAlt(self, value):
        self._apparentAlt = value

    @property
    def apparentAz(self):
        return self._apparentAz

    @apparentAz.setter
    def apparentAz(self, value):
        self._apparentAz = value

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
        self._statusSlew = value

    def __str__(self):
        output = '<Lat: {0}>   <Lon: {1}>   <Elev: {2}>'
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

        >>> settings = Settings()
    """

    __all__ = ['Setting',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    def __init__(self):
        self._slewRate = 0
        self._timeToFlip = 0
        self._meridianLimitGuide = 0
        self._meridianLimitSlew = 0
        self._timeToMeridian = 0
        self._refractionTemperature = 0
        self._refractionPressure = 0
        self._TrackingRate = 0
        self._TelescopeTempDEC = 0
        self._statusRefraction = False
        self._statusUnattendedFlip = False
        self._statusDualAxisTracking = False
        self._currentHorizonLimitHigh = 0
        self._currentHorizonLimitLow = 0
        self._numberModelNames = 0
        self._numberAlignmentStars = 0
        self._UTCDataValid = ''
        self._UTCDataExpirationDate = ''

    @property
    def slewRate(self):
        return self._slewRate

    @slewRate.setter
    def slewRate(self, value):
        self._slewRate = value

    @property
    def timeToFlip(self):
        return self._timeToFlip

    @timeToFlip.setter
    def timeToFlip(self, value):
        self._timeToFlip = value

    @property
    def meridianLimitGuide(self):
        return self._meridianLimitGuide

    @meridianLimitGuide.setter
    def meridianLimitGuide(self, value):
        self._meridianLimitGuide = value

    @property
    def meridianLimitSlew(self):
        return self._meridianLimitSlew

    @meridianLimitSlew.setter
    def meridianLimitSlew(self, value):
        self._meridianLimitSlew = value

    @property
    def timeToMeridian(self):
        self._timeToMeridian = int(self._timeToFlip - self._meridianLimitGuide/360*24*60)
        return self._timeToMeridian

    @property
    def refractionTemperature(self):
        return self._refractionTemperature

    @refractionTemperature.setter
    def refractionTemperature(self, value):
        self._refractionTemperature = value

    @property
    def refractionPressure(self):
        return self._refractionPressure

    @refractionPressure.setter
    def refractionPressure(self, value):
        self._refractionPressure = value

    @property
    def TrackingRate(self):
        return self._TrackingRate

    @TrackingRate.setter
    def TrackingRate(self, value):
        self._TrackingRate = value

    @property
    def TelescopeTempDEC(self):
        return self._TelescopeTempDEC

    @TelescopeTempDEC.setter
    def TelescopeTempDEC(self, value):
        self._TelescopeTempDEC = value

    @property
    def refractionStatus(self):
        return self._statusRefraction

    @refractionStatus.setter
    def refractionStatus(self, value):
        self._statusRefraction = value

    @property
    def statusUnattendedFlip(self):
        return self._statusUnattendedFlip

    @statusUnattendedFlip.setter
    def statusUnattendedFlip(self, value):
        self._statusUnattendedFlip = value

    @property
    def statusDualAxisTracking(self):
        return self._statusDualAxisTracking

    @statusDualAxisTracking.setter
    def statusDualAxisTracking(self, value):
        self._statusDualAxisTracking = value

    @property
    def currentHorizonLimitHigh(self):
        return self._currentHorizonLimitHigh

    @currentHorizonLimitHigh.setter
    def currentHorizonLimitHigh(self, value):
        self._currentHorizonLimitHigh = value

    @property
    def currentHorizonLimitLow(self):
        return self._currentHorizonLimitLow

    @currentHorizonLimitLow.setter
    def currentHorizonLimitLow(self, value):
        self._currentHorizonLimitLow = value

    @property
    def UTCDataValid(self):
        return self._UTCDataValid

    @UTCDataValid.setter
    def UTCDataValid(self, value):
        self._UTCDataValid = value

    @property
    def UTCDataExpirationDate(self):
        return self._UTCDataExpirationDate

    @UTCDataExpirationDate.setter
    def UTCDataExpirationDate(self, value):
        self._UTCDataExpirationDate = value


class Model(object):
    """
    The class Model inherits all informations and handling of the actual
    alignment model used by the mount and the data, which models are stored
    in the mount and provides the abstracted interface to a 10 micron mount.

        >>> settings = Model()
    """

    __all__ = ['Model',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    def __init__(self):
        self._numberModelNames = 0
        self._numberAlignmentStars = 0
        self._starList = list()
        self._modelNameList = list()

    @property
    def starList(self):
        return self._starList

    @property
    def numberAlignmentStars(self):
        return self._numberAlignmentStars

    @numberAlignmentStars.setter
    def numberAlignmentStars(self, value):
        self._numberAlignmentStars = value

    def addStar(self):
        if isinstance(value, ModelStar):
            self._starList.extend(value)
        elif len(value) == 4:
            _point, _err, _number = value
            value = ModelStar(_point, _err, _number)
            self._starList.extend(value)
        else:
            self.logger.error('malformed value: {0}'.format(value))

    def delStar(self, value):
        value = int(value)
        if value < 0 or value > len(self._starList):
            self.logger.error('invalid value: {0}'.format(value))
            return
        self._starList.pop(value)

    def checkStarListOK(self):
        """
        Make a check if the actual alignment star count by polling gets the same
        number of stars compared to the number of stars in the list.
        Otherwise something was changed.

        :return: output of check
        """
        if self._numberAlignmentStars == len(self._starList):
            return True
        else:
            return False

    @property
    def modelNameList(self):
        return self._modelNameList

    @property
    def numberModelNames(self):
        return self._numberModelNames

    @numberModelNames.setter
    def numberModelNames(self, value):
        self._numberModelNames = value

    def addName(self):
        if isinstance(value, str):
            self._modelNameList.extend(value)
        else:
            self.logger.error('malformed value: {0}'.format(value))

    def delName(self, value):
        value = int(value)
        if value < 0 or value > len(self._modelNameList):
            self.logger.error('invalid value: {0}'.format(value))
            return
        self._modelNameList.pop(value)

    def checkModelNameListOK(self):
        """
        Make a check if the actual model name count by polling gets the same
        number of names compared to the number of names in the list.
        Otherwise something was changed.

        :return: output of check
        """
        if self._numberModelNames == len(self._starList):
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
                 point=(0, 0),
                 errorRMS=0,
                 errorAngle=0,
                 number=0
                 ):

        self.point = point
        self.errorRMS = errorRMS
        self.errorAngle = errorAngle
        self.number = number

    def _stringToHourHA(self, value):
        value = value.split(':')
        if len(value) != 3:
            self.logger.error('malformed value: {0}'.format(value))
            return 0
        value = [float(x) for x in value]
        value = value[0] + value[1] / 60 + value[2] / 3600
        return value

    def _stringToDegreeDEC(self, value):
        if value.count('*') != 1:
            self.logger.error('malformed value: {0}'.format(value))
            return 0
        value = value.replace('*', ':')
        _sign = value[0]
        if _sign == '-':
            _sign = - 1.0
        else:
            _sign = 1.0
        value = value[1:]
        value = value.split(':')
        if len(value) != 3:
            self.logger.error('malformed value: {0}'.format(value))
            return 0
        value = [float(x) for x in value]
        value = value[0] + value[1] / 60 + value[2] / 3600
        value = _sign * value
        return value

    @property
    def point(self):
        return self._point

    @point.setter
    def point(self, value):
        if isinstance(value, skyfield.api.Star):
            self._point = value
        elif isinstance(value, tuple):
            _ha, _dec = value
            if isinstance(value[1], str):
                _ha = self._stringToHourHA(_ha)
                _dec = self._stringToDegreeDEC(_dec)
            self._point = skyfield.api.Star(ra_hours=_ha,
                                            dec_degrees=_dec)
        else:
            self.logger.error('malformed value: {0}'.format(value))
            self._point = skyfield.api.Star(ra_hours=0,
                                            dec_degrees=0)

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
