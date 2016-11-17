############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016
#
# Licence APL2.0
#
############################################################

import logging
import math
import time
import datetime
import os
from shutil import copyfile
# threading
from PyQt5 import QtCore
# library for fits file handling
import pyfits
# for the sorting
from operator import itemgetter
# for handling SGPro interface
from support.sgpro import SGPro
from support.analyse import Analyse


def waitSettlingTime(timeDelay):                                                                                            # wait settling time
    time.sleep(timeDelay)                                                                                                   # just waiting


class Model(QtCore.QThread):
    logger = logging.getLogger('Model')                                                                                     # logging enabling
    signalModelConnected = QtCore.pyqtSignal(bool, name='ModelConnected')                                                   # message for errors
    signalModelCommand = QtCore.pyqtSignal([str], name='ModelCommand')                                                      # commands to sgpro thread
    signalModelAzAltPointer = QtCore.pyqtSignal([float, float], name='ModelAzAltPointer')                                   # setting az/alt pointer in charts
    signalModelRedrawRefinement = QtCore.pyqtSignal(bool, name='ModelRedrawRefinementPoints')                               # redraw refinement chart
    signalModelRedrawBase = QtCore.pyqtSignal(bool, name='ModelRedrawBasePoints')                                           # redraw base charts

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
        self.modelAnalyseData = []                                                                                          # analyse data for model
        self.captureFile = 'model_cap.fit'                                                                                  # filename for capturing file
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
            if self.command == 'RunBaseModel':                                                                              # actually doing by receiving signals which enables
                self.command = ''                                                                                           # only one command at a time, last wins
                self.runBaseModel()                                                                                         # should be refactored to queue only without signal
            elif self.command == 'RunRefinementModel':                                                                      #
                self.command = ''                                                                                           #
                self.runRefinementModel()                                                                                   #
            elif self.command == 'RunAnalyseModel':                                                                         #
                self.command = ''                                                                                           #
                self.runAnalyseModel()                                                                                      #
            elif self.command == 'ClearAlignmentModel':                                                                     #
                self.command = ''                                                                                           #
                self.clearAlignmentModel()                                                                                  #
            elif self.command == 'SortBasePoints':                                                                          #
                self.command = ''                                                                                           #
                self.sortPoints('base')                                                                                     #
            elif self.command == 'SortRefinementPoints':                                                                    #
                self.command = ''                                                                                           #
                self.sortPoints('refinement')                                                                               #
            elif self.command == 'GenerateDSOPoints':                                                                       #
                self.command = ''                                                                                           #
                self.generateDSOPoints()                                                                                    #
            elif self.command == 'GenerateDensePoints':                                                                     #
                self.command = ''                                                                                           #
                self.generateDensePoints()                                                                                  #
            elif self.command == 'GenerateNormalPoints':                                                                    #
                self.command = ''                                                                                           #
                self.generateNormalPoints()                                                                                 #
            elif self.command == 'GenerateGridPoints':                                                                      #
                self.command = ''                                                                                           #
                self.generateGridPoints()                                                                                   #
            elif self.command == 'GenerateBasePoints':                                                                      #
                self.command = ''                                                                                           #
                self.generateBasePoints()                                                                                   #
            elif self.command == 'DeleteBelowHorizonLine':                                                                  #
                self.command = ''                                                                                           #
                self.deleteBelowHorizonLine()                                                                               #
            if self.counter % 10 == 0:                                                                                      # standard cycles in model thread fast
                self.getStatusFast()                                                                                        # calling fast part of status
            if self.counter % 20 == 0:                                                                                      # standard cycles in model thread slow
                self.getStatusSlow()                                                                                        # calling slow part of status
            self.counter += 1                                                                                               # loop +1
            time.sleep(.1)                                                                                                  # wait for the next cycle
        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()

    def command(self, command):                                                                                             # dispatcher of commands inside thread
        if command == 'CancelBaseModel':                                                                                    # check the command
            self.command = ''                                                                                               # reset the command
            self.cancel = True                                                                                              # set cancel flag
            self.ui.btn_cancelBaseModel.setStyleSheet('background-color: red')                                              # reset color of button
        elif command == 'CancelRefinementModel':                                                                            # check the command
            self.command = ''                                                                                               # reset the command buffer
            self.cancel = True                                                                                              # set cancel flag
            self.ui.btn_cancelRefinementModel.setStyleSheet('background-color: red')                                        # reset color of button
        elif command == 'CancelAnalyseModel':                                                                               #
            self.command = ''                                                                                               #
            self.cancel = True                                                                                              #
            self.ui.btn_cancelAnalyseModel.setStyleSheet('background-color: red')                                           # reset color of button
        else:
            self.command = command                                                                                          # passing the command to main loop of thread

    def getStatusSlow(self):                                                                                                # check SGPro running
        suc, mes = self.SGPro.checkConnection()                                                                             # check status of SGPro
        self.connected = suc                                                                                                # set status for internal use
        self.signalModelConnected.emit(suc)                                                                                 # send status to GUI
        if not suc:                                                                                                         # otherwise
            self.logger.debug('getStatusSlow -> No SGPro connection: {0}'.format(mes))                                      # debug message

    def getStatusFast(self):                                                                                                # fast status
        pass                                                                                                                # actually no fast status

    def loadModelPoints(self, modelPointsFileName, modeltype):                                                              # load model point file from MM als list from tuples
        if modeltype == 'base':                                                                                             # check type of model file
            self.BasePoints = []                                                                                            # reset BasePoints
        else:                                                                                                               #
            self.RefinementPoints = []                                                                                      # reset  points
        try:                                                                                                                # fault tolerance, if file io fails
            with open('config\\' + modelPointsFileName) as fileHandle:                                                      # run over complete file
                for line in fileHandle:                                                                                     # run over lines
                    convertedLine = line.rstrip('\n').split(':')                                                            # format is same as Per's MM
                    Point = (int(convertedLine[0]), int(convertedLine[1]))                                                  # take data from line
                    if len(convertedLine) == 2:                                                                             # in MM format base and refinement are included
                        if modeltype == 'refinement':                                                                       # Switch for type
                            self.RefinementPoints.append(Point)                                                             # add data to the adequate list
                    else:
                        if modeltype == 'base':
                            self.BasePoints.append(Point)
            fileHandle.close()                                                                                              # close file
        except Exception as e:                                                                                              # handle exception
            self.messageQueue.put('Error loading model points from {0} error:{1}!'.format(modelPointsFileName, e))          # Gui message
            self.logger.error('loadModelPoints -> {0} could not be loaded error{1}'.format(modelPointsFileName, e))         # log output

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
        else:
            self.RefinementPoints = eastSide + westSide                                                                     # put them together
            self.signalModelRedrawRefinement.emit(True)                                                                     # update graphics

    def loadHorizonPoints(self, horizonPointsFileName):                                                                     # load a ModelMaker model file, return base & refine points as lists of (az,alt) tuples
        hp = []                                                                                                             # clear cache
        try:                                                                                                                # try opening the file
            with open('config\\' + horizonPointsFileName) as f:                                                             # run through file
                for line in f:                                                                                              # run through lines
                    m = line.rstrip('\n').split(':')                                                                        # split the values
                    point = (int(m[0]), int(m[1]))                                                                          # get point data
                    hp.append(point)                                                                                        # add the point
            f.close()                                                                                                       # close file again
        except Exception as e:                                                                                              # handle exception
            self.messageQueue.put('Error loading horizon points: {0}'.format(e))                                            # show on GUI
            self.logger.error('loadHorizonPoints -> Error loading horizon points: {0}'.format(e))                           # write to logger
            return                                                                                                          # stop routine
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
        self.signalModelRedrawRefinement.emit(True)                                                                         # update graphics

    def transformCelestialHorizontal(self, ha, dec):
        self.mount.transform.SetJ2000(ha, dec)                                                                              # set J2000 ra, dec
        alt = self.mount.transform.ElevationTopocentric                                                                     # convert alt
        az = self.mount.transform.AzimuthTopocentric                                                                        # convert az
        return az, alt

    def generateDSOPoints(self):                                                                                            # model points along dso path
        if self.mount.connected:
            self.ui.btn_generateDSOPoints.setStyleSheet('background-color: rgb(42, 130, 218)')                              # take some time, therefore coloring button during execution
            self.RefinementPoints = []                                                                                      # clear point list
            for i in range(0, 25):                                                                                          # round model point from actual az alt position 24 hours
                ra = self.mount.degStringToDecimal(self.ui.le_trackRA.text()) + i / 12.0                                    # Transform text to hours format
                if ra >= 24:
                    ra -= 24
                dec = self.mount.degStringToDecimal(self.ui.le_trackDEC.text())                                             # Transform text to degree format
                self.mount.transform.SetJ2000(ra, dec)                                                                      # set data in J2000
                alt = int(self.mount.transform.ElevationTopocentric)                                                        # take az data
                az = int(self.mount.transform.AzimuthTopocentric)                                                           # take alt data
                print(ra, dec, az, alt)
                if alt > 0:                                                                                                 # we only take point alt > 0
                    self.RefinementPoints.append((az, alt))                                                                 # add point to list
                self.signalModelRedrawRefinement.emit(True)                                                                 # update graphics
            self.ui.btn_generateDSOPoints.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')         # color button back, routine finished

    def generateDensePoints(self):                                                                                          # generate pointcloud in greater circles of sky
        if self.mount.connected:
            self.ui.btn_generateDensePoints.setStyleSheet('background-color: rgb(42, 130, 218)')                            # tale some time, color button fro showing running
            self.RefinementPoints = []                                                                                      # clear pointlist
            west = []                                                                                                       # no sorting, point will be for west and east prepared
            east = []                                                                                                       #
            for dec in range(-10, 90, 10):                                                                                  # range, actually referenced from european situation
                if dec < 30:                                                                                                # has to be generalized
                    step = -15                                                                                              # lower dec, more point
                elif dec < 70:
                    step = -10
                else:
                    step = -30                                                                                              # higher dec. less point (anyway denser)
                for ha in range(239, 0, step):                                                                              # for complete 24 hourangle
                    az, alt = self.transformCelestialHorizontal(ha/10, dec)                                                 # do the transformation to alt az
                    if alt > 0:                                                                                             # only point with alt > 0 are taken
                        if az > 180:                                                                                        # put to the right list
                            east.append((int(az), int(alt)))                                                                # add to east
                        else:
                            west.append((int(az), int(alt)))                                                                # add to west
                self.RefinementPoints = west + east                                                                         # combine pointlist
                self.signalModelRedrawRefinement.emit(True)                                                                 # update graphics
            self.ui.btn_generateDensePoints.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')       # routing finished, coloring default

    def generateNormalPoints(self):
        if self.mount.connected:
            self.ui.btn_generateNormalPoints.setStyleSheet('background-color: rgb(42, 130, 218)')                           # tale some time, color button fro showing running
            self.RefinementPoints = []                                                                                      # clear pointlist
            west = []                                                                                                       # no sorting, point will be for west and east prepared
            east = []                                                                                                       #
            for dec in range(-15, 90, 15):                                                                                  # range, actually referenced from european situation
                if dec < 60:                                                                                                # has to be generalized
                    step = -1                                                                                               # lower dec, more point
                else:
                    step = -2                                                                                               # higher dec. less point (anyway denser)
                for ha in range(23, -1, step):                                                                              # for complete 24 hourangle
                    az, alt = self.transformCelestialHorizontal(ha, dec)                                                    # do the transformation to alt az
                    if alt > 0:                                                                                             # only point with alt > 0 are taken
                        if az > 180:                                                                                        # put to the right list
                            east.append((int(az), int(alt)))                                                                # add to east
                        else:
                            west.append((int(az), int(alt)))                                                                # add to west
                self.RefinementPoints = west + east                                                                         # combine pointlist
                self.signalModelRedrawRefinement.emit(True)                                                                 # update graphics
            self.ui.btn_generateNormalPoints.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')      # routing finished, coloring default

    def generateGridPoints(self):                                                                                           # model points along dso path
        self.ui.btn_generateGridPoints.setStyleSheet('background-color: rgb(42, 130, 218)')                                 # take some time, therefore coloring button during execution
        self.RefinementPoints = []                                                                                          # clear point list
        for az in range(0, 360, 30):                                                                                        # make point for all azimuth
            for alt in range(20, 90, 10):                                                                                   # make point for all altitudes
                self.RefinementPoints.append((az, alt))                                                                     # add point to list
            self.signalModelRedrawRefinement.emit(True)                                                                     # update graphics
        self.ui.btn_generateGridPoints.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')            # color button back, routine finished

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
        self.signalModelRedrawBase.emit(True)                                                                               # redraw the chart

    def clearAlignmentModel(self):
        self.ui.btn_clearAlignmentModel.setStyleSheet('background-color: rgb(42, 130, 218)')
        self.modelAnalyseData = []
        self.LogQueue.put('Clearing alignment model - taking 4 seconds. \n\n')
        self.commandQueue.put('ClearAlign')
        time.sleep(4)                                                                                                       # we are waiting 4 seconds like Per did (don't know if necessary)
        self.ui.btn_clearAlignmentModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')

    def runBaseModel(self):
        if self.connected:
            self.ui.btn_runBaseModel.setStyleSheet('background-color: rgb(42, 130, 218)')
            if len(self.BasePoints) > 0:
                self.modelAnalyseData = self.runModel('Base', self.BasePoints)
            else:
                self.logger.warning('runBaseModel -> There are no Basepoints to model')
            name = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + '_base_run.txt'                                      # generate name of analyse file
            self.Analyse.saveData(self.modelAnalyseData, name)                                                              # save the data
            self.ui.le_analyseFileName.setText(name)                                                                        # set data name in GUI to start over quickly
            self.ui.btn_runBaseModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')

    def runRefinementModel(self):
        if self.connected:
            self.ui.btn_runRefinementModel.setStyleSheet('background-color: rgb(42, 130, 218)')
            if len(self.RefinementPoints) > 0:
                self.modelAnalyseData = self.runModel('Refinement', self.RefinementPoints)
            else:
                self.logger.warning('runRefinementModel -> There are no Refinement Points to model')
            name = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + '_refinement_run.txt'                                # generate name of analyse file
            self.ui.le_analyseFileName.setText(name)                                                                        # set data name in GUI to start over quickly
            self.Analyse.saveData(self.modelAnalyseData, name)                                                              # save the data
            self.ui.btn_runRefinementModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')

    def runAnalyseModel(self):
        if self.connected:
            self.ui.btn_runAnalyseModel.setStyleSheet('background-color: rgb(42, 130, 218)')
            if len(self.RefinementPoints + self.BasePoints) > 0:
                self.modelAnalyseData = self.runModel('Analyse', self.BasePoints + self.RefinementPoints)
            else:
                self.logger.warning('runAnalyseModel -> There are no Refinement or Base Points to model')
            name = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) + '_analyse_run.txt'                                   # generate name of analyse file
            self.ui.le_analyseFileName.setText(name)                                                                        # set data name in GUI to start over quickly
            self.Analyse.saveData(self.modelAnalyseData, name)                                                              # save the data
            self.ui.btn_runAnalyseModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')

    def slewMountDome(self, az, alt):                                                                                       # slewing mount and dome to alt az point
        self.commandQueue.put('Sz{0:03d}*00'.format(az))                                                                    # Azimuth setting
        self.commandQueue.put('Sa+{0:02d}*00'.format(alt))                                                                  # Altitude Setting
        if self.ui.checkTestWithoutMount.isChecked():                                                                       # if simulation
            self.mount.signalMountAzAltPointer.emit(az, alt)                                                                # just set the pointer, normally done from mount thread
            time.sleep(0.5)                                                                                                 # wait 0.5 s the you can watch
        else:                                                                                                               # otherwise
            self.commandQueue.put('MS')                                                                                     # initiate slewing
            if self.ui.checkSlewDome.isChecked() and self.dome.connected:                                                   # if there is a dome, should be slewed as well
                self.dome.ascom.SlewToAzimuth = az                                                                          # set azimuth coordinate
                if self.dome.ascom.CanSetAltitude:                                                                          # if dome can set Altitude as well
                    self.dome.ascom.SlewToAltitude = alt                                                                    # set altitude for dome
            time.sleep(2.5)                                                                                                 # wait for mount to start
            while self.mount.slewing or (self.dome.ascom.Slewing and self.ui.checkSlewDome.isChecked()):                    # wait for tracking = 7 or dome not slewing
                time.sleep(.1)                                                                                              # loop time

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

    def capturingImage(self, index, ra, dec, jd, az, alt, sub, sX, sY, oX, oY):                                             # capturing image
        self.LogQueue.put('Capturing image for model point {0:2d}...'.format(index + 1))                                    # gui output
        guid = ''                                                                                                           # define guid
        imagepath = ''                                                                                                      # define imagepath
        mes = ''                                                                                                            # define message
        if not self.ui.checkTestWithoutCamera.isChecked():                                                                  # if it's not simulation, we start imaging
            self.logger.debug('capturingImage-> params: BIN: {0} ISO:{1} EXP:{2} Path: {3}'
                              .format(self.ui.cameraBin.value(), int(float(self.ui.isoSetting.value())),
                                      self.ui.cameraExposure.value(),
                                      self.ui.le_imageDirectoryName.text() + '\\' + self.captureFile))                      # write logfile
            if self.ui.checkFastDownload.isChecked():                                                                       # if camera is supporting high speed download
                speed = 'HiSpeed'                                                                                           # we can use it for improved modeling speed
            else:                                                                                                           # otherwise
                speed = 'Normal'                                                                                            # standard speed
            suc, mes, guid = self.SGPro.SgCaptureImage(binningMode=self.ui.cameraBin.value(),
                                                       exposureLength=self.ui.cameraExposure.value(),
                                                       isoMode=int(float(self.ui.isoSetting.value())),
                                                       gain='High', speed=speed, frameType='Light',
                                                       path=self.ui.le_imageDirectoryName.text() + '\\' + self.captureFile,
                                                       useSubframe=sub, posX=oX, posY=oY, width=sX, height=sY)              # start imaging with parameters. HiSpeed and DSLR doesn't work with SGPro
        else:                                                                                                               # otherwise its simulation
            suc = True                                                                                                      # success is always true
        if suc:                                                                                                             # if we successfully starts imaging, we ca move on
            if not self.ui.checkTestWithoutCamera.isChecked():                                                              # if we simulate, we cannot wait for SGPro, there is nothing !
                while True:                                                                                                 # waiting for the image download before proceeding
                    suc, imagepath = self.SGPro.SgGetImagePath(guid)                                                        # there is the image path, once the image is downloaded
                    if suc:                                                                                                 # until then, the link is only the receipt
                        break                                                                                               # stopping the loop
                    else:                                                                                                   # otherwise
                        time.sleep(0.5)                                                                                     # wait for 0.5 seconds
                self.logger.debug('capturingImage-> getImagePath-> suc: {0}, imagepath: {1}'.format(suc, imagepath))        # debug output
                hint = float(self.ui.pixelSize.value()) * 206.6 / float(self.ui.focalLength.value())                        # calculating hint with focal length and pixel size of cam
                fitsFileHandle = pyfits.open(imagepath, mode='update')                                                      # open for adding field info
                fitsHeader = fitsFileHandle[0].header                                                                       # getting the header part
                fitsHeader['DATE-OBS'] = datetime.datetime.utcnow().isoformat()                                             # set time to current time
                h, m, s = self.mount.decimalToDegree(ra)                                                                    # convert
                fitsHeader['OBJCTRA'] = '{0:02} {1:02} {2:02}'.format(h, m, s)                                              # set the point coordinates from mount in J2000 as hi nt precision 2 ???
                h, m, s = self.mount.decimalToDegree(dec)                                                                   # convert
                fitsHeader['OBJCTDEC'] = '{0:+03} {1:02} {2:02}'.format(h, m, s)                                            # set dec as well
                fitsHeader['CDELT1'] = str(hint)                                                                            # x is the same as y
                fitsHeader['CDELT2'] = str(hint)                                                                            # and vice versa
                fitsHeader['MW-AZ'] = str(az)                                                                               # x is the same as y
                fitsHeader['MW_ALT'] = str(alt)                                                                             # and vice versa
                self.logger.debug(
                    'capturingImage-> DATE-OBS: {0}, OBJCTRA: {1} OBJTDEC: {2} CDELT1: {3} CDELT2: {4}'.format(
                        fitsHeader['DATE-OBS'], fitsHeader['OBJCTRA'], fitsHeader['OBJCTDEC'], fitsHeader['CDELT1'],
                        fitsHeader['CDELT2']))                                                                              # write all header data to debug
                fitsFileHandle.flush()                                                                                      # write all to disk
                fitsFileHandle.close()                                                                                      # close FIT file
                self.LogQueue.put('\tImage path: {0}\n'.format(imagepath))                                                  # Gui output
                return True, 'success', imagepath                                                                           # return true message imagepath
            else:                                                                                                           # If we test without camera, we need to take pictures of test
                imagepath = self.ui.le_imageDirectoryName.text() + '\\' + self.captureFile                                  # set imagepath to default
                copyfile(os.getcwd() + '\\testimages\\model_cap-{0}.fit'.format(index), imagepath)                          # copy testfile instead of imaging
                self.LogQueue.put('\tImage path: {0}\n'.format(imagepath))                                                  # Gui output
                return True, 'testsetup', imagepath                                                                         # return true test message imagepath
        else:                                                                                                               # otherwise
            return False, mes, ''                                                                                           # image capturing was failing, writing message from SGPro back

    def solveImage(self, modeltype, imagepath):                                                                             # solving image based on information inside the FITS files, no additional info
        hint = float(self.ui.pixelSize.value()) * 206.6 * float(self.ui.cameraBin.value()) / float(self.ui.focalLength.value())    # calculating hint for solve
        if modeltype == 'Base':                                                                                             # base type could be done with blind solve
            suc, mes, guid = self.SGPro.SgSolveImage(imagepath, scaleHint=hint, blindSolve=self.ui.checkUseBlindSolve.isChecked(), useFitsHeaders=True)
        else:
            suc, mes, guid = self.SGPro.SgSolveImage(imagepath, scaleHint=hint, blindSolve=False, useFitsHeaders=True)
        self.logger.debug('solveImage (start)-> suc:{0} mes:{1} guid:{2} scalehint:{3}'.format(suc, mes, guid, hint))
        if not suc:                                                                                                         # if we failed to start solving
            self.LogQueue.put('\t\tSolving could not be started: ' + mes)                                                   # Gui output
            self.logger.warning('solveImage -> no start {0}'. format(mes))                                                  # debug output
            return False, 0, 0, 0, 0, 0, 0, 0                                                                               # default parameters without success
        while True:                                                                                                         # retrieving solving data in loop
            suc, mes, ra_sol, dec_sol, scale, angle, timeTS = self.SGPro.SgGetSolvedImageData(guid)                         # retrieving the data from solver
            dec_sol = float(dec_sol)                                                                                        # convert to float
            ra_sol = float(ra_sol)                                                                                          #
            scale = float(scale)                                                                                            #
            angle = float(angle)                                                                                            #
            timeTS = float(timeTS)                                                                                          #
            mes = mes.strip('\n')                                                                                           # sometimes there are heading \n in message
            if mes[:7] in ['Matched', 'Solve t']:                                                                           # if there is success, we can move on
                self.logger.debug('solveImage (solved)-> suc:{0} mes:{1} guid:{2} ra:{3} dec:{4}'.format(suc, mes, guid, ra_sol, dec_sol))
                fitsFileHandle = pyfits.open(imagepath, mode='readonly')                                                    # open for getting telescope coordinates
                fitsHeader = fitsFileHandle[0].header                                                                       # getting the header part
                ra_fits = self.mount.degStringToDecimal(fitsHeader['OBJCTRA'], ' ')                                         # convert to decimals the ra of original pointing of mount
                dec_fits = self.mount.degStringToDecimal(fitsHeader['OBJCTDEC'], ' ')                                       # convert to decimals the dec of original pointing of mount
                fitsFileHandle.close()                                                                                      # close FIT file. All the data was store in FITS so batch could be made
                return True, ra_fits, ra_sol, dec_fits, dec_sol, scale, angle, timeTS                                       # return values after successful solving
            elif mes != 'Solving':                                                                                          # general error
                self.LogQueue.put('\t\t\tError:  ' + mes)                                                                   # Gui output
                self.logger.debug('solveImage (solved)-> suc:{0} mes:{1} guid:{2}'.format(suc, mes, guid))                  # debug output
                return False, 0, 0, 0, 0, 0, 0, 0                                                                           # default parameters without success
            else:                                                                                                           # otherwise
                if self.ui.checkUseBlindSolve.isChecked():                                                                  # when using blind solve, it takes 30-60 s
                    time.sleep(5)                                                                                           # therefore slow cycle
                else:                                                                                                       # local solver takes 1-2 s
                    time.sleep(.25)                                                                                         # therefore quicker cycle

    def addRefinementStar(self, ra, dec):                                                                                   # add refinement star during model run
        if len(self.ui.le_refractionTemperature.text()) > 0:                                                                # set refraction temp
            self.mount.transform.SiteTemperature = float(self.ui.le_refractionTemperature.text())                           # set it if string available
        else:                                                                                                               # otherwise
            self.mount.transform.SiteTemperature = 20.0                                                                     # set it to 20.0 degree c
        self.mount.transform.SetJ2000(float(ra), float(dec))                                                                # set coordinates in J2000 (solver)
        if not self.ui.checkTestWithoutMount.isChecked():                                                                   # test setup without mount. can't refine with simulation
            h, m, s = self.mount.decimalToDegree(self.mount.transform.RATopocentric)                                        # convert to Jnow
            self.mount.sendCommand('Sr{0:02d}:{1:02d}:{2:04.2f}'.format(h, m, s))                                           # Write jnow ra to mount
            h, m, s = self.mount.decimalToDegree(self.mount.transform.DecTopocentric)                                       # convert to Jnow
            self.mount.sendCommand('Sd{0:+02d}*{1:02d}:{2:04.2f}'.format(h, m, s))
            self.logger.debug('addRefinementStar -> ra:{0} dec:{1}'.format(self.mount.transform.RATopocentric,
                                                                           self.mount.transform.DecTopocentric))            # debug output
            sync_result = self.mount.sendCommand('CMS')                                                                     # send sync command (regardless what driver tells)
            if sync_result.strip() == 'E':                                                                                  # if sync result is E, than fault happen
                self.logger.warning('addRefinementStar -> Star could not be added. ra:{0} dec:{1}'.format(ra, dec))         # write debug output
                return False                                                                                                # no refinement feedback
            else:                                                                                                           # otherwise
                return True                                                                                                 # result OK, synced
        else:                                                                                                               # if simulation, than always OK
            return True                                                                                                     # simulation OK

    def runModel(self, modeltype, runPoints):                                                                               # model run routing
        self.LogQueue.put('delete')                                                                                         # deleting the logfile view
        self.LogQueue.put('Start {0} Model. {1}'.format(modeltype, time.ctime()))                                           # Start informing user
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
        self.logger.debug('runModel-> subframe: {0}, {1}, {2}, {3}, {4}'.format(self.sub, self.sizeX, self.sizeY, self.offX, self.offY))    # log data
        if not self.ui.checkTestWithoutMount.isChecked():                                                                   # if mount simulated, no real commands to mount
            self.commandQueue.put('PO')                                                                                     # unpark to start slewing
            self.commandQueue.put('AP')   #######                                                                                  # tracking should be on as well
        for i, p in enumerate(runPoints):                                                                                   # run through all model points
            if self.cancel:                                                                                                 # here is the entry point for canceling the model run
                self.LogQueue.put('\n\n{0} Model canceled !\n'.format(modeltype))                                           # we keep all the stars before
                self.cancel = False                                                                                         # and make it back to default
                self.ui.btn_cancelBaseModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')       # button back to default color
                self.ui.btn_cancelRefinementModel.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')     # button back to default color
                break                                                                                                       # finally stopping model run
            self.LogQueue.put('\n\nSlewing to point {0:2d}  @ Az: {1:3d}\xb0 Alt: {2:2d}\xb0...'.format(i+1, p[0], p[1]))   # Gui Output
            self.logger.debug('runModel-> point {0:2d}  Az: {1:3d} Alt: {2:2d}'.format(i+1, p[0], p[1]))                    # Debug output
            self.slewMountDome(p[0], p[1])                                                                                  # slewing mount and dome to az/alt for model point
            self.LogQueue.put('\tWait mount settling time {0} second(s) \n'.format(int(self.ui.settlingTime.value())))      # Gui Output
            waitSettlingTime(float(self.ui.settlingTime.value()))                                                           # wait for settling mount
            suc, mes, imagepath = self.capturingImage(i, self.mount.ra, self.mount.dec, self.mount.jd, p[0], p[1],
                                                      self.sub, self.sizeX, self.sizeY, self.offX, self.offY)               # capturing image and store position (ra,dec), time, (az,alt)
            self.logger.debug('runModel-> capturingImage-> suc:{0} mes:{1}'.format(suc, mes))                               # Debug
            if suc:                                                                                                         # if a picture could be taken
                self.LogQueue.put('Solving Image...')                                                                       # output for user GUI
                suc, ra_m, ra_sol, dec_m, dec_sol, scale, angle, timeTS = self.solveImage(modeltype, imagepath)             # solve the position and returning the values
                self.logger.debug('runModel-> solveImage-> suc:{0} ra:{1} dec:{2} scale:{3} angle:{4}'.format(suc, ra_sol, dec_sol, scale, angle))  # debug output
                if not self.ui.checkKeepImages.isChecked():                                                                 # check if the model images should be kept
                    os.remove(imagepath)                                                                                    # otherwise just delete them
                if suc:                                                                                                     # solved data is there, we can sync
                    if not modeltype == 'Analyse':                                                                          # if we run analyse, we don't change the model
                        self.addRefinementStar(ra_sol, dec_sol)                                                             # sync the actual star to resolved coordinates in J2000
                    self.numCheckPoints += 1                                                                                # increase index for synced stars
                    raE = (ra_sol - ra_m) * 3600                                                                            # calculate the alignment error ra
                    decE = (dec_sol - dec_m) * 3600                                                                         # calculate the alignment error dec
                    err = math.sqrt(raE * raE + decE * decE)                                                                # accumulate sum of error vectors squared
                    self.logger.debug('runModel-> raE:{0} decE:{1} ind:{2}'.format(raE, decE, self.numCheckPoints))         # generating debug output
                    self.results.append((i, p[0], p[1], ra_m, dec_m, ra_sol, dec_sol, raE, decE, err))                      # adding point for matrix
                    if modeltype == 'Base':                                                                                 # depending on modeltype set the relating modeled point invisible
                        self.BasePoints[i][2].setVisible(False)                                                             # visibility = False
                    if modeltype == 'Refinement':                                                                           # depending on modeltype set the relating modeled point invisible
                        self.RefinementPoints[i][2].setVisible(False)                                                       # visibility = False
                    self.LogQueue.put(
                        '\t\t\tRA: {0:3.1f}  DEC: {1:3.1f}  Scale: {2:2.2f}  Angle: {3:3.1f}  RAdiff: {4:2.1f}  DECdiff: {5:2.1f}  Took: {6:3.1f}s'.format(
                            ra_sol, dec_sol, scale, angle, raE, decE, timeTS))                                              # data for User
                    self.logger.debug(
                        'runModel-> RA: {0:3.1f}  DEC: {1:3.1f}  Scale: {2:2.2f}  Angle: {3:3.1f}  Error: {4:2.1f}  Took: {5:3.1f}s'.format(
                            ra_sol, dec_sol, scale, angle, err, timeTS))                                                    # log output
        self.LogQueue.put('\n\n{0} Model finished. Number of points: {1:3d}   {2}.\n\n'.format(modeltype, self.numCheckPoints, time.ctime()))    # GUI output
        return self.results                                                                                                 # return results for analysing
