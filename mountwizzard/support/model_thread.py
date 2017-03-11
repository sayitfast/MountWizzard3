############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017
#
# Licence APL2.0
#
############################################################

import logging
import math
import time
import datetime
import os
import shutil
import copy
import random
# threading
from PyQt5 import QtCore
from PyQt5 import QtWidgets
# library for fits file handling
import pyfits
# for the sorting
from operator import itemgetter
# for data storing
from support.analyse import Analyse


class Model(QtCore.QThread):
    logger = logging.getLogger(__name__)                                                                                    # logging enabling
    signalModelConnected = QtCore.pyqtSignal(bool, name='ModelConnected')                                                   # message for errors
    signalModelCommand = QtCore.pyqtSignal([str], name='ModelCommand')                                                      # commands to sgpro thread
    signalModelRedraw = QtCore.pyqtSignal(bool, name='ModelRedrawPoints')

    BLUE = 'background-color: rgb(42, 130, 218)'
    RED = 'background-color: red'
    DEFAULT = 'background-color: rgb(32,32,32); color: rgb(192,192,192)'
    REF_PICTURE = '/model001.py'

    def __init__(self, app):
        super().__init__()
        self.app = app                                                                                                      # class reference for dome control

        self.analyse = Analyse(self.app)                                                                                    # use Class for saving analyse data

        self.horizonPoints = []                                                                                             # point out of file for showing the horizon
        self.BasePoints = []                                                                                                # base point out of a file for modeling
        self.RefinementPoints = []                                                                                          # refinement point out of file for modeling
        self.alignmentPoints = []                                                                                           # placeholder for all points, which were modeled
        self.connected = False                                                                                              # connection to SGPro
        self.cancel = False                                                                                                 # cancelling the modeling
        self.modelrun = False
        self.modelAnalyseData = []                                                                                          # analyse data for model
        self.captureFile = 'model'                                                                                          # filename for capturing file
        self.counter = 0                                                                                                    # counter for main loop
        self.command = ''                                                                                                   # command buffer
        self.errSum = 0.0                                                                                                   # resetting all the counting data for the model
        self.numCheckPoints = 0                                                                                             # number og checkpoints done
        self.results = []                                                                                                   # error results
        self.sizeX = 0                                                                                                      # sizeX of subframe
        self.sizeY = 0                                                                                                      # sizeY of subframe
        self.offX = 0                                                                                                       # offsetX for subframe
        self.offY = 0                                                                                                       # offsetY for subframe
        self.signalModelCommand.connect(self.sendCommand)                                                                   # signal for receiving commands to modeling from GUI

    def run(self):                                                                                                          # runnable for doing the work
        self.counter = 0                                                                                                    # cyclic counter
        while True:                                                                                                         # thread loop for doing jobs
            if self.connected and self.app.mount.connected:
                if self.command == 'RunBaseModel':                                                                          # actually doing by receiving signals which enables
                    self.command = ''                                                                                       # only one command at a time, last wins
                    self.app.ui.btn_runBaseModel.setStyleSheet(self.BLUE)
                    self.runBaseModel()                                                                                     # should be refactored to queue only without signal
                    self.app.ui.btn_runBaseModel.setStyleSheet(self.DEFAULT)
                    self.app.ui.btn_cancelModel.setStyleSheet(self.DEFAULT)                                                 # button back to default color
                elif self.command == 'RunRefinementModel':                                                                  #
                    self.command = ''                                                                                       #
                    self.app.ui.btn_runRefinementModel.setStyleSheet(self.BLUE)
                    self.runRefinementModel()                                                                               #
                    self.app.ui.btn_runRefinementModel.setStyleSheet(self.DEFAULT)
                    self.app.ui.btn_cancelModel.setStyleSheet(self.DEFAULT)                                                 # button back to default color
                elif self.command == 'RunBatchModel':                                                                       #
                    self.command = ''                                                                                       #
                    self.app.ui.btn_runBatchModel.setStyleSheet(self.BLUE)
                    self.runBatchModel()                                                                                    #
                    self.app.ui.btn_runBatchModel.setStyleSheet(self.DEFAULT)
                elif self.command == 'RunCheckModel':                                                                       #
                    self.command = ''                                                                                       #
                    self.app.ui.btn_runCheckModel.setStyleSheet(self.BLUE)                                                  # button blue (running)
                    self.runCheckModel()                                                                                    #
                    self.app.ui.btn_runCheckModel.setStyleSheet(self.DEFAULT)
                    self.app.ui.btn_cancelModel.setStyleSheet(self.DEFAULT)                                                 # button back to default color
                elif self.command == 'RunAllModel':
                    self.command = ''
                    self.app.ui.btn_runAllModel.setStyleSheet(self.BLUE)                                                    # button blue (running)
                    self.runAllModel()
                    self.app.ui.btn_runAllModel.setStyleSheet(self.DEFAULT)
                    self.app.ui.btn_cancelModel.setStyleSheet(self.DEFAULT)                                                 # button back to default color
                elif self.command == 'RunTimeChangeModel':                                                                  #
                    self.command = ''                                                                                       #
                    self.app.ui.btn_runTimeChangeModel.setStyleSheet(self.BLUE)
                    self.runTimeChangeModel()                                                                               #
                    self.app.ui.btn_runTimeChangeModel.setStyleSheet(self.DEFAULT)
                    self.app.ui.btn_cancelAnalyseModel.setStyleSheet(self.DEFAULT)                                          # button back to default color
                elif self.command == 'RunHystereseModel':                                                                   #
                    self.command = ''                                                                                       #
                    self.app.ui.btn_runHystereseModel.setStyleSheet(self.BLUE)
                    self.runHystereseModel()                                                                                #
                    self.app.ui.btn_runHystereseModel.setStyleSheet(self.DEFAULT)
                    self.app.ui.btn_cancelAnalyseModel.setStyleSheet(self.DEFAULT)                                          # button back to default color
                elif self.command == 'ClearAlignmentModel':                                                                 #
                    self.command = ''                                                                                       #
                    self.app.ui.btn_clearAlignmentModel.setStyleSheet(self.BLUE)
                    self.app.modelLogQueue.put('Clearing alignment model - taking 4 seconds.\n')
                    self.clearAlignmentModel()                                                                              #
                    self.app.modelLogQueue.put('Model cleared!\n')
                    self.app.ui.btn_clearAlignmentModel.setStyleSheet(self.DEFAULT)
                elif self.command == 'LoadBasePoints':
                    self.command = ''
                    self.BasePoints = self.showBasePoints()
                    self.signalModelRedraw.emit(True)
                elif self.command == 'LoadRefinementPoints':
                    self.command = ''
                    self.RefinementPoints = self.showRefinementPoints()
                    self.signalModelRedraw.emit(True)
                elif self.command == 'SortRefinementPoints':                                                                #
                    self.command = ''                                                                                       #
                    self.sortPoints('refinement')
                    self.signalModelRedraw.emit(True)
                elif self.command == 'GenerateDSOPoints':                                                                   #
                    self.command = ''                                                                                       #
                    self.app.ui.btn_generateDSOPoints.setStyleSheet(self.BLUE)                                              # take some time, therefore coloring button during execution
                    self.RefinementPoints = self.generateDSOPoints()
                    self.signalModelRedraw.emit(True)
                    self.app.ui.btn_generateDSOPoints.setStyleSheet(self.DEFAULT)                                           # color button back, routine finished
                elif self.command == 'GenerateDensePoints':                                                                 #
                    self.command = ''                                                                                       #
                    self.app.ui.btn_generateDensePoints.setStyleSheet(self.BLUE)                                            # tale some time, color button fro showing running
                    self.RefinementPoints = self.generateDensePoints()
                    self.signalModelRedraw.emit(True)
                    self.app.ui.btn_generateDensePoints.setStyleSheet(self.DEFAULT)                                         # routing finished, coloring default
                elif self.command == 'GenerateNormalPoints':                                                                #
                    self.command = ''                                                                                       #
                    self.app.ui.btn_generateNormalPoints.setStyleSheet(self.BLUE)                                           # tale some time, color button fro showing running
                    self.RefinementPoints = self.generateNormalPoints()
                    self.signalModelRedraw.emit(True)
                    self.app.ui.btn_generateNormalPoints.setStyleSheet(self.DEFAULT)                                        # routing finished, coloring default
                elif self.command == 'GenerateGridPoints':                                                                  #
                    self.command = ''                                                                                       #
                    self.app.ui.btn_generateGridPoints.setStyleSheet(self.BLUE)                                             # take some time, therefore coloring button during execution
                    self.RefinementPoints = self.generateGridPoints()
                    self.signalModelRedraw.emit(True)
                    self.app.ui.btn_generateGridPoints.setStyleSheet(self.DEFAULT)                                          # color button back, routine finished
                elif self.command == 'GenerateBasePoints':                                                                  #
                    self.command = ''                                                                                       #
                    self.BasePoints = self.generateBasePoints()
                    self.signalModelRedraw.emit(True)
                elif self.command == 'DeleteBelowHorizonLine':
                    self.command = ''
                    self.deleteBelowHorizonLine()
                    self.signalModelRedraw.emit(True)
                elif self.command == 'DeletePoints':
                    self.command = ''
                    self.deletePoints()
                    self.signalModelRedraw.emit(True)
            if self.counter % 10 == 0:                                                                                      # standard cycles in model thread fast
                self.getStatusFast()                                                                                        # calling fast part of status
            if self.counter % 20 == 0:                                                                                      # standard cycles in model thread slow
                self.getStatusSlow()                                                                                        # calling slow part of status
            self.counter += 1                                                                                               # loop +1
            time.sleep(.1)                                                                                                  # wait for the next cycle
        self.ascom.Quit()
        pythoncom.CoUninitialize()
        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()

    @QtCore.Slot(str)
    def sendCommand(self, command):                                                                                         # dispatcher of commands inside thread
        if self.modelrun:
            if command == 'CancelModel':                                                                                    # check the command
                self.command = ''                                                                                           # reset the command
                self.cancel = True                                                                                          # set cancel flag
                self.app.ui.btn_cancelModel.setStyleSheet(self.RED)                                                         # reset color of button
            elif command == 'CancelAnalyseModel':                                                                           #
                self.command = ''                                                                                           #
                self.cancel = True                                                                                          #
                self.app.ui.btn_cancelAnalyseModel.setStyleSheet(self.RED)                                                  # reset color of button
        else:
            self.command = command                                                                                          # passing the command to main loop of thread

    def getStatusSlow(self):                                                                                                # check SGPro running
        suc, mes = self.app.cpObject.checkConnection()                                                                      # check status of cpObject
        self.connected = suc                                                                                                # set status for internal use
        self.signalModelConnected.emit(suc)                                                                                 # send status to GUI
        if not suc:                                                                                                         # otherwise
            self.logger.debug('getStatusSlow  -> No Camera connection: {0}'.format(mes))                                    # debug message

    def getStatusFast(self):                                                                                                # fast status
        pass                                                                                                                # actually no fast status

    @staticmethod
    def timeStamp():
        return time.strftime("%H:%M:%S", time.localtime())

    def loadModelPoints(self, modelPointsFileName, modeltype):                                                              # load model point file from MM als list from tuples
        p = []
        number = 0
        try:                                                                                                                # fault tolerance, if file io fails
            with open('config/' + modelPointsFileName) as fileHandle:                                                       # run over complete file
                for line in fileHandle:                                                                                     # run over lines
                    if line.startswith('GRID'):                                                                             # if grid, then its a TSX file
                        convertedLine = line.rstrip('\n').split()                                                           # format is TSX format
                        point = (float(convertedLine[2]), float(convertedLine[3]))                                          # take data from line
                        number += 1
                        if modeltype == 'refinement' and number > 3:                                                        # in MM format base and refinement are included
                            p.append(point)                                                                                 # add data to the adequate list
                        elif modeltype == 'base' and number <= 3:
                            p.append(point)                                                                                 # add data to the adequate list
                    else:
                        convertedLine = line.rstrip('\n').split(':')                                                        # format is same as Per's MM
                        point = (int(convertedLine[0]), int(convertedLine[1]))                                              # take data from line
                        if len(convertedLine) == 2 and modeltype == 'refinement':                                           # in MM format base and refinement are included
                            p.append(point)                                                                                 # add data to the adequate list
                        elif len(convertedLine) != 2 and modeltype == 'base':
                            p.append(point)
            fileHandle.close()                                                                                              # close file
        except Exception as e:                                                                                              # handle exception
            self.app.messageQueue.put('Error loading model points from {0} error:{1}!'.format(modelPointsFileName, e))      # Gui message
            self.logger.error('loadModelPoints -> {0} could not be loaded error{1}'.format(modelPointsFileName, e))         # log output
        finally:
            return p

    def sortPoints(self, modeltype):                                                                                        # sorting point for performance
        if modeltype == 'base':                                                                                             # check type of sorting
            points = self.BasePoints                                                                                        # starting with point equals base points
        else:                                                                                                               # otherwise
            points = self.RefinementPoints                                                                                  # take the refinement points
        if len(points) == 0:                                                                                                # if no basepoints, than no sort
            self.logger.warning('sortBasePoints -> There are no {0}points to sort'.format(modeltype))
            return
        westSide = []                                                                                                       # split west and east side of pier
        eastSide = []                                                                                                       # and reset them
        a = sorted(points, key=itemgetter(0))                                                                               # first sort for az
        for i in range(0, len(a)):                                                                                          # split flip sides
            if a[i][0] >= 180:                                                                                              # choose the right side
                westSide.append((a[i][0], a[i][1]))                                                                         # add the point tto list
            else:                                                                                                           #
                eastSide.append((a[i][0], a[i][1]))                                                                         #
        westSide = sorted(westSide, key=itemgetter(1))                                                                      # sort west flipside
        eastSide = sorted(eastSide, key=itemgetter(1))                                                                      # sort east flipside
        if modeltype == 'base':
            self.BasePoints = eastSide + westSide                                                                           # put them together
        else:
            self.RefinementPoints = eastSide + westSide                                                                     # put them together

    def loadHorizonPoints(self, horizonPointsFileName):                                                                     # load a ModelMaker model file, return base & refine points as lists of (az,alt) tuples
        self.horizonPoints = []                                                                                             # clear horizon variable
        if self.app.ui.checkUseMinimumHorizonLine.isChecked():
            minAlt = int(float(self.app.ui.altitudeMinimumHorizon.value()))
            hp = ((0, minAlt), (359, minAlt))
        else:
            if horizonPointsFileName == '':
                return
            hp = []                                                                                                         # clear cache
            if not os.path.isfile(os.getcwd() + '/config/' + horizonPointsFileName):
                self.app.messageQueue.put('Horizon points file does not exist !')                                           # show on GUI
                self.logger.error('loadHorizonPoints -> horizon points file does not exist !')                              # write to logger
            else:
                try:                                                                                                        # try opening the file
                    with open(os.getcwd() + '/config/' + horizonPointsFileName) as f:                                       # run through file
                        for line in f:                                                                                      # run through lines
                            m = line.rstrip('\n').split(':')                                                                # split the values
                            point = (int(m[0]), int(m[1]))                                                                  # get point data
                            hp.append(point)                                                                                # add the point
                    f.close()                                                                                               # close file again
                except Exception as e:                                                                                      # handle exception
                    self.app.messageQueue.put('Error loading horizon points: {0}'.format(e))                                # show on GUI
                    self.logger.error('loadHorizonPoints -> Error loading horizon points: {0}'.format(e))                   # write to logger
                    return                                                                                                  # stop routine
            hp = sorted(hp, key=itemgetter(0))                                                                              # list should be sorted, but I do it for security anyway
        az_last = 0                                                                                                         # starting azimuth
        alt_last = 0                                                                                                        # starting altitude
        for i in range(0, len(hp)):                                                                                         # run through all points an link them via line
            az_act = hp[i][0]                                                                                               # get az from point of file
            alt_act = hp[i][1]                                                                                              # get alt from point of file
            if az_act > az_last:                                                                                            # if act az is greater than last on, we have to draw a line
                incline = (alt_act - alt_last) / (az_act - az_last)                                                         # calculation the line incline
                for j in range(az_last, az_act):                                                                            # run through the space, where no points are given in the file
                    point = (j, int(alt_last + incline * (j - az_last)))                                                    # calculation value of next point
                    self.horizonPoints.append(point)                                                                        # add the interpolated point to list
            else:                                                                                                           # otherwise no interpolation
                self.horizonPoints.append(hp[i])                                                                            # add the point to list, no interpolation needed
            az_last = az_act                                                                                                # set az value to next point
            alt_last = alt_act                                                                                              # same to alt value

    def isAboveHorizonLine(self, point):                                                                                    # check, if point is above horizon list (by horizon file)
        if len(self.horizonPoints) > 0:                                                                                     # check if there are horizon points
            if point[1] > self.horizonPoints[int(point[0])][1]:                                                             # simple comparison. important: each Int(az) has value set
                return True                                                                                                 # point is above -> True
            else:                                                                                                           #
                return False                                                                                                # points are below the horizon line -> False
        else:                                                                                                               #
            return True                                                                                                     # if there is no horizon line, all are in

    def deleteBelowHorizonLine(self):                                                                                       # remove points from modeling, if below horizon
        i = 0                                                                                                               # list index
        while i < len(self.RefinementPoints):                                                                               # loop for generating list index of point which is below horizon
            if self.isAboveHorizonLine(self.RefinementPoints[i]):                                                           #
                i += 1                                                                                                      # if ok , keep him
            else:                                                                                                           #
                del self.RefinementPoints[i]                                                                                # otherwise delete point from list

    def deletePoints(self):
        self.BasePoints = []
        self.RefinementPoints = []

    def showBasePoints(self):
        value = self.loadModelPoints(self.app.ui.le_modelPointsFileName.text(), 'base')
        return value

    def showRefinementPoints(self):
        value = self.loadModelPoints(self.app.ui.le_modelPointsFileName.text(), 'refinement')
        return value

    def generateDSOPoints(self):                                                                                            # model points along dso path
        hours = int(float(self.app.ui.numberHoursDSO.value()))
        number = int(float(self.app.ui.numberPointsDSO.value()))
        preview = int(float(self.app.ui.numberHoursPreview.value()))
        raCopy = copy.copy(self.app.mount.ra)
        decCopy = copy.copy(self.app.mount.dec)
        value = []                                                                                                          # clear point list
        for i in range(0, number):                                                                                          # round model point from actual az alt position 24 hours
            ra = raCopy - float(i) * hours / number - preview
            az, alt = self.app.mount.transformNovas(ra, decCopy, 1)                                                         # transform to az alt
            if alt > 0:                                                                                                     # we only take point alt > 0
                value.append((az, alt))                                                                                     # add point to list
        return value

    def generateDensePoints(self):                                                                                          # generate pointcloud in greater circles of sky
        west = []                                                                                                           # no sorting, point will be for west and east prepared
        east = []                                                                                                           #
        for dec in range(-10, 90, 10):                                                                                      # range, actually referenced from european situation
            if dec < 30:                                                                                                    # has to be generalized
                step = -15                                                                                                  # lower dec, more point
            elif dec < 70:
                step = -10
            else:
                step = -30                                                                                                  # higher dec. less point (anyway denser)
            for ha in range(120, -120, step):                                                                               # for complete 24 hourangle
                az, alt = self.app.mount.transformNovas(ha / 10, dec, 1)                                                    # do the transformation to alt az
                if alt > 0:                                                                                                 # only point with alt > 0 are taken
                    if az > 180:                                                                                            # put to the right list
                        east.append((az, alt))                                                                              # add to east
                    else:
                        west.append((az, alt))                                                                              # add to west
        value = west + east
        return value                                                                                                        # combine pointlist

    def generateNormalPoints(self):
        west = []                                                                                                           # no sorting, point will be for west and east prepared
        east = []                                                                                                           #
        for dec in range(-15, 90, 15):                                                                                      # range, actually referenced from european situation
            if dec < 60:                                                                                                    # has to be generalized
                step = -10                                                                                                  # lower dec, more point
            else:
                step = -20                                                                                                  # higher dec. less point (anyway denser)
            for ha in range(120, -120, step):                                                                               # for complete 24 hourangle
                az, alt = self.app.mount.transformNovas(ha / 10, dec, 1)                                                    # do the transformation to alt az
                if alt > 0:                                                                                                 # only point with alt > 0 are taken
                    if az > 180:                                                                                            # put to the right list
                        east.append((az, alt))                                                                              # add to east
                    else:
                        west.append((az, alt))                                                                              # add to west
        value = west + east
        return value                                                                                                        # combine pointlist

    def generateGridPoints(self):                                                                                           # model points along dso path
        row = int(float(self.app.ui.numberGridPointsRow.value()))
        col = int(float(self.app.ui.numberGridPointsCol.value()))
        value = []                                                                                                          # clear point list
        for az in range(5, 360, int(360 / col)):                                                                            # make point for all azimuth
            for alt in range(10, 90, int(90 / row)):                                                                        # make point for all altitudes
                value.append((az, alt))                                                                                     # add point to list
        return value

    def generateBasePoints(self):                                                                                           # do base point equally distributed
        value = []
        az = float(self.app.ui.azimuthBase.value())                                                                         # get az value from gui
        alt = float(self.app.ui.altitudeBase.value())                                                                       # same to alt value
        for i in range(0, 3):                                                                                               # we need 3 basepoints
            azp = i * 120 + az                                                                                              # equal distance of 120 degree in az
            if azp > 360:                                                                                                   # value range 0-360
                azp -= 360                                                                                                  # shift it if necessary
            point = (azp, alt)                                                                                              # generate the point value az,alt
            value.append(point)                                                                                             # put it to list
        return value

    def clearAlignmentModel(self):
        self.modelAnalyseData = []
        self.app.commandQueue.put('ClearAlign')
        time.sleep(4)                                                                                                       # we are waiting 4 seconds like Per did (don't know if necessary)

    def runBaseModel(self):
        settlingTime = int(float(self.app.ui.settlingTime.value()))
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        if len(self.BasePoints) > 0:
            self.modelAnalyseData = self.runModel('Base', self.BasePoints, directory, settlingTime)
        else:
            self.logger.warning('runBaseModel -> There are no Basepoints to model')
        name = directory + '_test.dat'                                                                                      # generate name of analyse file
        if len(self.modelAnalyseData) > 0:
            self.app.ui.le_analyseFileName.setText(name)                                                                    # set data name in GUI to start over quickly
            self.analyse.saveData(self.modelAnalyseData, name)                                                              # save the data

    def runRefinementModel(self):
        settlingTime = int(float(self.app.ui.settlingTime.value()))
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        if len(self.RefinementPoints) > 0:
            self.modelAnalyseData = self.runModel('Refinement', self.RefinementPoints,
                                                  directory, settlingTime)
            name = directory + '_refinement.dat'                                                                            # generate name of analyse file
            if len(self.modelAnalyseData) > 0:
                self.app.ui.le_analyseFileName.setText(name)                                                                # set data name in GUI to start over quickly
                self.analyse.saveData(self.modelAnalyseData, name)                                                          # save the data
        else:
            self.logger.warning('runRefinementModel -> There are no Refinement Points to model')

    def runCheckModel(self):
        settlingTime = int(float(self.app.ui.settlingTime.value()))
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        points = self.BasePoints + self.RefinementPoints
        if len(points) > 0:                                                                                                 # there should be some points
            self.modelAnalyseData = self.runModel('Check', points, directory, settlingTime)                                 # run the analyse
            name = directory + '_check.dat'                                                                                 # generate name of analyse file
            if len(self.modelAnalyseData) > 0:
                self.app.ui.le_analyseFileName.setText(name)                                                                # set data name in GUI to start over quickly
                self.analyse.saveData(self.modelAnalyseData, name)                                                          # save the data
        else:                                                                                                               # otherwise omit the run
            self.logger.warning('runAnalyseModel -> There are no Refinement or Base Points to model')                       # write error log

    def runAllModel(self):
        settlingTime = int(float(self.app.ui.settlingTime.value()))
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        points = self.BasePoints + self.RefinementPoints
        if len(points) > 0:                                                                                                 # there should be some points
            self.modelAnalyseData = self.runModel('All', points, directory, settlingTime)                                   # run the analyse
            name = directory + '_all.dat'                                                                                   # generate name of analyse file
            if len(self.modelAnalyseData) > 0:
                self.app.ui.le_analyseFileName.setText(name)                                                                # set data name in GUI to start over quickly
                self.analyse.saveData(self.modelAnalyseData, name)                                                          # save the data
        else:                                                                                                               # otherwise omit the run
            self.logger.warning('runAllModel -> There are no Refinement or Base Points to model')                           # write error log

    def runTimeChangeModel(self):
        settlingTime = int(float(self.app.ui.delayTimeTimeChange.value()))                                                  # using settling time also for waiting / delay
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        points = []                                                                                                         # clear the points
        for i in range(0, int(float(self.app.ui.numberRunsTimeChange.value()))):                                            # generate the points
            points.append((int(self.app.ui.azimuthTimeChange.value()), int(self.app.ui.altitudeTimeChange.value()),
                           QtWidgets.QGraphicsTextItem(''), True))
        self.modelAnalyseData = self.runModel('TimeChange', points, directory, settlingTime)                                # run the analyse
        name = directory + '_timechange.dat'                                                                                # generate name of analyse file
        if len(self.modelAnalyseData) > 0:
            self.app.ui.le_analyseFileName.setText(name)                                                                    # set data name in GUI to start over quickly
            self.analyse.saveData(self.modelAnalyseData, name)                                                              # save the data

    def runHystereseModel(self):
        waitingTime = int(float(self.app.ui.settlingTime.value()))                                                          # using settling time also for waiting / delay
        alt1 = int(float(self.app.ui.altitudeHysterese1.value()))
        alt2 = int(float(self.app.ui.altitudeHysterese2.value()))
        az1 = int(float(self.app.ui.azimuthHysterese1.value()))
        az2 = int(float(self.app.ui.azimuthHysterese2.value()))
        numberRunsHysterese = int(float(self.app.ui.numberRunsHysterese.value()))
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        points = []
        for i in range(0, numberRunsHysterese):
            points.append((az1, alt1, QtWidgets.QGraphicsTextItem(''), True))
            points.append((az2, alt2, QtWidgets.QGraphicsTextItem(''), False))
        self.modelAnalyseData = self.runModel('Hysterese', points, directory, waitingTime)                                  # run the analyse
        name = directory + '_hysterese.dat'                                                                                 # generate name of analyse file
        self.app.ui.le_analyseFileName.setText(name)                                                                        # set data name in GUI to start over quickly
        if len(self.modelAnalyseData) > 0:
            self.app.ui.le_analyseFileName.setText(name)                                                                    # set data name in GUI to start over quickly
            self.analyse.saveData(self.modelAnalyseData, name)                                                              # save the data

    def runBatchModel(self):
        nameDataFile = self.app.ui.le_analyseFileName.text()
        self.logger.debug('runBatchModel  -> model from {0}'.format(nameDataFile))                                          # debug output
        data = self.analyse.loadData(nameDataFile)                                                                          # load data
        if not('ra_Jnow' in data and 'dec_Jnow' in data):                                                                   # you need stored mount positions
            self.logger.error('runBatchModel  -> ra_Jnow or dec_Jnow not in data file')                                     # debug output
            self.app.modelLogQueue.put('{0} - mount coordinates missing\n'.format(self.timeStamp()))                        # Gui Output
            return
        if not('ra_sol_Jnow' in data and 'dec_sol_Jnow' in data):                                                           # you need solved star positions
            self.logger.error('runBatchModel  -> ra_sol_Jnow or dec_sol_Jnow not in data file')                             # debug output
            self.app.modelLogQueue.put('{0} - solved data missing\n'.format(self.timeStamp()))                              # Gui Output
            return
        if not('pierside' in data and 'sidereal_time' in data):                                                             # you need sidereal time and pierside
            self.logger.error('runBatchModel  -> pierside and sidereal time not in data file')                              # debug output
            self.app.modelLogQueue.put('{0} - time and pierside missing\n'.format(self.timeStamp()))                        # Gui Output
            return
        self.app.mount.saveActualModel('BATCH')
        self.app.modelLogQueue.put('{0} - Start Batch model. Saving Actual model to BATCH\n'.format(self.timeStamp()))      # Gui Output
        self.app.mount.sendCommand('newalig')
        self.app.modelLogQueue.put('{0} - \tOpening Calculation\n'.format(self.timeStamp()))                                # Gui Output
        for i in range(0, len(data['index'])):
            command = 'newalpt{0},{1},{2},{3},{4},{5}'.format(self.app.mount.decimalToDegree(data['ra_Jnow'][i], False, True),
                                                              self.app.mount.decimalToDegree(data['dec_Jnow'][i], True, False),
                                                              data['pierside'][i],
                                                              self.app.mount.decimalToDegree(data['ra_sol_Jnow'][i], False, True),
                                                              self.app.mount.decimalToDegree(data['dec_sol_Jnow'][i], True, False),
                                                              self.app.mount.decimalToDegree(data['sidereal_time_float'][i], False, True))
            reply = self.app.mount.sendCommand(command)
            if reply == 'E':
                self.logger.error('runBatchModel  -> point {0} could not be added'.format(reply))                           # debug output
                self.app.modelLogQueue.put('{0} - \tPoint could not be added\n'.format(self.timeStamp()))                   # Gui Output
            else:
                self.app.modelLogQueue.put('{0} - \tAdded point {1} @ Az:{2}, Alt:{3} \n'
                                           .format(self.timeStamp(), reply, int(data['azimuth'][i]), int(data['altitude'][i])))  # Gui Output
        reply = self.app.mount.sendCommand('endalig')
        if reply == 'V':
            self.app.modelLogQueue.put('{0} - Model successful finished! \n'.format(self.timeStamp()))                      # Gui Output
            self.logger.error('runBatchModel  -> Model successful finished!')                                               # debug output
        else:
            self.app.modelLogQueue.put('{0} - Model could not be calculated with current data! \n'.format(self.timeStamp()))    # Gui Output
            self.logger.error('runBatchModel  -> Model could not be calculated with current data!')                         # debug output

    def slewMountDome(self, az, alt):                                                                                       # slewing mount and dome to alt az point
        self.app.commandQueue.put('Sz{0:03d}*{1:02d}'.format(int(az), int((az - int(az)) * 60 + 0.5)))                      # Azimuth setting
        self.app.commandQueue.put('Sa+{0:02d}*{1:02d}'.format(int(alt), int((alt - int(alt)) * 60 + 0.5)))                  # Altitude Setting
        self.app.commandQueue.put('MS')                                                                                     # initiate slewing with tracking at the end
        self.logger.debug('slewMountDome  -> Connected:{0}'.format(self.app.dome.connected))
        break_counter = 0
        while not self.app.mount.slewing:                                                                                   # wait for mount starting slewing
            time.sleep(0.1)                                                                                                 # loop time
            break_counter += 1
            if break_counter == 30:
                break
        if self.app.dome.connected == 1:                                                                                    # if there is a dome, should be slewed as well
            if az >= 360:
                az = 359.9
            elif az < 0.0:
                az = 0.0
            try:
                self.app.dome.ascom.SlewToAzimuth(float(az))                                                                # set azimuth coordinate
            except Exception as e:
                self.logger.error('slewMountDome  -> value: {0}, error: {1}'.format(az, e))
            self.logger.debug('slewMountDome  -> Azimuth:{0}'.format(az))
            while not self.app.mount.slewing:                                                                               # wait for mount starting slewing
                if self.cancel:
                    break
                time.sleep(0.1)                                                                                             # loop time
            while self.app.mount.slewing or self.app.dome.slewing:                                                          # wait for stop slewing mount or dome not slewing
                if self.cancel:
                    break
                time.sleep(0.1)                                                                                             # loop time
        else:
            while self.app.mount.slewing:                                                                                   # wait for tracking = 7 or dome not slewing
                if self.cancel:
                    break
                time.sleep(0.1)                                                                                             # loop time

    def prepareCaptureImageSubframes(self, scale, sizeX, sizeY, canSubframe, modelData):                                    # get camera data for doing subframes
        modelData['sizeX'] = 0                                                                                              # size inner window
        modelData['sizeY'] = 0                                                                                              # size inner window
        modelData['offX'] = 0                                                                                               # offset is half of the rest
        modelData['offY'] = 0                                                                                               # same in y
        modelData['canSubframe'] = False
        if canSubframe:                                                                                                     # if camera could do subframes
            modelData['sizeX'] = int(sizeX * scale)                                                                         # size inner window
            modelData['sizeY'] = int(sizeY * scale)                                                                         # size inner window
            modelData['offX'] = int((sizeX - sizeX) / 2)                                                                    # offset is half of the rest
            modelData['offY'] = int((sizeY - sizeY) / 2)                                                                    # same in y
            modelData['canSubframe'] = True                                                                                 # same in y
        else:                                                                                                               # otherwise error
            self.logger.warning('prepareCaptureSubframe-> Camera does not support subframe.')                               # log message
        return modelData                                                                                                    # default without subframe

    def capturingImage(self, modelData, simulation):                                                                        # capturing image
        if self.cancel:
            return False, 'Cancel modeling pressed', modelData
        st_fits_header = modelData['sidereal_time'][0:10]                                                                   # store local sideral time as well
        ra_fits_header = self.app.mount.decimalToDegree(modelData['ra_J2000'], False, False, ' ')                           # set the point coordinates from mount in J2000 as hint precision 2
        dec_fits_header = self.app.mount.decimalToDegree(modelData['dec_J2000'], True, False, ' ')                          # set dec as well
        raJnow_fits_header = self.app.mount.decimalToDegree(modelData['ra_Jnow'], False, True, ' ')                         # set the point coordinates from mount in J2000 as hint precision 2
        decJnow_fits_header = self.app.mount.decimalToDegree(modelData['dec_Jnow'], True, True, ' ')                        # set dec as well
        if modelData['pierside'] == '1':
            pierside_fits_header = 'E'
        else:
            pierside_fits_header = 'W'
        self.logger.debug('capturingImage -> modelData: {0}'.format(modelData))                                             # write logfile
        suc, mes, guid = self.app.cpObject.SgCaptureImage(binningMode=modelData['binning'],
                                                          exposureLength=modelData['exposure'],
                                                          iso=str(modelData['iso']),
                                                          gain=modelData['gainValue'],
                                                          speed=modelData['speed'],
                                                          frameType='Light',
                                                          filename=modelData['file'],
                                                          path=modelData['base_dir_images'],
                                                          useSubframe=modelData['canSubframe'],
                                                          posX=modelData['offX'],
                                                          posY=modelData['offY'],
                                                          width=modelData['sizeX'],
                                                          height=modelData['sizeY'])                                        # start imaging with parameters. HiSpeed and DSLR doesn't work with SGPro
        modelData['imagepath'] = ''
        self.logger.debug('captureImage   -> message: {0}'.format(mes))
        if suc:                                                                                                             # if we successfully starts imaging, we ca move on
            while True:                                                                                                     # waiting for the image download before proceeding
                suc, modelData['imagepath'] = self.app.cpObject.SgGetImagePath(guid)                                        # there is the image path, once the image is downloaded
                if suc:                                                                                                     # until then, the link is only the receipt
                    break                                                                                                   # stopping the loop
                else:                                                                                                       # otherwise
                    time.sleep(0.5)                                                                                         # wait for 0.5 seconds
            if simulation:
                shutil.copyfile(os.path.dirname(os.path.realpath(__file__)) + self.REF_PICTURE, modelData['imagepath'])     # copy reference file as simulation target
            else:
                self.logger.debug('capturingImage -> getImagePath-> suc: {0}, modelData{1}'.format(suc, modelData))         # debug output
                fitsFileHandle = pyfits.open(modelData['imagepath'], mode='update')                                         # open for adding field info
                fitsHeader = fitsFileHandle[0].header                                                                       # getting the header part
                fitsHeader['DATE-OBS'] = datetime.datetime.now().isoformat()                                                # set time to current time of the mount
                fitsHeader['OBJCTRA'] = ra_fits_header                                                                      # set ra in header from solver in J2000
                fitsHeader['OBJCTDEC'] = dec_fits_header                                                                    # set dec in header from solver in J2000
                fitsHeader['CDELT1'] = modelData['hint']                                                                    # x is the same as y
                fitsHeader['CDELT2'] = modelData['hint']                                                                    # and vice versa
                fitsHeader['MW_MRA'] = raJnow_fits_header                                                                   # reported RA of mount in JNOW
                fitsHeader['MW_MDEC'] = decJnow_fits_header                                                                 # reported DEC of mount in JNOW
                fitsHeader['MW_ST'] = st_fits_header                                                                        # reported local sideral time of mount from GS command
                fitsHeader['MW_MSIDE'] = pierside_fits_header                                                               # reported pierside of mount from SD command
                fitsHeader['MW_EXP'] = modelData['exposure']                                                                # store the exposure time as well
                fitsHeader['MW_AZ'] = modelData['azimuth']                                                                  # x is the same as y
                fitsHeader['MW_ALT'] = modelData['altitude']                                                                # and vice versa
                self.logger.debug('capturingImage -> DATE-OBS:{0}, OBJCTRA:{1} OBJTDEC:{2} CDELT:{3} MW_MRA:{4} '
                                  'MW_MDEC:{5} MW_ST:{6} MW_PIER:{7} MW_EXP:{8} MW_AZ:{9} MW_ALT:{10}'
                                  .format(fitsHeader['DATE-OBS'], fitsHeader['OBJCTRA'], fitsHeader['OBJCTDEC'],
                                          fitsHeader['CDELT1'], fitsHeader['MW_MRA'], fitsHeader['MW_MDEC'],
                                          fitsHeader['MW_ST'], fitsHeader['MW_MSIDE'], fitsHeader['MW_EXP'],
                                          fitsHeader['MW_AZ'], fitsHeader['MW_ALT']))                                       # write all header data to debug
                fitsFileHandle.flush()                                                                                      # write all to disk
                fitsFileHandle.close()                                                                                      # close FIT file
            return True, 'OK', modelData                                                                                    # return true OK and imagepath
        else:                                                                                                               # otherwise
            return False, mes, modelData                                                                                    # image capturing was failing, writing message from SGPro back

    def addSolveRandomValues(self, modelData):
        modelData['dec_sol'] = modelData['dec_J2000'] + (2 * random.random() - 1) / 360
        modelData['ra_sol'] = modelData['ra_J2000'] + (2 * random.random() - 1) / 3600
        modelData['scale'] = 1.3
        modelData['angle'] = 90
        modelData['timeTS'] = 2.5
        ra, dec = self.app.mount.transformNovas(modelData['ra_sol'], modelData['dec_sol'], 3)
        modelData['ra_sol_Jnow'] = ra
        modelData['dec_sol_Jnow'] = dec
        modelData['raError'] = (modelData['ra_sol'] - modelData['ra_J2000']) * 3600
        modelData['decError'] = (modelData['dec_sol'] - modelData['dec_J2000']) * 3600
        modelData['modelError'] = math.sqrt(modelData['raError'] * modelData['raError'] + modelData['decError'] * modelData['decError'])
        return modelData

    def solveImage(self, modeltype, modelData, simulation):                                                                 # solving image based on information inside the FITS files, no additional info
        if modeltype == 'Base':                                                                                             # base type could be done with blind solve
            suc, mes, guid = self.app.cpObject.SgSolveImage(modelData['imagepath'],
                                                            scaleHint=modelData['hint'],
                                                            blindSolve=modelData['blind'],
                                                            useFitsHeaders=True)
        else:                                                                                                               # otherwise we have no chance for blind solve
            suc, mes, guid = self.app.cpObject.SgSolveImage(modelData['imagepath'],
                                                            scaleHint=modelData['hint'],
                                                            blindSolve=False,
                                                            useFitsHeaders=True)                                            # solve without blind
        if not suc:
            self.logger.warning('solveImage     -> no start {0}'.format(mes))                                               # debug output
            return False, mes, modelData
        while True:                                                                                                         # retrieving solving data in loop
            suc, mes, ra_sol, dec_sol, scale, angle, timeTS = self.app.cpObject.SgGetSolvedImageData(guid)                  # retrieving the data from solver
            mes = mes.strip('\n')                                                                                           # sometimes there are heading \n in message
            if mes[:7] in ['Matched', 'Solve t', 'Valid s', 'succeed']:                                                     # if there is success, we can move on
                self.logger.debug('solveImage solv-> modelData {0}'.format(modelData))
                solved = True
                modelData['dec_sol'] = float(dec_sol)                                                                       # convert values to float, should be stored in float not string
                modelData['ra_sol'] = float(ra_sol)
                modelData['scale'] = float(scale)
                modelData['angle'] = float(angle)
                modelData['timeTS'] = float(timeTS)
                break
            elif mes != 'Solving':                                                                                          # general error
                solved = False
                break
            elif self.cancel:
                solved = False
                break
            else:                                                                                                           # otherwise
                if modelData['blind']:                                                                                      # when using blind solve, it takes 30-60 s
                    time.sleep(5)                                                                                           # therefore slow cycle
                else:                                                                                                       # local solver takes 1-2 s
                    time.sleep(.25)                                                                                         # therefore quicker cycle
        self.logger.debug('solveImage     -> suc:{0} mes:{1}'.format(suc, mes))                                             # debug output
        if solved:
            ra_sol_Jnow, dec_sol_Jnow = self.app.mount.transformNovas(modelData['ra_sol'], modelData['dec_sol'], 3)         # transform J2000 -> Jnow
            modelData['ra_sol_Jnow'] = ra_sol_Jnow                                                                          # ra in Jnow
            modelData['dec_sol_Jnow'] = dec_sol_Jnow                                                                        # dec in  Jnow
            modelData['raError'] = (modelData['ra_sol'] - modelData['ra_J2000']) * 3600                                     # calculate the alignment error ra
            modelData['decError'] = (modelData['dec_sol'] - modelData['dec_J2000']) * 3600                                  # calculate the alignment error dec
            modelData['modelError'] = math.sqrt(modelData['raError'] * modelData['raError'] + modelData['decError'] * modelData['decError'])
            fitsFileHandle = pyfits.open(modelData['imagepath'], mode='update')                                             # open for adding field info
            fitsHeader = fitsFileHandle[0].header                                                                           # getting the header part
            fitsHeader['MW_PRA'] = modelData['ra_sol_Jnow']
            fitsHeader['MW_PDEC'] = modelData['dec_sol_Jnow']
            fitsHeader['MW_SRA'] = modelData['ra_sol']
            fitsHeader['MW_SDEC'] = modelData['dec_sol']
            fitsHeader['MW_PSCAL'] = modelData['scale']
            fitsHeader['MW_PANGL'] = modelData['angle']
            fitsHeader['MW_PTS'] = modelData['timeTS']
            self.logger.debug('solvingImage   -> MW_PRA:{0} MW_PDEC:{1} MW_PSCAL:{2} MW_PANGL:{3} MW_PTS:{4}'.
                              format(fitsHeader['MW_PRA'], fitsHeader['MW_PDEC'], fitsHeader['MW_PSCAL'],
                                     fitsHeader['MW_PANGL'], fitsHeader['MW_PTS']))                                         # write all header data to debug
            fitsFileHandle.flush()                                                                                          # write all to disk
            fitsFileHandle.close()                                                                                          # close FIT file
            if simulation:
                modelData = self.addSolveRandomValues(modelData)
            return True, mes, modelData
        else:
            return False, mes, modelData

    def addRefinementStar(self, ra, dec):                                                                                   # add refinement star during model run
        self.logger.debug('addRefinementSt-> ra:{0} dec:{1}'.format(ra, dec))                                               # debug output
        self.app.mount.sendCommand('Sr{0}'.format(ra))                                                                      # Write jnow ra to mount
        self.app.mount.sendCommand('Sd{0}'.format(dec))                                                                     # Write jnow dec to mount
        reply = self.app.mount.sendCommand('CMS')                                                                           # send sync command (regardless what driver tells)
        if reply == 'E':                                                                                                    # 'E' says star could not be added
            self.logger.error('addRefinementSt-> error adding star')
            return False
        else:
            self.logger.debug('addRefinementSt-> refinement star added')
            return True                                                                                                     # simulation OK

    # noinspection PyUnresolvedReferences
    def runModel(self, modeltype, runPoints, directory, settlingTime):                                                      # model run routing
        modelData = dict()                                                                                                  # all model data
        results = list()                                                                                                    # results
        self.app.modelLogQueue.put('delete')                                                                                # deleting the logfile view
        self.app.modelLogQueue.put('{0} - Start {1} Model\n'.format(self.timeStamp(), modeltype))                           # Start informing user
        numCheckPoints = 0                                                                                                  # number og checkpoints done
        modelData['base_dir_images'] = self.app.ui.le_imageDirectoryName.text() + '/' + directory                           # define subdirectory for storing the images
        scaleSubframe = self.app.ui.scaleSubframe.value() / 100                                                             # scale subframe in percent
        suc, mes, sizeX, sizeY, canSubframe, gainValue = self.app.cpObject.SgGetCameraProps()                               # look for capabilities of cam
        modelData['gainValue'] = gainValue
        if suc:
            self.logger.debug('runModel       -> camera props: {0}, {1}, {2}'.format(sizeX, sizeY, canSubframe))            # debug data
        else:
            self.logger.warning('runModel       -> SgGetCameraProps with error: {0}'.format(mes))                           # log message
            self.app.modelLogQueue.put('{0} -\t {1} Model canceled! Error: {2}\n'.format(self.timeStamp(), modeltype, mes))
            return {}                                                                                                       # if cancel or failure, that empty dict has to returned
        modelData = self.prepareCaptureImageSubframes(scaleSubframe, sizeX, sizeY, canSubframe, modelData)                  # calculate the necessary data
        if modelData['sizeX'] == 800 and modelData['sizeY'] == 600:
            simulation = True
        else:
            simulation = False
        if not self.app.ui.checkDoSubframe.isChecked():                                                                     # should we run with subframes
            modelData['canSubframe'] = False                                                                                # set default values
        self.logger.debug('runModel       -> modelData: {0}'.format(modelData))                                             # log data
        self.app.commandQueue.put('PO')                                                                                     # unpark to start slewing
        self.app.commandQueue.put('AP')                                                                                     # tracking on during the picture taking
        if not os.path.isdir(modelData['base_dir_images']):                                                                 # if analyse dir doesn't exist, make it
            os.makedirs(modelData['base_dir_images'])                                                                       # if path doesn't exist, generate is
        for i, (p_az, p_alt, p_item, p_solve) in enumerate(runPoints):                                                      # run through all model points
            modelData['azimuth'] = p_az
            modelData['altitude'] = p_alt
            self.modelrun = True                                                                                            # sets the run flag true
            if p_item.isVisible():                                                                                          # is the model point to be run = true ?
                if self.cancel:                                                                                             # here is the entry point for canceling the model run
                    self.app.modelLogQueue.put('{0} -\t {1} Model canceled !\n'.format(self.timeStamp(), modeltype))        # we keep all the stars before
                    self.app.commandQueue.put('AP')                                                                         # tracking on during the picture taking
                    self.cancel = False                                                                                     # and make it back to default
                    break                                                                                                   # finally stopping model run
                self.app.modelLogQueue.put('{0} - Slewing to point {1:2d}  @ Az: {2:3.0f}\xb0 Alt: {3:2.0f}\xb0\n'
                                           .format(self.timeStamp(), i+1, p_az, p_alt))                                     # Gui Output
                self.logger.debug('runModel       -> point {0:2d}  Az: {1:3.0f} Alt: {2:2.0f}'.format(i+1, p_az, p_alt))    # Debug output
                if modeltype in ['TimeChange']:                                                                             # in time change there is only slew for the first time, than only track during imaging
                    if i == 0:
                        self.slewMountDome(p_az, p_alt)                                                                     # slewing mount and dome to az/alt for first slew only
                        self.app.commandQueue.put('RT9')                                                                    # stop tracking until next round
                else:
                    self.slewMountDome(p_az, p_alt)                                                                         # slewing mount and dome to az/alt for model point and analyse
                self.app.modelLogQueue.put('{0} -\t Wait mount settling / delay time:  {1:02d} sec'
                                           .format(self.timeStamp(), settlingTime))                                         # Gui Output
                timeCounter = settlingTime
                while timeCounter > 0:                                                                                      # waiting for settling time and showing data
                    time.sleep(1)                                                                                           # only step n seconds
                    timeCounter -= 1                                                                                        # count down
                    self.app.modelLogQueue.put('backspace')
                    self.app.modelLogQueue.put('{0:02d} sec'.format(timeCounter))                                           # write to gui
                self.app.modelLogQueue.put('\n')                                                                            # clear gui for next line
            if p_item.isVisible() and p_solve:                                                                              # is the model point to be run = visible and to be evaluated p_solve = True
                if self.app.ui.checkFastDownload.isChecked():                                                               # if camera is supporting high speed download
                    modelData['speed'] = 'HiSpeed'
                else:                                                                                                       # otherwise
                    modelData['speed'] = 'Normal'
                modelData['file'] = self.captureFile + '{0:03d}'.format(i) + '.fit'                                         # generate filename for storing image
                modelData['binning'] = int(float(self.app.ui.cameraBin.value()))
                modelData['exposure'] = int(float(self.app.ui.cameraExposure.value()))
                modelData['iso'] = int(float(self.app.ui.isoSetting.value()))
                modelData['blind'] = self.app.ui.checkUseBlindSolve.isChecked()
                modelData['hint'] = float(self.app.ui.pixelSize.value()) * modelData['binning'] * 206.6 / float(self.app.ui.focalLength.value())
                modelData['sidereal_time'] = self.app.mount.sidereal_time[0:9]
                modelData['sidereal_time_float'] = self.app.mount.degStringToDecimal(self.app.mount.sidereal_time[0:9])
                modelData['ra_J2000'] = self.app.mount.ra
                modelData['dec_J2000'] = self.app.mount.dec
                modelData['ra_Jnow'] = self.app.mount.raJnow
                modelData['dec_Jnow'] = self.app.mount.decJnow
                modelData['pierside'] = self.app.mount.pierside
                modelData['index'] = i
                modelData['refractionTemp'] = self.app.mount.refractionTemp                                                 # set it if string available
                modelData['refractionPress'] = self.app.mount.refractionPressure                                            # set it if string available
                if modeltype in ['TimeChange']:
                    self.app.commandQueue.put('AP')                                                                         # tracking on during the picture taking
                self.app.modelLogQueue.put('{0} -\t Capturing image for model point {1:2d}\n'.format(self.timeStamp(), i + 1))   # gui output
                suc, mes, imagepath = self.capturingImage(modelData, simulation)                                            # capturing image and store position (ra,dec), time, (az,alt)
                if modeltype in ['TimeChange']:
                    self.app.commandQueue.put('RT9')                                                                        # stop tracking until next round
                self.logger.debug('runModel-capImg-> suc:{0} mes:{1}'.format(suc, mes))                                     # Debug
                if suc:                                                                                                     # if a picture could be taken
                    self.app.modelLogQueue.put('{0} -\t Solving Image\n'.format(self.timeStamp()))                          # output for user GUI
                    suc, mes, modelData = self.solveImage(modeltype, modelData, simulation)                                 # solve the position and returning the values
                    self.app.modelLogQueue.put('{0} -\t Image path: {1}\n'.format(self.timeStamp(), modelData['imagepath']))     # Gui output
                    if suc:                                                                                                 # solved data is there, we can sync
                        if modeltype in ['Base', 'Refinement', 'All']:                                                      #
                            suc = self.addRefinementStar(modelData['ra_sol_Jnow'], modelData['dec_sol_Jnow'])               # sync the actual star to resolved coordinates in JNOW
                            if suc:
                                self.app.modelLogQueue.put('{0} -\t Point added\n'.format(self.timeStamp()))
                            else:
                                self.app.modelLogQueue.put('{0} -\t Point could not be added - please check!\n'.format(self.timeStamp()))
                        numCheckPoints += 1                                                                                 # increase index for synced stars
                        results.append(copy.copy(modelData))                                                                # adding point for matrix
                        self.logger.debug('runModel       -> raE:{0} decE:{1} ind:{2}'
                                          .format(modelData['raError'], modelData['decError'], numCheckPoints))             # generating debug output
                        p_item.setVisible(False)                                                                            # set the relating modeled point invisible
                        self.app.modelLogQueue.put('{0} -\t RA_diff:  {1:2.1f}    DEC_diff: {2:2.1f}\n'
                                                   .format(self.timeStamp(), modelData['raError'], modelData['decError']))  # data for User
                        self.logger.debug('runModel       -> modelData: {0}'.format(modelData))                             # log output
                    else:                                                                                                   # no success in solving
                        if os.path.isfile(modelData['imagepath']):
                            os.remove(modelData['imagepath'])                                                               # delete unsolved image
                        self.app.modelLogQueue.put('{0} -\t Solving error: {1}\n'.format(self.timeStamp(), mes))            # Gui output
        if not self.app.ui.checkKeepImages.isChecked():                                                                     # check if the model images should be kept
            shutil.rmtree(modelData['base_dir_images'], ignore_errors=True)                                                 # otherwise just delete them
        self.app.modelLogQueue.put('{0} - {1} Model run finished. Number of modeled points: {2:3d}\n\n'
                                   .format(self.timeStamp(), modeltype, numCheckPoints))                                    # GUI output
        self.modelrun = False
        return results                                                                                                      # return results for analysing
