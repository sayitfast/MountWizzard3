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
# threading
from PyQt5 import QtCore
from PyQt5 import QtWidgets
# library for fits file handling
import pyfits
# for the sorting
from operator import itemgetter
# for handling SGPro interface
from support.sgpro import SGPro
from support.analyse import Analyse


class Model(QtCore.QThread):
    logger = logging.getLogger(__name__)                                                                                    # logging enabling
    signalModelConnected = QtCore.pyqtSignal(bool, name='ModelConnected')                                                   # message for errors
    signalModelCommand = QtCore.pyqtSignal([str], name='ModelCommand')                                                      # commands to sgpro thread
    signalModelRedraw = QtCore.pyqtSignal(bool, name='ModelRedrawPoints')

    BLUE = 'background-color: rgb(42, 130, 218)'
    RED = 'background-color: red'
    DEFAULT = 'background-color: rgb(32,32,32); color: rgb(192,192,192)'

    def __init__(self, ui, mount, dome, messageQueue, commandQueue, dataQueue, LogQueue):
        super().__init__()
        self.signalModelCommand.connect(self.command)                                                                       # signal for receiving commands to modeling from GUI
        self.mount = mount                                                                                                  # class reference for mount control
        self.dome = dome                                                                                                    # class reference for dome control
        self.ui = ui                                                                                                        # class for GUI object
        self.messageQueue = messageQueue                                                                                    # queue for sending error messages in GUI
        self.commandQueue = commandQueue                                                                                    # command queue for mount
        self.dataQueue = dataQueue                                                                                          # Feedback queue for Data
        self.LogQueue = LogQueue                                                                                            # GUI output windows messages in modeling windows
        self.SGPro = SGPro()                                                                                                # wrapper class SGPro REST API
        self.Analyse = Analyse()                                                                                            # use Class for saving analyse data
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
        self.sub = False                                                                                                    # use subframes when imaging
        self.sizeX = 0                                                                                                      # sizeX of subframe
        self.sizeY = 0                                                                                                      # sizeY of subframe
        self.offX = 0                                                                                                       # offsetX for subframe
        self.offY = 0                                                                                                       # offsetY for subframe

    def run(self):                                                                                                          # runnable for doing the work
        self.counter = 0                                                                                                    # cyclic counter
        while True:                                                                                                         # thread loop for doing jobs
            if self.connected and self.mount.connected:
                if self.command == 'RunBaseModel':                                                                          # actually doing by receiving signals which enables
                    self.command = ''                                                                                       # only one command at a time, last wins
                    self.ui.btn_runBaseModel.setStyleSheet(self.BLUE)
                    self.runBaseModel()                                                                                     # should be refactored to queue only without signal
                    self.ui.btn_runBaseModel.setStyleSheet(self.DEFAULT)
                    self.ui.btn_cancelBaseModel.setStyleSheet(self.DEFAULT)                                                 # button back to default color
                elif self.command == 'RunRefinementModel':                                                                  #
                    self.command = ''                                                                                       #
                    self.ui.btn_runRefinementModel.setStyleSheet(self.BLUE)
                    self.runRefinementModel()                                                                               #
                    self.ui.btn_runRefinementModel.setStyleSheet(self.DEFAULT)
                    self.ui.btn_cancelRefinementModel.setStyleSheet(self.DEFAULT)                                           # button back to default color
                elif self.command == 'RunAnalyseModel':                                                                     #
                    self.command = ''                                                                                       #
                    self.ui.btn_runAnalyseModel.setStyleSheet(self.BLUE)                                                    # button blue (running)
                    self.runAnalyseModel()                                                                                  #
                    self.ui.btn_runAnalyseModel.setStyleSheet(self.DEFAULT)
                    self.ui.btn_cancelAnalyseModel.setStyleSheet(self.DEFAULT)                                              # button back to default color
                elif self.command == 'RunTimeChangeModel':                                                                  #
                    self.command = ''                                                                                       #
                    self.ui.btn_runTimeChangeModel.setStyleSheet(self.BLUE)
                    self.runTimeChangeModel()                                                                               #
                    self.ui.btn_runTimeChangeModel.setStyleSheet(self.DEFAULT)
                    self.ui.btn_cancelTimeChangeModel.setStyleSheet(self.DEFAULT)                                           # button back to default color
                elif self.command == 'RunHystereseModel':                                                                   #
                    self.command = ''                                                                                       #
                    self.ui.btn_runHystereseModel.setStyleSheet(self.BLUE)
                    self.runHystereseModel()                                                                                #
                    self.ui.btn_runHystereseModel.setStyleSheet(self.DEFAULT)
                    self.ui.btn_cancelHystereseModel.setStyleSheet(self.DEFAULT)                                            # button back to default color
                elif self.command == 'ClearAlignmentModel':                                                                 #
                    self.command = ''                                                                                       #
                    self.ui.btn_clearAlignmentModel.setStyleSheet(self.BLUE)
                    self.LogQueue.put('Clearing alignment model - taking 4 seconds.\n')
                    self.clearAlignmentModel()                                                                              #
                    self.ui.btn_clearAlignmentModel.setStyleSheet(self.DEFAULT)
                elif self.command == 'LoadBasePoints':
                    self.command = ''
                    self.showBasePoints()
                elif self.command == 'LoadRefinementPoints':
                    self.command = ''
                    self.showRefinementPoints()
                elif self.command == 'SortRefinementPoints':                                                                #
                    self.command = ''                                                                                       #
                    self.sortPoints('refinement')                                                                           #
                elif self.command == 'GenerateDSOPoints':                                                                   #
                    self.command = ''                                                                                       #
                    self.ui.btn_generateDSOPoints.setStyleSheet(self.BLUE)                                                  # take some time, therefore coloring button during execution
                    self.generateDSOPoints()                                                                                #
                    self.ui.btn_generateDSOPoints.setStyleSheet(self.DEFAULT)                                               # color button back, routine finished
                elif self.command == 'GenerateDensePoints':                                                                 #
                    self.command = ''                                                                                       #
                    self.ui.btn_generateDensePoints.setStyleSheet(self.BLUE)                                                # tale some time, color button fro showing running
                    self.generateDensePoints()                                                                              #
                    self.ui.btn_generateDensePoints.setStyleSheet(self.DEFAULT)                                             # routing finished, coloring default
                elif self.command == 'GenerateNormalPoints':                                                                #
                    self.command = ''                                                                                       #
                    self.ui.btn_generateNormalPoints.setStyleSheet(self.BLUE)                                               # tale some time, color button fro showing running
                    self.generateNormalPoints()                                                                             #
                    self.ui.btn_generateNormalPoints.setStyleSheet(self.DEFAULT)                                            # routing finished, coloring default
                elif self.command == 'GenerateGridPoints':                                                                  #
                    self.command = ''                                                                                       #
                    self.ui.btn_generateGridPoints.setStyleSheet(self.BLUE)                                                 # take some time, therefore coloring button during execution
                    self.generateGridPoints()                                                                               #
                    self.ui.btn_generateGridPoints.setStyleSheet(self.DEFAULT)                                              # color button back, routine finished
                elif self.command == 'GenerateBasePoints':                                                                  #
                    self.command = ''                                                                                       #
                    self.generateBasePoints()                                                                               #
                elif self.command == 'DeleteBelowHorizonLine':                                                              #
                    self.command = ''                                                                                       #
                    self.deleteBelowHorizonLine()                                                                           #
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

    def command(self, command):                                                                                             # dispatcher of commands inside thread
        if self.modelrun:
            if command == 'CancelBaseModel':                                                                                # check the command
                self.command = ''                                                                                           # reset the command
                self.cancel = True                                                                                          # set cancel flag
                self.ui.btn_cancelBaseModel.setStyleSheet(self.RED)                                                         # reset color of button
            elif command == 'CancelRefinementModel':                                                                        # check the command
                self.command = ''                                                                                           # reset the command buffer
                self.cancel = True                                                                                          # set cancel flag
                self.ui.btn_cancelRefinementModel.setStyleSheet(self.RED)                                                   # reset color of button
            elif command == 'CancelAnalyseModel':                                                                           #
                self.command = ''                                                                                           #
                self.cancel = True                                                                                          #
                self.ui.btn_cancelAnalyseModel.setStyleSheet(self.RED)                                                      # reset color of button
            elif command == 'CancelTimeChangeModel':                                                                        #
                self.command = ''                                                                                           #
                self.cancel = True                                                                                          #
                self.ui.btn_cancelTimeChangeModel.setStyleSheet(self.RED)                                                   # reset color of button
            elif command == 'CancelHystereseModel':                                                                         #
                self.command = ''                                                                                           #
                self.cancel = True                                                                                          #
                self.ui.btn_cancelHystereseModel.setStyleSheet(self.RED)                                                    # reset color of button
        else:
            self.command = command                                                                                          # passing the command to main loop of thread

    def getStatusSlow(self):                                                                                                # check SGPro running
        suc, mes = self.SGPro.checkConnection()                                                                             # check status of SGPro
        self.connected = suc                                                                                                # set status for internal use
        self.signalModelConnected.emit(suc)                                                                                 # send status to GUI
        if not suc:                                                                                                         # otherwise
            self.logger.debug('getStatusSlow  -> No SGPro connection: {0}'.format(mes))                                     # debug message

    def getStatusFast(self):                                                                                                # fast status
        pass                                                                                                                # actually no fast status

    def loadModelPoints(self, modelPointsFileName, modeltype):                                                              # load model point file from MM als list from tuples
        p = []
        try:                                                                                                                # fault tolerance, if file io fails
            with open('config/' + modelPointsFileName) as fileHandle:                                                       # run over complete file
                for line in fileHandle:                                                                                     # run over lines
                    convertedLine = line.rstrip('\n').split(':')                                                            # format is same as Per's MM
                    Point = (int(convertedLine[0]), int(convertedLine[1]))                                                  # take data from line
                    if len(convertedLine) == 2 and modeltype == 'refinement':                                               # in MM format base and refinement are included
                        p.append(Point)                                                                                     # add data to the adequate list
                    elif len(convertedLine) != 2 and modeltype == 'base':
                        p.append(Point)
            fileHandle.close()                                                                                              # close file
        except Exception as e:                                                                                              # handle exception
            self.messageQueue.put('Error loading model points from {0} error:{1}!'.format(modelPointsFileName, e))          # Gui message
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
            self.signalModelRedrawBase.emit(True)                                                                           # update graphics
            self.signalModelRedraw.emit(True)                                                                               # update graphics
        else:
            self.RefinementPoints = eastSide + westSide                                                                     # put them together
            self.signalModelRedrawRefinement.emit(True)                                                                     # update graphics
            self.signalModelRedraw.emit(True)                                                                               # update graphics

    def loadHorizonPoints(self, horizonPointsFileName):                                                                     # load a ModelMaker model file, return base & refine points as lists of (az,alt) tuples
        hp = []                                                                                                             # clear cache
        if not os.path.isfile(os.getcwd() + '/config/' + horizonPointsFileName):
            self.messageQueue.put('Horizon points file does not exist !')                                                   # show on GUI
            self.logger.error('loadHorizonPoints -> horizon points file does not exist !')                                  # write to logger
        else:
            try:                                                                                                            # try opening the file
                with open(os.getcwd() + '/config/' + horizonPointsFileName) as f:                                           # run through file
                    for line in f:                                                                                          # run through lines
                        m = line.rstrip('\n').split(':')                                                                    # split the values
                        point = (int(m[0]), int(m[1]))                                                                      # get point data
                        hp.append(point)                                                                                    # add the point
                f.close()                                                                                                   # close file again
            except Exception as e:                                                                                          # handle exception
                self.messageQueue.put('Error loading horizon points: {0}'.format(e))                                        # show on GUI
                self.logger.error('loadHorizonPoints -> Error loading horizon points: {0}'.format(e))                       # write to logger
                return                                                                                                      # stop routine
        hp = sorted(hp, key=itemgetter(0))                                                                                  # list should be sorted, but I do it for security anyway
        self.horizonPoints = []                                                                                             # clear horizon variable
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
        self.signalModelRedraw.emit(True)

    def transformCelestialHorizontal(self, ha, dec):
        self.mount.transform.SetJ2000(ha, dec)                                                                              # set J2000 ra, dec
        alt = self.mount.transform.ElevationTopocentric                                                                     # convert alt
        az = self.mount.transform.AzimuthTopocentric                                                                        # convert az
        return az, alt

    def showBasePoints(self):
        self.BasePoints = self.loadModelPoints(self.ui.le_modelPointsFileName.text(), 'base')
        self.signalModelRedraw.emit(True)

    def showRefinementPoints(self):
        self.RefinementPoints = self.loadModelPoints(self.ui.le_modelPointsFileName.text(), 'refinement')
        self.signalModelRedraw.emit(True)

    def generateDSOPoints(self):                                                                                            # model points along dso path
        self.RefinementPoints = []                                                                                          # clear point list
        if len(self.ui.le_trackRA.text()) == 0 or len(self.ui.le_trackDEC.text()) == 0:
            return
        for i in range(0, 25):                                                                                              # round model point from actual az alt position 24 hours
            ra = self.mount.degStringToDecimal(self.ui.le_trackRA.text()) + i / 12.0                                        # Transform text to hours format
            if ra >= 24:
                ra -= 24
            dec = self.mount.degStringToDecimal(self.ui.le_trackDEC.text())                                                 # Transform text to degree format
            self.mount.transform.SetJ2000(ra, dec)                                                                          # set data in J2000
            alt = int(self.mount.transform.ElevationTopocentric)                                                            # take az data
            az = int(self.mount.transform.AzimuthTopocentric)                                                               # take alt data
            if alt > 0:                                                                                                     # we only take point alt > 0
                self.RefinementPoints.append((az, alt))                                                                     # add point to list
            self.signalModelRedraw.emit(True)

    def generateDensePoints(self):                                                                                          # generate pointcloud in greater circles of sky
        self.RefinementPoints = []                                                                                          # clear pointlist
        west = []                                                                                                           # no sorting, point will be for west and east prepared
        east = []                                                                                                           #
        for dec in range(-10, 90, 10):                                                                                      # range, actually referenced from european situation
            if dec < 30:                                                                                                    # has to be generalized
                step = -15                                                                                                  # lower dec, more point
            elif dec < 70:
                step = -10
            else:
                step = -30                                                                                                  # higher dec. less point (anyway denser)
            for ha in range(239, 0, step):                                                                                  # for complete 24 hourangle
                az, alt = self.transformCelestialHorizontal(ha/10, dec)                                                     # do the transformation to alt az
                if alt > 0:                                                                                                 # only point with alt > 0 are taken
                    if az > 180:                                                                                            # put to the right list
                        east.append((int(az), int(alt)))                                                                    # add to east
                    else:
                        west.append((int(az), int(alt)))                                                                    # add to west
            self.RefinementPoints = west + east                                                                             # combine pointlist
            self.signalModelRedraw.emit(True)

    def generateNormalPoints(self):
        self.RefinementPoints = []                                                                                          # clear pointlist
        west = []                                                                                                           # no sorting, point will be for west and east prepared
        east = []                                                                                                           #
        for dec in range(-15, 90, 15):                                                                                      # range, actually referenced from european situation
            if dec < 60:                                                                                                    # has to be generalized
                step = -10                                                                                                  # lower dec, more point
            else:
                step = -20                                                                                                  # higher dec. less point (anyway denser)
            for ha in range(239, 0, step):                                                                                  # for complete 24 hourangle
                az, alt = self.transformCelestialHorizontal(ha / 10, dec)                                                   # do the transformation to alt az

                if alt > 0:                                                                                                 # only point with alt > 0 are taken
                    if az > 180:                                                                                            # put to the right list
                        east.append((int(az), int(alt)))                                                                    # add to east
                    else:
                        west.append((int(az), int(alt)))                                                                    # add to west
            self.RefinementPoints = west + east                                                                             # combine pointlist
            self.signalModelRedraw.emit(True)

    def generateGridPoints(self):                                                                                           # model points along dso path
        row = int(float(self.ui.numberGridPointsRow.value()))
        col = int(float(self.ui.numberGridPointsCol.value()))
        self.RefinementPoints = []                                                                                          # clear point list
        for az in range(5, 360, int(360 / col)):                                                                            # make point for all azimuth
            for alt in range(10, 90, int(90 / row)):                                                                        # make point for all altitudes
                self.RefinementPoints.append((az, alt))                                                                     # add point to list
            time.sleep(.05)
            self.signalModelRedraw.emit(True)

    def generateBasePoints(self):                                                                                           # do base point equally distributed
        self.BasePoints = []                                                                                                # clear it
        az = int(float(self.ui.azimuthBase.value()))                                                                        # get az value from gui
        alt = int(float(self.ui.altitudeBase.value()))                                                                      # same to alt value
        for i in range(0, 3):                                                                                               # we need 3 basepoints
            azp = i * 120 + az                                                                                              # equal distance of 120 degree in az
            if azp > 360:                                                                                                   # value range 0-360
                azp -= 360                                                                                                  # shift it if necessary
            point = (azp, alt)                                                                                              # generate the point value az,alt
            self.BasePoints.append(point)                                                                                   # put it to list
        self.signalModelRedraw.emit(True)

    def clearAlignmentModel(self):
        self.modelAnalyseData = []
        self.commandQueue.put('ClearAlign')
        time.sleep(4)                                                                                                       # we are waiting 4 seconds like Per did (don't know if necessary)

    def runBaseModel(self):
        settlingTime = int(float(self.ui.settlingTime.value()))
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        if len(self.BasePoints) > 0:
            self.modelAnalyseData = self.runModel('Base', self.BasePoints, directory, settlingTime)
        else:
            self.logger.warning('runBaseModel -> There are no Basepoints to model')

    def runRefinementModel(self):
        settlingTime = int(float(self.ui.settlingTime.value()))
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        if len(self.RefinementPoints) > 0:
            self.modelAnalyseData = self.runModel('Refinement', self.RefinementPoints,
                                                  directory, settlingTime)
        else:
            self.logger.warning('runRefinementModel -> There are no Refinement Points to model')
        name = directory + '_refinement.txt'                                                                                # generate name of analyse file
        self.ui.le_analyseFileName.setText(name)                                                                            # set data name in GUI to start over quickly
        self.Analyse.saveData(self.modelAnalyseData, name)                                                                  # save the data

    def runAnalyseModel(self):
        settlingTime = int(float(self.ui.settlingTime.value()))
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        if len(self.RefinementPoints + self.BasePoints) > 0:                                                                # there should be some points
            self.modelAnalyseData = self.runModel('Analyse', self.BasePoints + self.RefinementPoints,
                                                  directory, settlingTime)         # run the analyse
        else:                                                                                                               # otherwise omit the run
            self.logger.warning('runAnalyseModel -> There are no Refinement or Base Points to model')                       # write error log
        name = directory + '_analyse.txt'                                                                                   # generate name of analyse file
        self.ui.le_analyseFileName.setText(name)                                                                            # set data name in GUI to start over quickly
        self.Analyse.saveData(self.modelAnalyseData, name)                                                                  # save the data

    def runTimeChangeModel(self):
        settlingTime = int(float(self.ui.delayTimeTimeChange.value()))                                                      # using settling time also for waiting / delay
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        points = []                                                                                                         # clear the points
        for i in range(0, int(float(self.ui.numberRunsTimeChange.value()))):                                                # generate the points
            points.append((int(self.ui.azimuthTimeChange.value()), int(self.ui.altitudeTimeChange.value()),
                           QtWidgets.QGraphicsTextItem(''), True))
        self.modelAnalyseData = self.runModel('TimeChange', points, directory, settlingTime)                                # run the analyse
        name = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + '_timechange.txt'                                        # generate name of analyse file
        self.ui.le_analyseFileName.setText(name)                                                                            # set data name in GUI to start over quickly
        self.Analyse.saveData(self.modelAnalyseData, name)                                                                  # save the data

    def runHystereseModel(self):
        settlingTime = int(float(self.ui.settlingTime.value()))                                                             # using settling time also for waiting / delay
        directory = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
        points = [(270, 85, QtWidgets.QGraphicsTextItem(''), True),
                  (000, 20, QtWidgets.QGraphicsTextItem(''), False),
                  (270, 85, QtWidgets.QGraphicsTextItem(''), True),
                  (90, 20, QtWidgets.QGraphicsTextItem(''), False),
                  (270, 85, QtWidgets.QGraphicsTextItem(''), True),
                  (180, 20, QtWidgets.QGraphicsTextItem(''), False),
                  (270, 85, QtWidgets.QGraphicsTextItem(''), True),
                  (90, 85, QtWidgets.QGraphicsTextItem(''), True),
                  (181, 20, QtWidgets.QGraphicsTextItem(''), False),
                  (90, 85, QtWidgets.QGraphicsTextItem(''), True),
                  (270, 20, QtWidgets.QGraphicsTextItem(''), False),
                  (90, 85, QtWidgets.QGraphicsTextItem(''), True),
                  (359, 20, QtWidgets.QGraphicsTextItem(''), False),
                  (90, 85, QtWidgets.QGraphicsTextItem(''), True)]
        self.modelAnalyseData = self.runModel('Hysterese', points, directory, settlingTime)                                 # run the analyse
        name = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + '_hysterese.txt'                                         # generate name of analyse file
        self.ui.le_analyseFileName.setText(name)                                                                            # set data name in GUI to start over quickly
        self.Analyse.saveData(self.modelAnalyseData, name)                                                                  # save the data

    def slewMountDome(self, az, alt):                                                                                       # slewing mount and dome to alt az point
        self.commandQueue.put('Sz{0:03d}*00'.format(az))                                                                    # Azimuth setting
        self.commandQueue.put('Sa+{0:02d}*00'.format(alt))                                                                  # Altitude Setting
        self.commandQueue.put('MS')                                                                                         # initiate slewing with tracking at the end
        self.logger.debug('slewMountDome  -> Connected:{0}'.format(self.dome.connected))
        if self.dome.connected == 1:                                                                                        # if there is a dome, should be slewed as well
            self.dome.ascom.SlewToAzimuth(float(az))                                                                        # set azimuth coordinate
            self.logger.debug('slewMountDome  -> Azimuth:{0}'.format(az))
            while not self.mount.slewing:                                                                                   # wait for mount starting slewing
                time.sleep(0.1)                                                                                             # loop time
            while self.mount.slewing or self.dome.slewing:                                                                  # wait for stop slewing mount or dome not slewing
                time.sleep(0.1)                                                                                             # loop time
        else:
            while not self.mount.slewing:                                                                                   # wait for mount starting slewing
                time.sleep(0.1)                                                                                             # loop time
            while self.mount.slewing:                                                                                       # wait for tracking = 7 or dome not slewing
                time.sleep(0.1)                                                                                             # loop time

    def prepareCaptureImageSubframes(self, scale):                                                                          # get camera data for doing subframes
        suc, mes, sizeX, sizeY, canSubframe = self.SGPro.SgGetCameraProps()                                                 # look for capabilities of cam
        self.logger.debug('prepareCaptureSubframe-> camera props: {0}, {1}, {2}'.format(sizeX, sizeY, canSubframe))         # debug data
        if suc:                                                                                                             # if cam props are there
            if canSubframe:                                                                                                 # if camera could do subframes
                sizeXsub = int(sizeX * scale)                                                                               # size inner window
                sizeYsub = int(sizeY * scale)                                                                               # size inner window
                offX = int((sizeX - sizeXsub) / 2)                                                                          # offset is half of the rest
                offY = int((sizeY - sizeYsub) / 2)                                                                          # same in y
                return True, sizeXsub, sizeYsub, offX, offY                                                                 # return values
            else:                                                                                                           # otherwise error
                self.logger.warning('prepareCaptureSubframe-> Camera does not support subframe error: {0}'.format(mes))     # log message
                return False, 0, 0, 0, 0                                                                                    # default without subframe

    def getTestImage(self, index, imagepath):
        if os.path.isfile(os.getcwd() + '/testimages/model{0:03d}.fit'.format(index)):                                      # check existing image file
            shutil.copyfile(os.getcwd() + '/testimages/model{0:03d}.fit'.format(index), imagepath)                          # copy testfile instead of imaging
        else:
            if index == 0:                                                                                                  # test images should start with 0
                self.logger.error('getTestImage   -> no test image files available !')
                return False
            else:
                shutil.copyfile(os.getcwd() + '/testimages/model{0:03d}.fit'.format(0), imagepath)                          # copy first testfile instead of imaging
                return True

    def capturingImage(self, st, ra, dec, raJnow, decJnow, az, alt, binning, exposure, isoMode, sub,
                       sX, sY, oX, oY, speed, file, hint, pierside):                                                        # capturing image
        st_fits_header = st[0:10]                                                                                           # store local sideral time as well
        ra_fits_header = self.mount.decimalToDegree(ra, False, False, ' ')                                                  # set the point coordinates from mount in J2000 as hint precision 2
        dec_fits_header = self.mount.decimalToDegree(dec, True, False, ' ')                                                 # set dec as well
        raJnow_fits_header = self.mount.decimalToDegree(raJnow, False, True, ' ')                                           # set the point coordinates from mount in J2000 as hint precision 2
        decJnow_fits_header = self.mount.decimalToDegree(decJnow, True, True, ' ')                                          # set dec as well
        if pierside == '1':
            pierside_fits_header = 'E'
        else:
            pierside_fits_header = 'W'
        self.logger.debug('capturingImage -> params: BIN:{0} ISO:{1} EXP:{2} Path:{3}'
                          .format(binning, isoMode, exposure, file))                                                        # write logfile
        suc, mes, guid = self.SGPro.SgCaptureImage(binningMode=binning,
                                                   exposureLength=exposure,
                                                   isoMode=isoMode, iso=str(isoMode),
                                                   gain='High', speed=speed, frameType='Light',
                                                   path=file,
                                                   useSubframe=sub, posX=oX, posY=oY, width=sX, height=sY)                  # start imaging with parameters. HiSpeed and DSLR doesn't work with SGPro
        if suc:                                                                                                             # if we successfully starts imaging, we ca move on
            while True:                                                                                                     # waiting for the image download before proceeding
                suc, imagepath = self.SGPro.SgGetImagePath(guid)                                                            # there is the image path, once the image is downloaded
                if suc:                                                                                                     # until then, the link is only the receipt
                    break                                                                                                   # stopping the loop
                else:                                                                                                       # otherwise
                    time.sleep(0.5)                                                                                         # wait for 0.5 seconds
            self.logger.debug('capturingImage -> getImagePath-> suc: {0}, imagepath: {1}'.format(suc, imagepath))           # debug output
            fitsFileHandle = pyfits.open(imagepath, mode='update')                                                          # open for adding field info
            fitsHeader = fitsFileHandle[0].header                                                                           # getting the header part
            fitsHeader['DATE-OBS'] = datetime.datetime.now().isoformat()                                                    # set time to current time of the mount
            fitsHeader['OBJCTRA'] = ra_fits_header                                                                          # set ra in header from solver in J2000
            fitsHeader['OBJCTDEC'] = dec_fits_header                                                                        # set dec in header from solver in J2000
            fitsHeader['CDELT1'] = hint                                                                                     # x is the same as y
            fitsHeader['CDELT2'] = hint                                                                                     # and vice versa
            fitsHeader['MW_MRA'] = raJnow_fits_header                                                                       # reported RA of mount in JNOW
            fitsHeader['MW_MDEC'] = decJnow_fits_header                                                                     # reported DEC of mount in JNOW
            fitsHeader['MW_ST'] = st_fits_header                                                                            # reported local sideral time of mount from GS command
            fitsHeader['MW_MSIDE'] = pierside_fits_header                                                                   # reported pierside of mount from SD command
            fitsHeader['MW_EXP'] = exposure                                                                                 # store the exposure time as well
            fitsHeader['MW_AZ'] = az                                                                                        # x is the same as y
            fitsHeader['MW_ALT'] = alt                                                                                      # and vice versa
            self.logger.debug('capturingImage -> DATE-OBS:{0}, OBJCTRA:{1} OBJTDEC:{2} CDELT:{3} MW_MRA:{4} '
                              'MW_MDEC:{5} MW_ST:{6} MW_PIER:{7} MW_EXP:{8} MW_AZ:{9} MW_ALT:{10}'
                              .format(fitsHeader['DATE-OBS'], fitsHeader['OBJCTRA'], fitsHeader['OBJCTDEC'],
                                      fitsHeader['CDELT1'], fitsHeader['MW_MRA'], fitsHeader['MW_MDEC'],
                                      fitsHeader['MW_ST'], fitsHeader['MW_MSIDE'], fitsHeader['MW_EXP'],
                                      fitsHeader['MW_AZ'], fitsHeader['MW_ALT']))                                           # write all header data to debug
            fitsFileHandle.flush()                                                                                          # write all to disk
            fitsFileHandle.close()                                                                                          # close FIT file
            return True, 'OK', imagepath                                                                                    # return true OK and imagepath
        else:                                                                                                               # otherwise
            return False, mes, ''                                                                                           # image capturing was failing, writing message from SGPro back

    def solveImage(self, modeltype, blind, imagepath, hint, refractionTemp):                                                # solving image based on information inside the FITS files, no additional info
        if modeltype == 'Base':                                                                                             # base type could be done with blind solve
            suc, mes, guid = self.SGPro.SgSolveImage(imagepath, scaleHint=hint,
                                                     blindSolve=blind,
                                                     useFitsHeaders=True)
        else:                                                                                                               # otherwise we have no chance for blind solve
            suc, mes, guid = self.SGPro.SgSolveImage(imagepath, scaleHint=hint,
                                                     blindSolve=False,
                                                     useFitsHeaders=True)                                                   # solve without blind
        if not suc:
            self.logger.warning('solveImage     -> no start {0}'.format(mes))                                           # debug output
            return False, mes
        while True:                                                                                                         # retrieving solving data in loop
            suc, mes, ra_sol, dec_sol, scale, angle, timeTS = self.SGPro.SgGetSolvedImageData(guid)                         # retrieving the data from solver
            dec_sol = float(dec_sol)                                                                                        # convert to float
            ra_sol = float(ra_sol)                                                                                          #
            scale = float(scale)                                                                                            #
            angle = float(angle)                                                                                            #
            timeTS = float(timeTS)                                                                                          #
            mes = mes.strip('\n')                                                                                           # sometimes there are heading \n in message
            if mes[:7] in ['Matched', 'Solve t', 'Valid s']:                                                                # if there is success, we can move on
                self.logger.debug('solveImage solv-> ra_sol:{0} dec_sol:{1} suc:{2} mes:{3} scale:{4} angle:{5} '
                                  'timeTS: {6}'.format(ra_sol, dec_sol, suc, mes, scale, angle, timeTS))
                solved = True
                break
            elif mes != 'Solving':                                                                                          # general error
                solved = False
                break
            else:                                                                                                           # otherwise
                if blind:                                                                                                   # when using blind solve, it takes 30-60 s
                    time.sleep(5)                                                                                           # therefore slow cycle
                else:                                                                                                       # local solver takes 1-2 s
                    time.sleep(.25)                                                                                         # therefore quicker cycle
        self.logger.debug('solveImage     -> suc:{0} mes:{1}'.format(suc, mes))                                             # debug output
        if solved:
            self.mount.transform.SiteTemperature = refractionTemp                                                           # set refraction temp in converter
            self.mount.transform.SetJ2000(float(ra_sol), float(dec_sol))                                                    # set coordinates in J2000 (solver)
            ra_sol_Jnow = self.mount.decimalToDegree(self.mount.transform.RATopocentric, False, True)                       # convert to Jnow
            dec_sol_Jnow = self.mount.decimalToDegree(self.mount.transform.DecTopocentric, True, True)                      # convert to Jnow
            fitsFileHandle = pyfits.open(imagepath, mode='update')                                                          # open for adding field info
            fitsHeader = fitsFileHandle[0].header                                                                           # getting the header part
            fitsHeader['MW_PRA'] = ra_sol_Jnow
            fitsHeader['MW_PDEC'] = dec_sol_Jnow
            fitsHeader['MW_SRA'] = ra_sol
            fitsHeader['MW_SDEC'] = dec_sol
            fitsHeader['MW_PSCAL'] = scale
            fitsHeader['MW_PANGL'] = angle
            fitsHeader['MW_PTS'] = timeTS
            self.logger.debug('solvingImage   -> MW_PRA:{0} MW_PDEC:{1} MW_PSCAL:{2} MW_PANGL:{3} MW_PTS:{4}'.
                              format(fitsHeader['MW_PRA'], fitsHeader['MW_PDEC'], fitsHeader['MW_PSCAL'],
                                     fitsHeader['MW_PANGL'], fitsHeader['MW_PTS']))                                          # write all header data to debug
            fitsFileHandle.flush()  # write all to disk
            fitsFileHandle.close()  # close FIT file
            return True, mes
        else:
            return False, mes

    def addRefinementStar(self, ra, dec):                                                                                   # add refinement star during model run
        self.commandQueue.put('Sr{0}'.format(ra))                                                                        # Write jnow ra to mount
        self.commandQueue.put('Sd{0}'.format(dec))                                                                        # Write jnow dec to mount
        self.logger.debug('addRefinementSt-> ra:{0} dec:{1}'.format(ra, dec))                                               # debug output
        print(ra, dec)
        # self.commandQueue.put('CMS')                                                                                      # send sync command (regardless what driver tells)
        # TODO: implement event loop to get feedback of the return value of the command
        return True                                                                                                         # simulation OK

    def extractFitsData(self, imagepath):
        fitsFileHandle = pyfits.open(imagepath)
        fitsHeader = fitsFileHandle[0].header
        ra_sol = fitsHeader['MW_SRA']
        dec_sol = fitsHeader['MW_SDEC']
        ra_m = self.mount.degStringToDecimal(fitsHeader['OBJCTRA'])
        dec_m = self.mount.degStringToDecimal(fitsHeader['OBJCTDEC'])
        ra_sol_Jnow = fitsHeader['MW_PRA']
        dec_sol_Jnow = fitsHeader['MW_PDEC']
        scale = fitsHeader['MW_PSCAL']
        angle = fitsHeader['MW_PANGL']
        timeTS = fitsHeader['MW_PTS']
        fitsFileHandle.close()  # close FIT file
        return ra_sol, dec_sol, ra_sol_Jnow, dec_sol_Jnow, ra_m, dec_m, scale, angle, timeTS

    def runModel(self, modeltype, runPoints, directory, settlingTime):                                                                 # model run routing
        self.LogQueue.put('delete')                                                                                         # deleting the logfile view
        self.LogQueue.put('{0} - Start {1} Model\n'.format(time.strftime("%H:%M:%S", time.localtime()), modeltype))         # Start informing user
        self.errSum = 0.0                                                                                                   # resetting all the counting data for the model
        self.numCheckPoints = 0                                                                                             # number og checkpoints done
        self.results = []                                                                                                   # error results
        if self.ui.checkDoSubframe.isChecked():                                                                             # should we run with subframes
            scaleSubframe = self.ui.scaleSubframe.value() / 100                                                             # scale subframe in percent
            self.sub, self.sizeX, self.sizeY, self.offX, self.offY = self.prepareCaptureImageSubframes(scaleSubframe)       # calculate the necessary data
        else:                                                                                                               # otherwise
            self.sub = False                                                                                                # set default values
            self.sizeX = 0                                                                                                  #
            self.sizeY = 0                                                                                                  #
            self.offX = 0                                                                                                   #
            self.offY = 0                                                                                                   #
        self.logger.debug('runModel       -> subframe: {0}, {1}, {2}, {3}, {4}'
                          .format(self.sub, self.sizeX, self.sizeY, self.offX, self.offY))                                  # log data
        self.commandQueue.put('PO')                                                                                         # unpark to start slewing
        self.commandQueue.put('AP')                                                                                         # tracking on during the picture taking
        base_dir_images = self.ui.le_imageDirectoryName.text() + '/' + directory                                            # define subdirectory for storing the images
        if not os.path.isdir(base_dir_images):                                                                              # if analyse dir doesn't exist, make it
            os.makedirs(base_dir_images)                                                                                    # if path doesn't exist, generate is
        for i, (p_az, p_alt, p_item, p_solve) in enumerate(runPoints):                                                      # run through all model points
            self.modelrun = True                                                                                            # sets the run flag true
            if p_item.isVisible():                                                                                          # is the model point to be run = true ?
                if self.cancel:                                                                                             # here is the entry point for canceling the model run
                    self.LogQueue.put('{0} -\t {1} Model canceled !\n'
                                      .format(time.strftime("%H:%M:%S", time.localtime()), modeltype))                       # we keep all the stars before
                    self.commandQueue.put('AP')                                                                             # tracking on during the picture taking
                    self.cancel = False                                                                                     # and make it back to default
                    break                                                                                                   # finally stopping model run
                self.LogQueue.put('{0} - Slewing to point {1:2d}  @ Az: {2:3d}\xb0 Alt: {3:2d}\xb0\n'
                                  .format(time.strftime("%H:%M:%S", time.localtime()), i+1, p_az, p_alt))                   # Gui Output
                self.logger.debug('runModel       -> point {0:2d}  Az: {1:3d} Alt: {2:2d}'.format(i+1, p_az, p_alt))        # Debug output
                if modeltype in ['TimeChange']:                                                                             # in time change there is only slew for the first time, than only track during imaging
                    if i == 0:
                        self.slewMountDome(p_az, p_alt)                                                                     # slewing mount and dome to az/alt for first slew only
                        self.commandQueue.put('RT9')                                                                        # stop tracking until next round
                else:
                    self.slewMountDome(p_az, p_alt)                                                                         # slewing mount and dome to az/alt for model point and analyse
                self.LogQueue.put('{0} -\t Wait mount settling / delay time {1:d} second(s) '
                                  .format(time.strftime("%H:%M:%S", time.localtime()), settlingTime))                       # Gui Output
                timeCounter = settlingTime
                while timeCounter > 0:                                                                                      # waiting for settling time and showing data
                    time.sleep(1)                                                                                           # only step n seconds
                    timeCounter -= 1                                                                                        # count down
                    self.LogQueue.put(' {0:d}'.format(timeCounter))                                                         # write to gui
                self.LogQueue.put('\n')                                                                                     # clear gui for next line
            if p_item.isVisible() and p_solve:                                                                              # is the model point to be run = true ?
                if self.ui.checkFastDownload.isChecked():                                                                   # if camera is supporting high speed download
                    speed = 'HiSpeed'                                                                                       # we can use it for improved modeling speed
                else:                                                                                                       # otherwise
                    speed = 'Normal'                                                                                        # standard speed
                binning = int(float(self.ui.cameraBin.value()))                                                             # get binning value from gui
                exposure = int(float(self.ui.cameraExposure.value()))                                                       # get exposure value from gui
                isoMode = int(float(self.ui.isoSetting.value()))                                                            # get isoMode value from GUI
                blind = self.ui.checkUseBlindSolve.isChecked()                                                              # get data from gui
                hint = float(self.ui.pixelSize.value()) * binning * 206.6 / float(self.ui.focalLength.value())              # calculating hint with focal length and pixel size of cam
                file = base_dir_images + '/' + self.captureFile + '{0:03d}'.format(i) + '.fit'                              # generate filepath for storing image
                if modeltype in ['TimeChange']:
                    self.commandQueue.put('AP')                                                                             # tracking on during the picture taking
                self.LogQueue.put('{0} -\t Capturing image for model point {1:2d}\n'
                                  .format(time.strftime("%H:%M:%S", time.localtime()), i + 1))                              # gui output
                suc, mes, imagepath = self.capturingImage(self.mount.sidereal_time, self.mount.ra, self.mount.dec,
                                                          self.mount.raJnow, self.mount.decJnow,
                                                          p_az, p_alt, binning, exposure, isoMode, self.sub, self.sizeX,
                                                          self.sizeY, self.offX, self.offY, speed, file, hint,
                                                          self.mount.pierside)                                              # capturing image and store position (ra,dec), time, (az,alt)
                if modeltype in ['TimeChange']:
                    self.commandQueue.put('RT9')                                                                            # stop tracking until next round
                self.logger.debug('runModel-capImg-> suc:{0} mes:{1}'.format(suc, mes))                                     # Debug
                if suc:                                                                                                     # if a picture could be taken
                    self.LogQueue.put('{0} -\t Solving Image\n'.format(time.strftime("%H:%M:%S", time.localtime())))        # output for user GUI
                    if len(self.ui.le_refractionTemperature.text()) > 0:  # set refraction temp
                        refractionTemp = float(self.ui.le_refractionTemperature.text())  # set it if string available
                    else:  # otherwise
                        refractionTemp = 20.0  # set it to 20.0 degree c
                    suc, mes = self.solveImage(modeltype, blind, imagepath, hint, refractionTemp)                           # solve the position and returning the values
                    self.LogQueue.put('{0} -\t Image path: {1}\n'
                                      .format(time.strftime("%H:%M:%S", time.localtime()), imagepath))                      # Gui output
                    if suc:                                                                                                 # solved data is there, we can sync
                        ra_sol, dec_sol, ra_sol_Jnow, dec_sol_Jnow, ra_m, dec_m, scale, angle, timeTS = self.extractFitsData(imagepath)
                        if modeltype in ['Base', 'Refinement']:                                                             #
                            self.addRefinementStar(ra_sol_Jnow, dec_sol_Jnow)                                               # sync the actual star to resolved coordinates in JNOW
                        self.numCheckPoints += 1                                                                            # increase index for synced stars
                        raE = (ra_sol - ra_m) * 3600                                                                        # calculate the alignment error ra
                        decE = (dec_sol - dec_m) * 3600                                                                     # calculate the alignment error dec
                        err = math.sqrt(raE * raE + decE * decE)                                                            # accumulate sum of error vectors squared
                        self.logger.debug('runModel       -> raE:{0} decE:{1} ind:{2}'.format(raE, decE, self.numCheckPoints))  # generating debug output
                        self.results.append((i, p_az, p_alt, ra_m, dec_m, ra_sol, dec_sol, raE, decE, err))                 # adding point for matrix
                        p_item.setVisible(False)                                                                            # set the relating modeled point invisible
                        self.LogQueue.put('{0} -\t RA: {1:3.1f}  DEC: {2:3.1f}  Angle: {3:3.1f}  RAdiff: {4:2.1f}  '
                                          'DECdiff: {5:2.1f}  Took: {6:3.1f}s\n'
                                          .format(time.strftime("%H:%M:%S", time.localtime()), ra_sol, dec_sol,
                                                  angle, raE, decE, timeTS))                                                # data for User
                        self.logger.debug('runModel       -> RA: {0:3.1f}  DEC: {1:3.1f}  Scale: {2:2.2f}  Angle: {3:3.1f}  '
                                          'Error: {4:2.1f}  Took: {5:3.1f}s'.format(ra_sol, dec_sol, scale, angle, err, timeTS))    # log output
                    else:                                                                                                   # no success in solving
                        os.remove(imagepath)                                                                                # delete unsolved image
                        self.LogQueue.put('{0} -\t Solving error: {1}\n'
                                          .format(time.strftime("%H:%M:%S", time.localtime()), mes))                        # Gui output
        if not self.ui.checkKeepImages.isChecked():                                                                         # check if the model images should be kept
            shutil.rmtree(base_dir_images, ignore_errors=True)                                                              # otherwise just delete them
        self.LogQueue.put('{0} - {1} Model run finished. Number of modeled points: {2:3d}\n\n'
                          .format(time.strftime("%H:%M:%S", time.localtime()), modeltype, self.numCheckPoints))             # GUI output
        self.modelrun = False
        return self.results                                                                                                 # return results for analysing
