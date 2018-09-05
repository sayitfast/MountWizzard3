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


class Build(object):
    """
    The class Build inherits all information and handling of the actual
    build data which was generated during the model run.

        >>> settings = Build(
        >>>                 )

    But mostly the command will be:

        >>> settings = Build()
    """

    __all__ = ['Build',
               'setList',
               'addSet',
               'delSet',
               'checkSetListOK',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    def __init__(self,
                 ):

        self._setList = list()

    @property
    def setList(self):
        return self._setList

    @setList.setter
    def setList(self, value):
        if isinstance(value, list) and len(value) > 0:
            self._setList = value
        else:
            self._setList = list()

    def addStar(self, value):
        """
        Adds a star to the list of stars. Type of name should be class ModelStar.

        :param      value:  name as type ModelStar
        :return:    nothing
        """

        if isinstance(value, BuildStar):
            self._setList.insert(len(self._setList), value)
            return
        if not isinstance(value, (list, str)):
            self.logger.error('malformed value: {0}'.format(value))
            return
        if isinstance(value, str):
            value = value.split(',')
        if len(value) == 5:
            _ha, _dec, _err, _angle, _number = value
            value = ModelStar(point=(_ha, _dec),
                              errorRMS=_err,
                              errorAngle=_angle,
                              number=_number)
            self._setList.insert(len(self._setList), value)

    def delStar(self, value):
        """
        Deletes a name from the list of stars at position value. The numbering
        is from 0 to len -1 of list.

        :param value: position as int
        """
        try:
            value = int(value)
        except Exception as e:
            self.logger.error('error: {0}, malformed value: {1}'.format(e, value))
            return
        if value < 0 or value > len(self._setList) - 1:
            self.logger.error('invalid value: {0}'.format(value))
            return
        self._setList.pop(value)

    def checkSetListOK(self):
        """
        Make a check if the actual alignment star count by polling gets the same
        number of stars compared to the number of stars in the list.
        Otherwise something was changed.

        :return: True if same size
        """
        if self._numberStars == len(self._setList):
            return True
        else:
            return False


class BuildStar(object):
    """
    The class BuildStar inherits all informations and handling of the coordinates of
    a pointing direction of the nominal mount coordinates and the plate solved
    coordinates, which were derived from a taken image at the scope
    the coordinates both are in JNow topocentric

        >>> settings = BuildStar(
        >>>                     )

    coordinates could be from type skyfield.api.Star or just a tuple of (ha, dec) where
    the format should be float or the 10micron string format.

    """

    __all__ = ['ModelStar',
               'mountStar',
               'pierside',
               'solveStar',
               'sidereal',
               ]
    version = '0.1'
    logger = logging.getLogger(__name__)

    def __init__(self,
                 ):

        self._mountStar = None
        self._pierside = None
        self._solveStar = None
        self._sidereal = None

    @property
    def mountStar(self):
        return self._mountStar

    @mountStar.setter
    def mountStar(self, value):
        if isinstance(value, skyfield.api.Star):
            self._mountStar = value
            return
        if not isinstance(value, tuple):
            self.logger.error('malformed value: {0}'.format(value))
            self._mountStar = skyfield.api.Star(ra_hours=0,
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
            self._mountStar = skyfield.api.Star(ra_hours=_ha,
                                                dec_degrees=_dec)
        else:
            self.logger.error('malformed value: {0}'.format(value))

    @property
    def pierside(self):
        return self._pierside

    @pierside.setter
    def pierside(self, value):
        try:
            self._pierside = int(value)
        except Exception as e:
            self.logger.error('error: {0}, malformed value: {1}'.format(e, value))

    @property
    def solveStar(self):
        return self._solveStar

    @solveStar.setter
    def solveStar(self, value):
        if isinstance(value, skyfield.api.Star):
            self._solveStar = value
            return
        if not isinstance(value, tuple):
            self.logger.error('malformed value: {0}'.format(value))
            self._solveStar = skyfield.api.Star(ra_hours=0,
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
            self._solveStar = skyfield.api.Star(ra_hours=_ha,
                                                dec_degrees=_dec)
        else:
            self.logger.error('malformed value: {0}'.format(value))

    @property
    def sidereal(self):
        return self._sidereal

    @sidereal.setter
    def sidereal(self, value):
        try:
            self._sidereal = float(value)
        except Exception as e:
            self.logger.error('error: {0}, malformed value: {1}'.format(e, value))
