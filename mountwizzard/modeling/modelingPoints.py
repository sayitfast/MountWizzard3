############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
############################################################
import logging
import os
import copy
import operator
import numpy
from astrometry import transform


class ModelPoints:
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        self.app = app
        self.transform = transform.Transform(self.app)
        self.horizonPoints = list()
        self.modelPoints = list()
        self.BasePoints = list()
        self.RefinementPoints = list()

    def initConfig(self):
        try:
            if 'HorizonPointsFileName' in self.app.config:
                self.app.ui.le_horizonPointsFileName.setText(self.app.config['HorizonPointsFileName'])
            if 'CheckUseMinimumHorizonLine' in self.app.config:
                self.app.ui.checkUseMinimumHorizonLine.setChecked(self.app.config['CheckUseMinimumHorizonLine'])
            if 'CheckUseFileHorizonLine' in self.app.config:
                self.app.ui.checkUseFileHorizonLine.setChecked(self.app.config['CheckUseFileHorizonLine'])
            if 'AltitudeMinimumHorizon' in self.app.config:
                self.app.ui.altitudeMinimumHorizon.setValue(self.app.config['AltitudeMinimumHorizon'])
            self.loadHorizonPoints(self.app.config['HorizonPointsFileName'],
                                   self.app.config['CheckUseFileHorizonLine'],
                                   self.app.config['CheckUseMinimumHorizonLine'],
                                   self.app.config['AltitudeMinimumHorizon'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['HorizonPointsFileName'] = self.app.ui.le_horizonPointsFileName.text()
        self.app.config['CheckUseMinimumHorizonLine'] = self.app.ui.checkUseMinimumHorizonLine.isChecked()
        self.app.config['CheckUseFileHorizonLine'] = self.app.ui.checkUseFileHorizonLine.isChecked()
        self.app.config['AltitudeMinimumHorizon'] = self.app.ui.altitudeMinimumHorizon.value()

    def saveModelPoints(self, modelPointsFileName):
        msg = None
        fileHandle = None
        if modelPointsFileName.strip() == '':
            msg = 'No Model Points Filename given!'
            self.logger.warning('No Model Points Filename given!')
            return msg
        try:
            fileHandle = open(modelPointsFileName + '.txt', 'w')
            for i in range(0, len(self.modelPoints)):
                fileHandle.write('MW-3:{0:03d}:{1:03d}\n'.format(int(self.modelPoints[i][0]), int(int(self.modelPoints[i][1]))))
            fileHandle.close()
        except Exception as e:
            msg = 'Error saving modeling points to file [{0}] error: {1}!'.format(modelPointsFileName, e)
            self.logger.warning('Error loading modeling points to file [{0}] error: {1}!'.format(modelPointsFileName, e))
        finally:
            if fileHandle:
                fileHandle.close()
            return msg

    def loadModelPoints(self, modelPointsFileName, modeltype):
        p = []
        number = 0
        msg = None
        if modelPointsFileName.strip() == '':
            msg = 'No model points filename given!'
            self.logger.warning('No model points filename given!')
            return p, msg
        try:
            with open('config/' + modelPointsFileName + '.txt', 'r') as fileHandle:
                for line in fileHandle:
                    if line.startswith('GRID'):
                        # if grid, then its a TSX file (the sky x)
                        convertedLine = line.rstrip('\n').split()
                        point = (float(convertedLine[2]), float(convertedLine[3]))
                        number += 1
                        if modeltype == 'Refinement' and number > 3:
                            p.append(point)
                        elif modeltype == 'Base' and number <= 3:
                            p.append(point)
                    elif line.startswith('MW-3'):
                        # if mountwizzard, it's native version 3
                        convertedLine = line.rstrip('\n').split(':')
                        p.append((float(convertedLine[1]), float(convertedLine[2])))
                    else:
                        # format is same as Per's Model Maker
                        convertedLine = line.rstrip('\n').split(':')
                        point = (int(convertedLine[0]), int(convertedLine[1]))
                        if len(convertedLine) == 2 and modeltype == 'Full':
                            p.append(point)
                        elif len(convertedLine) != 2 and modeltype == 'Initial':
                            p.append(point)
        except Exception as e:
            msg = 'Error loading modeling points from file [{0}] error: {1}!'.format(modelPointsFileName, e)
            self.logger.warning('Error loading modeling points from file [{0}] error: {1}!'.format(modelPointsFileName, e))
        finally:
            return p, msg

    def sortPoints(self):
        points = self.ModelPoints
        if len(points) == 0:
            self.logger.warning('There are no points to sort')
            return
        westSide = []
        eastSide = []
        a = sorted(points, key=operator.itemgetter(0))
        for i in range(0, len(a)):
            if a[i][0] >= 180:
                westSide.append((a[i][0], a[i][1]))
            else:
                eastSide.append((a[i][0], a[i][1]))
        westSide = sorted(westSide, key=operator.itemgetter(1))
        eastSide = sorted(eastSide, key=operator.itemgetter(1))
        self.modelPoints = westSide + eastSide
        self.app.workerModelingDispatcher.signalModelPointsRedraw.emit()

    def loadHorizonPoints(self, horizonPointsFileName, horizonByFile, horizonByAltitude, altitudeMinimumHorizon):
        self.horizonPoints = []
        if not (horizonByFile or horizonByAltitude):
            return
        hp = []
        msg = None
        if horizonByFile:
            if horizonPointsFileName == '':
                msg = 'No horizon points filename given !'
                return msg
            if not os.path.isfile(os.getcwd() + '/config/' + horizonPointsFileName + '.txt'):
                msg = 'Horizon points file does not exist !'
                self.logger.warning('Horizon points file does not exist')
            else:
                try:
                    with open(os.getcwd() + '/config/' + horizonPointsFileName + '.txt') as f:
                        for line in f:
                            if ':' in line:
                                # model maker format
                                m = line.rstrip('\n').split(':')
                            else:
                                # carte du ciel / skychart format
                                m = line.rstrip('\n').split(' ')
                            point = (int(m[0]), int(m[1]))
                            hp.append(point)
                    f.close()
                except Exception as e:
                    msg = 'Error loading horizon points: {0}'.format(e)
                    self.logger.error('Error loading horizon points: {0}'.format(e))
                    return msg
            hp = sorted(hp, key=operator.itemgetter(0))
        if len(hp) == 0:
            hp = ((0, 0), (360, 0))
        x = [i[0] for i in hp]
        y = [i[1] for i in hp]
        if horizonByAltitude:
            y = numpy.clip(y, altitudeMinimumHorizon, None)
        self.horizonPoints = [list(a) for a in zip(x, y)]
        return msg

    def saveHorizonPoints(self, horizonPointsFileName):
        msg = None
        fileHandle = None
        if horizonPointsFileName.strip() == '':
            msg = 'No horizon points filename given!'
            self.logger.warning('No Model Points Filename given!')
            return msg
        try:
            fileHandle = open(horizonPointsFileName + '.txt', 'w')
            for i in range(0, len(self.horizonPoints)):
                # saving in model maker format
                fileHandle.write('{0:03d}:{1:03d}\n'.format(int(self.horizonPoints[i][0]), int(int(self.horizonPoints[i][1]))))
            fileHandle.close()
        except Exception as e:
            msg = 'Error saving horizon points to file [{0}] error: {1}!'.format(horizonPointsFileName, e)
            self.logger.warning('Error loading horizon points to file [{0}] error: {1}!'.format(horizonPointsFileName, e))
        finally:
            if fileHandle:
                fileHandle.close()
            return msg

    def isAboveHorizonLine(self, point):
        x = range(0, 361)
        y = numpy.interp(x, [i[0] for i in self.horizonPoints], [i[1] for i in self.horizonPoints], left=None, right=None, period=None)
        if point[1] > y[int(point[0])]:
            return True
        else:
            return False

    def deleteBelowHorizonLine(self):
        i = 0
        while i < len(self.modelPoints):
            if self.isAboveHorizonLine(self.modelPoints[i]):
                i += 1
            else:
                del self.modelPoints[i]

    def deletePoints(self):
        self.modelPoints = list()
        self.app.workerModelingDispatcher.signalModelPointsRedraw.emit()

    def loadInitialPoints(self, filename):
        self.modelPoints, msg = self.loadModelPoints(filename, 'Initial')
        self.app.workerModelingDispatcher.signalModelPointsRedraw.emit()

    def loadFullPoints(self, filename, limitByHorizonMask, doSortingPoints):
        self.modelPoints, msg = self.loadModelPoints(filename, 'Full')
        if limitByHorizonMask:
            self.deleteBelowHorizonLine()
        if doSortingPoints:
            self.sortPoints()
        self.app.messageQueue.put('ToModel>{0:02d}'.format(len(self.modelPoints)))
        self.app.workerModelingDispatcher.signalModelPointsRedraw.emit()

    def generateDSOPoints(self, limitByHorizonMask, hoursPathLength, numberOfPathPoints, hoursPathLengthPreview):
        # we have no position of the mount -> therefore we can't calculate the path
        if 'RaJNow' not in self.app.workerMountDispatcher.data:
            return
        self.modelPoints = list()
        ra = copy.copy(self.app.workerMountDispatcher.data['RaJNow'])
        dec = copy.copy(self.app.workerMountDispatcher.data['DecJNow'])
        for i in range(0, numberOfPathPoints):
            ra = ra - float(i) * hoursPathLength / numberOfPathPoints - hoursPathLengthPreview
            az, alt = self.transform.transformERFA(ra, dec, 1)
            if alt > 0:
                self.modelPoints.append((az, alt))
        if limitByHorizonMask:
            self.deleteBelowHorizonLine()
        self.app.messageQueue.put('ToModel>{0:02d}'.format(len(self.modelPoints)))
        self.app.workerModelingDispatcher.signalModelPointsRedraw.emit()

    def generateMaxPoints(self, limitByHorizonMask, doSortingPoints):
        west = []
        east = []
        for dec in range(-10, 90, 10):
            if dec < 30:
                step = -15
            elif dec < 70:
                step = -10
            else:
                step = -30
            for ha in range(120, -120, step):
                az, alt = self.transform.transformERFA(ha / 10, dec, 1)
                if alt > 0:
                    if az > 180:
                        east.append((az, alt))
                    else:
                        west.append((az, alt))
        self.modelPoints = west + east
        if limitByHorizonMask:
            self.deleteBelowHorizonLine()
        if doSortingPoints:
            self.sortPoints()
        self.app.messageQueue.put('ToModel>{0:02d}'.format(len(self.modelPoints)))
        self.app.workerModelingDispatcher.signalModelPointsRedraw.emit(True)

    def generateNormalPoints(self, limitByHorizonMask, doSortingPoints):
        west = []
        east = []
        for dec in range(-15, 90, 15):
            if dec < 60:
                step = -10
            else:
                step = -20
            for ha in range(120, -120, step):
                az, alt = self.transform.transformERFA(ha / 10, dec, 1)
                if alt > 0:
                    if az > 180:
                        east.append((az, alt))
                    else:
                        west.append((az, alt))
        self.modelPoints = west + east
        if limitByHorizonMask:
            self.deleteBelowHorizonLine()
        if doSortingPoints:
            self.sortPoints()
        self.app.messageQueue.put('ToModel>{0:02d}'.format(len(self.modelPoints)))
        self.app.workerModelingDispatcher.signalModelPointsRedraw.emit()

    def generateMinPoints(self, limitByHorizonMask, doSortingPoints):
        west = list()
        east = list()
        for dec in range(-15, 90, 15):
            if dec < 60:
                step = -15
            else:
                step = -30
            for ha in range(120, -120, step):
                az, alt = self.transform.transformERFA(ha / 10, dec, 1)
                if alt > 0:
                    if az > 180:
                        east.append((az, alt))
                    else:
                        west.append((az, alt))
        self.modelPoints = west + east
        if limitByHorizonMask:
            self.deleteBelowHorizonLine()
        if doSortingPoints:
            self.sortPoints()
        self.app.messageQueue.put('ToModel>{0:02d}'.format(len(self.modelPoints)))
        self.app.workerModelingDispatcher.signalModelPointsRedraw.emit()

    def generateGridPoints(self, limitByHorizonMask, doSortingPoints, numberOfRows, numberOfColumns, altitudeMin, altitudeMax):
        self.modelPoints = list()
        for az in range(5, 360, int(360 / numberOfColumns)):
            for alt in range(altitudeMin, altitudeMax + 1, int((altitudeMax - altitudeMin) / (numberOfRows - 1))):
                self.modelPoints.append((az, alt))
        if limitByHorizonMask:
            self.deleteBelowHorizonLine()
        if doSortingPoints:
            self.sortPoints()
        self.app.messageQueue.put('ToModel>{0:02d}'.format(len(self.modelPoints)))
        self.app.workerModelingDispatcher.signalModelPointsRedraw.emit()

    def generateInitialPoints(self, azimuth, altitude, numberOfPoints):
        self.modelPoints = list()
        for i in range(0, numberOfPoints):
            azp = i * 360 / numberOfPoints + azimuth
            if azp > 360:
                azp -= 360
            azp = int(azp)
            point = (azp, altitude)
            self.modelPoints.append(point)
        self.app.workerModelingDispatcher.signalModelPointsRedraw.emit()
