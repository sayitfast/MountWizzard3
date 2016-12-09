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

# import basic stuff
import logging
import sys
import json
import time
import os
# import for the PyQt5 Framework
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
# commands to threads
from queue import Queue
# import the UI part, which is done via QT Designer and exported
from support.mount_ui import Ui_MountDialog
# import mount functions of other classes
from support.weather_thread import Weather
from support.stick_thread import Stick
from support.mount_thread import Mount
from support.model_thread import Model
from support.analyse import Analyse
from support.relays import Relays
from support.dome_thread import Dome


def getXYEllipse(az, alt, height, width, border, esize):                                                                    # calculation of the ellipse
    x = border - esize / 2 + int(az / 360 * (width - 2 * border))
    y = height - border - esize / 2 - int(alt / 90 * (height - 2 * border))
    return int(x), int(y)


def getXYRectangle(az, width, border):
    x = (az - 15) * (width - 2 * border) / 360 + border
    y = border
    return int(x), int(y)


def constructHorizon(scene, horizon, height, width, border):                                                                # calculate horizon
    for i, p in enumerate(horizon):                                                                                         # over all point in the horizon file
        if (i != len(horizon)) and (i != 0):                                                                                # horizon in between
            pen = QPen(QColor(0, 96, 0), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                        # define the pen style thickness 3
            scene.addLine(border + int(p[0] / 360 * (width - 2 * border)),
                          height - border - int(p[1] * (height - 2 * border) / 90),
                          border + int(horizon[i - 1][0] / 360 * (width - 2 * border)),
                          height - border - int(horizon[i - 1][1] * (height - 2 * border) / 90),
                          pen)                                                                                              # and add it to the scene
    return scene


class MountWizzardApp(QDialog, QObject):
    logger = logging.getLogger('MountWizzardApp:')                                                                          # logging enabling

    def __init__(self):
        super(MountWizzardApp, self).__init__()                                                                             # Initialize Class for UI
        self.modifiers = None                                                                                               # for the mouse handling
        self.sceneRefinementPoints = None                                                                                   # graphics refinement
        self.config = {}                                                                                                    # configuration data, which is stored
        self.borderModelPointsView = 20                                                                                     # border from rectangle to plot
        self.textheightModelPointsView = 10                                                                                 # size of text for positioning
        self.ellipseSizeModelPointsView = 12                                                                                # diameter of ellipse / circle for points
        self.blueColor = QColor(32, 144, 192)                                                                               # blue astro color
        self.yellowColor = QColor(192, 192, 0)
        self.greenColor = QColor(0, 255, 0)
        self.whiteColor = QColor(192, 192, 192)
        self.pointerColor = QColor(255, 0, 255)
        self.moving = False                                                                                                 # check if window moves with mouse pointer
        self.offset = None                                                                                                  # check offset from mouse pick point to window 0,0 reference point
        self.ui = Ui_MountDialog()                                                                                          # load the dialog from "DESIGNER"
        self.ui.setupUi(self)                                                                                               # initialising the GUI
        self.initUI()                                                                                                       # adapt the window to our purpose
        self.pointerBaseTrackingWidget = QGraphicsEllipseItem(0, 0, 0, 0)                                                   # Reference Widget for Pointing
        self.pointerRefinementTrackingWidget = QGraphicsEllipseItem(0, 0, 0, 0)                                             # Reference Widget for Pointing
        self.pointerBaseDomeWidget = QGraphicsRectItem(0, 0, 0, 0)
        self.pointerRefinementDomeWidget = QGraphicsRectItem(0, 0, 0, 0)
        self.commandQueue = Queue()                                                                                         # queue for sending command to mount
        self.mountDataQueue = Queue()                                                                                       # queue for sending data back to gui
        self.modelLogQueue = Queue()                                                                                        # queue for showing the modeling progress
        self.messageQueue = Queue()                                                                                         # queue for showing messages in Gui from threads
        self.analyse = Analyse()                                                                                            # plotting and visualizing model measurements
        self.relays = Relays(self.ui)                                                                                       # Web base relays box for Booting and CCD / Heater On / OFF
        self.dome = Dome(self.messageQueue)                                                                                 # dome control
        self.dome.signalDomPointer.connect(self.setDomePointer)
        self.mount = Mount(self.ui, self.messageQueue, self.commandQueue, self.mountDataQueue)                              # Mount -> everything with mount and alignment
        self.weather = Weather(self.messageQueue)                                                                           # Stickstation Thread
        self.stick = Stick(self.messageQueue)                                                                               # Stickstation Thread
        self.model = Model(self.ui, self.mount, self.dome, self.messageQueue, self.commandQueue, self.mountDataQueue, self.modelLogQueue)  # transferring ui and mount object as well
        self.mappingFunctions()                                                                                             # mapping the functions to ui
        self.loadConfig()                                                                                                   # loading configuration
        self.showBasePoints()                                                                                               # populate gui with data for base model
        self.showRefinementPoints()                                                                                         # same for refinement
        self.mainLoop()                                                                                                     # starting loop for cyclic data to gui from threads
        self.mount.signalMountConnected.connect(self.setMountStatus)                                                        # status from thread
        self.mount.signalMountAzAltPointer.connect(self.setAzAltPointer)                                                    # set AzAltPointer in Gui
        self.mount.start()                                                                                                  # starting polling thread
        self.weather.signalWeatherData.connect(self.fillWeatherData)                                                        # connecting the signal
        self.weather.signalWeatherConnected.connect(self.setWeatherStatus)                                                  # status from thread
        self.weather.start()                                                                                                # starting polling thread
        self.stick.signalStickData.connect(self.fillStickData)                                                              # connecting the signal for data
        self.stick.signalStickConnected.connect(self.setStickStatus)                                                        # status from thread
        self.stick.start()                                                                                                  # starting polling thread
        self.dome.signalDomeConnected.connect(self.setDomeStatus)                                                           # status from thread
        self.dome.start()                                                                                                   # starting polling thread
        self.model.signalModelConnected.connect(self.setSGProStatus)                                                        # status from thread
        self.model.signalModelAzAltPointer.connect(self.setAzAltPointer)                                                    # set AzAltPointer in Gui
        self.model.signalModelRedrawRefinement. connect(self.showRefinementPoints)                                          # trigger redraw refinement chart
        self.model.signalModelRedrawBase.connect(self.showBasePoints)                                                       # trigger base chart
        self.model.start()                                                                                                  # starting polling thread
        if not os.path.isfile(os.getcwd() + '/mw.txt'):                                                                     # check existing file for enable the features
            self.ui.tabWidget.setTabEnabled(8, False)                                                                       # disable the tab for internal features

    def mappingFunctions(self):
        #
        # defining all the function against Dialog
        # here are the wrapper for commands
        #
        self.ui.btn_mountQuit.clicked.connect(self.saveConfigQuit)
        self.ui.btn_shutdownQuit.clicked.connect(self.shutdownQuit)
        self.ui.btn_mountPark.clicked.connect(self.mountPark)
        self.ui.btn_mountUnpark.clicked.connect(self.mountUnpark)
        self.ui.btn_startTracking.clicked.connect(self.startTracking)
        self.ui.btn_stopTracking.clicked.connect(self.stopTracking)
        self.ui.btn_setTrackingLunar.clicked.connect(self.setTrackingLunar)
        self.ui.btn_setTrackingSolar.clicked.connect(self.setTrackingSolar)
        self.ui.btn_setTrackingSideral.clicked.connect(self.setTrackingSideral)
        self.ui.btn_stop.clicked.connect(self.stop)
        self.ui.btn_mountPos1.clicked.connect(self.mountPosition1)
        self.ui.btn_mountPos2.clicked.connect(self.mountPosition2)
        self.ui.btn_mountPos3.clicked.connect(self.mountPosition3)
        self.ui.btn_mountPos4.clicked.connect(self.mountPosition4)
        self.ui.le_parkPos1Text.textChanged.connect(self.setParkPos1Text)
        self.ui.le_parkPos2Text.textChanged.connect(self.setParkPos2Text)
        self.ui.le_parkPos3Text.textChanged.connect(self.setParkPos3Text)
        self.ui.le_parkPos4Text.textChanged.connect(self.setParkPos4Text)
        self.ui.btn_setHorizonLimitHigh.clicked.connect(self.setHorizonLimitHigh)
        self.ui.btn_setHorizonLimitLow.clicked.connect(self.setHorizonLimitLow)
        self.ui.btn_setDualTracking.clicked.connect(self.setDualTracking)
        self.ui.btn_setUnattendedFlip.clicked.connect(self.setUnattendedFlip)
        self.ui.btn_setupMountDriver.clicked.connect(self.setupMountDriver)
        self.ui.btn_setupDomeDriver.clicked.connect(self.setupDomeDriver)
        self.ui.btn_setupStickDriver.clicked.connect(self.setupStickDriver)
        self.ui.btn_setupWeatherDriver.clicked.connect(self.setupWeatherDriver)
        self.ui.btn_setRefractionParameters.clicked.connect(self.setRefractionParameters)
        self.ui.btn_runBaseModel.clicked.connect(self.runBaseModel)
        self.ui.btn_cancelBaseModel.clicked.connect(self.cancelBaseModel)
        self.ui.btn_runRefinementModel.clicked.connect(self.runRefinementModel)
        self.ui.btn_cancelRefinementModel.clicked.connect(self.cancelRefinementModel)
        self.ui.btn_clearAlignmentModel.clicked.connect(self.clearAlignmentModel)
        self.ui.btn_selectImageDirectoryName.clicked.connect(self.selectImageDirectoryName)
        self.ui.btn_selectHorizonPointsFileName.clicked.connect(self.selectHorizonPointsFileName)
        self.ui.btn_selectModelPointsFileName.clicked.connect(self.selectModelPointsFileName)
        self.ui.btn_selectAnalyseFileName.clicked.connect(self.selectAnalyseFileName)
        self.ui.btn_getActualModel.clicked.connect(self.getAlignmentModel)
        self.ui.btn_setRefractionCorrection.clicked.connect(self.setRefractionCorrection)
        self.ui.btn_runTargetRMSAlignment.clicked.connect(self.runTargetRMSAlignment)
        self.ui.btn_sortRefinementPoints.clicked.connect(self.sortRefinementPoints)
        self.ui.btn_deleteBelowHorizonLine.clicked.connect(self.deleteBelowHorizonLine)
        self.ui.btn_backupModel.clicked.connect(self.backupModel)
        self.ui.btn_restoreModel.clicked.connect(self.restoreModel)
        self.ui.btn_flipMount.clicked.connect(self.flipMount)
        self.ui.btn_loadRefinementPoints.clicked.connect(self.loadModelRefinementPoints)
        self.ui.btn_loadBasePoints.clicked.connect(self.loadModelBasePoints)
        self.ui.btn_saveSimpleModel.clicked.connect(self.saveSimpleModel)
        self.ui.btn_loadSimpleModel.clicked.connect(self.loadSimpleModel)
        self.ui.btn_generateDSOPoints.clicked.connect(self.generateDSOPoints)
        self.ui.btn_generateDensePoints.clicked.connect(self.generateDensePoints)
        self.ui.btn_generateNormalPoints.clicked.connect(self.generateNormalPoints)
        self.ui.btn_generateGridPoints.clicked.connect(self.generateGridPoints)
        self.ui.btn_generateBasePoints.clicked.connect(self.generateBasePoints)
        self.ui.btn_runAnalyseModel.clicked.connect(self.runAnalyseModel)
        self.ui.btn_cancelAnalyseModel.clicked.connect(self.cancelAnalyseModel)
        self.ui.btn_runTimeChangeModel.clicked.connect(self.runTimeChangeModel)
        self.ui.btn_cancelTimeChangeModel.clicked.connect(self.cancelTimeChangeModel)
        self.ui.btn_runHystereseModel.clicked.connect(self.runHystereseModel)
        self.ui.btn_cancelHystereseModel.clicked.connect(self.cancelHystereseModel)
        self.ui.btn_runPlotAnalyse.clicked.connect(self.runPlotAnalyse)
        self.ui.btn_bootMount.clicked.connect(self.bootMount)
        self.ui.btn_switchCCD.clicked.connect(self.switchCCD)
        self.ui.btn_switchHeater.clicked.connect(self.switchHeater)

    def setParkPos1Text(self):                                                                                              # set text for button 1
        self.ui.btn_mountPos1.setText(self.ui.le_parkPos1Text.text())

    def setParkPos2Text(self):                                                                                              # set text for button 2
        self.ui.btn_mountPos2.setText(self.ui.le_parkPos2Text.text())

    def setParkPos3Text(self):                                                                                              # set text for button 3
        self.ui.btn_mountPos3.setText(self.ui.le_parkPos3Text.text())

    def setParkPos4Text(self):                                                                                              # set text for button 4
        self.ui.btn_mountPos4.setText(self.ui.le_parkPos4Text.text())

    def setAzAltPointer(self, az, alt):                                                                                     # set pointer in graphics
        x, y = getXYEllipse(az, alt, self.ui.modelBasePointsPlot.height(),
                            self.ui.modelBasePointsPlot.width(),
                            self.borderModelPointsView,
                            2 * self.ellipseSizeModelPointsView)                                                            # get xy coordinate
        self.pointerBaseTrackingWidget.setPos(x, y)                                                                         # set widget position to that coordinate
        self.pointerBaseTrackingWidget.setVisible(True)
        self.pointerBaseTrackingWidget.update()                                                                             # update the drawing
        self.pointerRefinementTrackingWidget.setPos(x, y)                                                                   # same for the refinement graphics - coordinate
        self.pointerRefinementTrackingWidget.setVisible(True)
        self.pointerRefinementTrackingWidget.update()                                                                       # and redraw the graphics

    def setDomePointer(self, az):                                                                                           # set pointer in graphics
        width = self.ui.modelBasePointsPlot.width()
        border = self.borderModelPointsView
        x, y = getXYRectangle(az, width, border)
        self.pointerBaseDomeWidget.setPos(x, y)                                                                             # set widget position to that coordinate
        self.pointerBaseDomeWidget.setVisible(True)
        self.pointerBaseDomeWidget.update()                                                                                 # update the drawing
        self.pointerRefinementDomeWidget.setPos(x, y)                                                                       # same for the refinement graphics - coordinate
        self.pointerRefinementDomeWidget.setVisible(True)
        self.pointerRefinementDomeWidget.update()                                                                           # and redraw the graphics

    def mousePressEvent(self, mouseEvent):                                                                                  # overloading the mouse events for handling customized windows
        self.modifiers = mouseEvent.modifiers()
        if mouseEvent.button() == Qt.LeftButton:
            self.moving = True
            self.offset = mouseEvent.pos()

    def mouseMoveEvent(self, mouseEvent):
        if self.moving:
            cursor = QCursor()
            self.move(cursor.pos() - self.offset)

    def mouseReleaseEvent(self, mouseEvent):
        if self.moving:
            cursor = QCursor()
            self.move(cursor.pos() - self.offset)
            self.moving = False

    def initUI(self):
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        darkPalette = QPalette()                                                                                            # set dark palette
        darkPalette.setColor(QPalette.Window, QColor(32, 32, 32))
        darkPalette.setColor(QPalette.WindowText, QColor(192, 192, 192))
        darkPalette.setColor(QPalette.Base, QColor(25, 25, 25))
        darkPalette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        darkPalette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        darkPalette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        darkPalette.setColor(QPalette.Text, self.blueColor)
        darkPalette.setColor(QPalette.Button, QColor(24, 24, 24))
        darkPalette.setColor(QPalette.ButtonText, QColor(192, 192, 192))
        darkPalette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        darkPalette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        self.setPalette(darkPalette)
        palette = QPalette()                                                                                                # title text
        palette.setColor(QPalette.Foreground, self.blueColor)
        palette.setColor(QPalette.Background, QColor(53, 53, 53))
        self.ui.windowTitle.setPalette(palette)
        self.show()                                                                                                         # show window

    def constructModelGrid(self, height, width, border, textheight, scene):                                                 # adding the plot area
        scene.setBackgroundBrush(QColor(32, 32, 32))                                                                        # background color
        pen = QPen(QColor(64, 64, 64), 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                          # building the grid of the plot and the axes
        for i in range(0, 361, 30):                                                                                         # set az ticks
            scene.addLine(border + int(i / 360 * (width - 2 * border)), height - border,
                          border + int(i / 360 * (width - 2 * border)), border, pen)
        for i in range(0, 91, 10):                                                                                          # set alt ticks
            scene.addLine(border, height - border - int(i * (height - 2 * border) / 90),
                          width - border, height - border - int(i * (height - 2*border) / 90), pen)
        scene.addRect(border, border, width - 2*border, height - 2*border, pen)                                             # set frame around graphics
        for i in range(0, 361, 30):                                                                                         # now the texts at the plot x
            text_item = QGraphicsTextItem('{0:03d}'.format(i), None)                                                        # set labels
            text_item.setDefaultTextColor(self.blueColor)                                                                   # coloring of label
            text_item.setPos(int(border / 2) + int(i / 360 * (width - 2 * border)), height - border)                        # placing the text
            scene.addItem(text_item)                                                                                        # adding item to scene to be shown
        for i in range(10, 91, 10):                                                                                         # now the texts at the plot y
            text_item = QGraphicsTextItem('{0:02d}'.format(i), None)
            text_item.setDefaultTextColor(self.blueColor)
            text_item.setPos(width - border, height - border - textheight - int(i * (height - 2 * border) / 90))
            scene.addItem(text_item)
            text_item = QGraphicsTextItem('{0:02d}'.format(i), None)
            text_item.setDefaultTextColor(self.blueColor)
            text_item.setPos(0, height - border - textheight - int(i * (height - 2 * border) / 90))
            scene.addItem(text_item)
        return scene

    def showBasePoints(self):                                                                                               # drawing the points to the grid for base points
        height = self.ui.modelBasePointsPlot.height()                                                                       # get some data out of the gui fields
        width = self.ui.modelBasePointsPlot.width()                                                                         #
        border = self.borderModelPointsView                                                                                 #
        textheight = self.textheightModelPointsView                                                                         #
        esize = self.ellipseSizeModelPointsView                                                                             #
        self.pointerBaseTrackingWidget, self.pointerBaseDomeWidget = \
            self.showPoints(self.ui.modelBasePointsPlot, self.model.BasePoints, self.model.horizonPoints,
                            height, width, border, textheight, esize)

    def showRefinementPoints(self):
        height = self.ui.modelRefinementPointsPlot.height()                                                                 # get some data out of the gui fields
        width = self.ui.modelRefinementPointsPlot.width()                                                                   #
        border = self.borderModelPointsView                                                                                 #
        textheight = self.textheightModelPointsView                                                                         #
        esize = self.ellipseSizeModelPointsView                                                                             #
        self.pointerRefinementTrackingWidget, self.pointerRefinementDomeWidget = \
            self.showPoints(self.ui.modelRefinementPointsPlot, self.model.RefinementPoints, self.model.horizonPoints,
                            height, width, border, textheight, esize)

    def showPoints(self, plotWidget, points, horizon, height, width, border, textheight, esize):
        scene = QGraphicsScene(0, 0, width-2, height-2)                                                                     # set the size of the scene to to not scrolled
        pen = QPen(QColor(128, 128, 128), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                       # outer circle is white
        brush = QBrush(QColor(64, 64, 64))
        domeWidget = scene.addRect(0, 0, int((width - 2 * border) * 30 / 360), int(height - 2 * border), pen, brush)
        domeWidget.setVisible(False)
        domeWidget.setOpacity(0.5)
        scene = self.constructModelGrid(height, width, border, textheight, scene)
        for i, p in enumerate(points):                                                                                      # show the points
            pen = QPen(self.greenColor, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                         # outer circle is white
            x, y = getXYEllipse(p[0], p[1], height, width, border, esize)
            scene.addEllipse(x, y, esize, esize, pen)
            pen = QPen(self.yellowColor, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                        # inner circle -> after modelling green or red
            x, y = getXYEllipse(p[0], p[1], height, width, border, esize/2)
            item = scene.addEllipse(0, 0, esize/2, esize/2, pen)
            item.setPos(x, y)
            text_item = QGraphicsTextItem('{0:02d}'.format(i+1), None)                                                      # put the enumerating number to the circle
            text_item.setDefaultTextColor(self.whiteColor)
            text_item.setPos(x+1, y+1)
            scene.addItem(text_item)
            points[i] = (p[0], p[1], item, True)                                                                            # storing the objects in the list
        scene = constructHorizon(scene, horizon, height, width, border)
        pen = QPen(self.pointerColor, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        trackWidget = scene.addEllipse(0, 0, 2 * esize, 2 * esize, pen)
        trackWidget.setVisible(False)
        plotWidget.setScene(scene)
        return trackWidget, domeWidget

    def loadConfig(self):
        # load the config file
        try:
            with open('config/config.cfg', 'r') as data_file:
                self.config = json.load(data_file)
            data_file.close()
            self.model.loadHorizonPoints(str(self.config['HorizonPointsFileName']))
            self.ui.le_parkPos1Text.setText(self.config['ParkPosText1'])
            self.ui.le_altParkPos1.setText(self.config['ParkPosAlt1'])
            self.ui.le_azParkPos1.setText(self.config['ParkPosAz1'])
            self.setParkPos1Text()
            self.ui.le_parkPos2Text.setText(self.config['ParkPosText2'])
            self.ui.le_altParkPos2.setText(self.config['ParkPosAlt2'])
            self.ui.le_azParkPos2.setText(self.config['ParkPosAz2'])
            self.setParkPos2Text()
            self.ui.le_parkPos3Text.setText(self.config['ParkPosText3'])
            self.ui.le_altParkPos3.setText(self.config['ParkPosAlt3'])
            self.ui.le_azParkPos3.setText(self.config['ParkPosAz3'])
            self.setParkPos3Text()
            self.ui.le_parkPos4Text.setText(self.config['ParkPosText4'])
            self.ui.le_altParkPos4.setText(self.config['ParkPosAlt4'])
            self.ui.le_azParkPos4.setText(self.config['ParkPosAz4'])
            self.setParkPos4Text()
            self.ui.le_modelPointsFileName.setText(self.config['ModelPointsFileName'])
            self.ui.le_horizonPointsFileName.setText(self.config['HorizonPointsFileName'])
            self.ui.le_imageDirectoryName.setText(self.config['ImageDirectoryName'])
            self.ui.cameraBin.setValue(self.config['CameraBin'])
            self.ui.cameraExposure.setValue(self.config['CameraExposure'])
            self.ui.isoSetting.setValue(self.config['ISOSetting'])
            self.ui.checkFastDownload.setChecked(self.config['CheckFastDownload'])
            self.ui.settlingTime.setValue(self.config['SettlingTime'])
            self.ui.checkUseBlindSolve.setChecked(self.config['CheckUseBlindSolve'])
            self.ui.targetRMS.setValue(self.config['TargetRMS'])
            self.ui.pixelSize.setValue(self.config['PixelSize'])
            self.ui.focalLength.setValue(self.config['FocalLength'])
            self.ui.scaleSubframe.setValue(self.config['ScaleSubframe'])
            self.ui.checkDoSubframe.setChecked(self.config['CheckDoSubframe'])
            self.ui.checkTestWithoutCamera.setChecked(self.config['CheckTestWithoutCamera'])
            self.ui.checkAutoRefraction.setChecked(self.config['CheckAutoRefraction'])
            self.ui.le_trackRA.setText(self.config['TrackRA'])
            self.ui.le_trackDEC.setText(self.config['TrackDEC'])
            self.ui.checkKeepImages.setChecked(self.config['CheckKeepImages'])
            self.ui.altitudeBase.setValue(self.config['AltitudeBase'])
            self.ui.azimuthBase.setValue(self.config['AzimuthBase'])
            self.ui.numberGridPointsCol.setValue(self.config['NumberGridPointsCol'])
            self.ui.numberGridPointsRow.setValue(self.config['NumberGridPointsRow'])
            self.ui.scalePlotRA.setValue(self.config['ScalePlotRA'])
            self.ui.scalePlotDEC.setValue(self.config['ScalePlotDEC'])
            self.ui.le_analyseFileName.setText(self.config['AnalyseFileName'])
            self.ui.altitudeTimeChange.setValue(self.config['AltitudeTimeChange'])
            self.ui.azimuthTimeChange.setValue(self.config['AzimuthTimeChange'])
            self.ui.numberRunsTimeChange.setValue(self.config['NumberRunsTimeChange'])
            self.ui.delayTimeTimeChange.setValue(self.config['DelayTimeTimeChange'])
            self.ui.altitudeMinHysterese.setValue(self.config['AltitudeMinHysterese'])
            self.ui.le_ipRelaybox.setText(self.config['IPRelaybox'])
            self.dome.driverName = self.config['ASCOMDomeDriverName']
            self.mount.driverName = self.config['ASCOMTelescopeDriverName']
            self.move(self.config['WindowPositionX'], self.config['WindowPositionY'])
        except Exception as e:
            self.messageQueue.put('Config.cfg could not be loaded !')
            self.logger.error('loadConfig -> item in config.cfg not loaded error:{0}'.format(e))
            return

    def saveConfig(self):
        # put the config data in the json object
        self.config['ParkPosText1'] = self.ui.le_parkPos1Text.text()
        self.config['ParkPosAlt1'] = self.ui.le_altParkPos1.text()
        self.config['ParkPosAz1'] = self.ui.le_azParkPos1.text()
        self.config['ParkPosText2'] = self.ui.le_parkPos2Text.text()
        self.config['ParkPosAlt2'] = self.ui.le_altParkPos2.text()
        self.config['ParkPosAz2'] = self.ui.le_azParkPos2.text()
        self.config['ParkPosText3'] = self.ui.le_parkPos3Text.text()
        self.config['ParkPosAlt3'] = self.ui.le_altParkPos3.text()
        self.config['ParkPosAz3'] = self.ui.le_azParkPos3.text()
        self.config['ParkPosText4'] = self.ui.le_parkPos4Text.text()
        self.config['ParkPosAlt4'] = self.ui.le_altParkPos4.text()
        self.config['ParkPosAz4'] = self.ui.le_azParkPos4.text()
        self.config['ModelPointsFileName'] = self.ui.le_modelPointsFileName.text()
        self.config['HorizonPointsFileName'] = self.ui.le_horizonPointsFileName.text()
        self.config['ImageDirectoryName'] = self.ui.le_imageDirectoryName.text()
        self.config['CameraBin'] = self.ui.cameraBin.value()
        self.config['CameraExposure'] = self.ui.cameraExposure.value()
        self.config['CheckFastDownload'] = self.ui.checkFastDownload.isChecked()
        self.config['ISOSetting'] = self.ui.isoSetting.value()
        self.config['SettlingTime'] = self.ui.settlingTime.value()
        self.config['CheckUseBlindSolve'] = self.ui.checkUseBlindSolve.isChecked()
        self.config['TargetRMS'] = self.ui.targetRMS.value()
        self.config['PixelSize'] = self.ui.pixelSize.value()
        self.config['FocalLength'] = self.ui.focalLength.value()
        self.config['ScaleSubframe'] = self.ui.scaleSubframe.value()
        self.config['CheckDoSubframe'] = self.ui.checkDoSubframe.isChecked()
        self.config['CheckTestWithoutCamera'] = self.ui.checkTestWithoutCamera.isChecked()
        self.config['CheckAutoRefraction'] = self.ui.checkAutoRefraction.isChecked()
        self.config['TrackRA'] = self.ui.le_trackRA.text()
        self.config['TrackDEC'] = self.ui.le_trackDEC.text()
        self.config['CheckKeepImages'] = self.ui.checkKeepImages.isChecked()
        self.config['AltitudeBase'] = self.ui.altitudeBase.value()
        self.config['AzimuthBase'] = self.ui.azimuthBase.value()
        self.config['NumberGridPointsRow'] = self.ui.numberGridPointsRow.value()
        self.config['NumberGridPointsCol'] = self.ui.numberGridPointsCol.value()
        self.config['WindowPositionX'] = self.pos().x()
        self.config['WindowPositionY'] = self.pos().y()
        self.config['ScalePlotRA'] = self.ui.scalePlotRA.value()
        self.config['ScalePlotDEC'] = self.ui.scalePlotDEC.value()
        self.config['AnalyseFileName'] = self.ui.le_analyseFileName.text()
        self.config['AltitudeTimeChange'] = self.ui.altitudeTimeChange.value()
        self.config['AzimuthTimeChange'] = self.ui.azimuthTimeChange.value()
        self.config['NumberRunsTimeChange'] = self.ui.numberRunsTimeChange.value()
        self.config['DelayTimeTimeChange'] = self.ui.delayTimeTimeChange.value()
        self.config['AltitudeMinHysterese'] = self.ui.altitudeMinHysterese.value()
        self.config['IPRelaybox'] = self.ui.le_ipRelaybox.text()
        self.config['ASCOMDomeDriverName'] = self.dome.driverName
        self.config['ASCOMTelescopeDriverName'] = self.mount.driverName

        # save the config file
        try:
            if not os.path.isdir(os.getcwd() + '/config'):                                                                  # if config dir doesn't exist, make it
                os.makedirs(os.getcwd() + '/config')                                                                        # if path doesn't exist, generate is
            with open('config/config.cfg', 'w') as outfile:
                json.dump(self.config, outfile)
            outfile.close()
        except Exception as e:
            self.messageQueue.put('Config.cfg could not be saved !')
            self.logger.error('loadConfig -> item in config.cfg not saved error {0}'.format(e))
            return

    def saveConfigQuit(self):
        self.saveConfig()
        # noinspection PyArgumentList
        QCoreApplication.instance().quit()

    def selectModelPointsFileName(self):
        dlg = QFileDialog()
        dlg.setViewMode(QFileDialog.List)
        dlg.setNameFilter("Text files (*.txt)")
        dlg.setFileMode(QFileDialog.ExistingFile)
        # noinspection PyArgumentList
        a = dlg.getOpenFileName(self, 'Open file', os.getcwd()+'/config', 'Text files (*.txt)')
        if a[0] != '':
            self.ui.le_modelPointsFileName.setText(os.path.basename(a[0]))
        else:
            self.logger.warning('selectModelPointsFile -> no file selected')

    def selectAnalyseFileName(self):
        dlg = QFileDialog()
        dlg.setViewMode(QFileDialog.List)
        dlg.setNameFilter("Text files (*.txt)")
        dlg.setFileMode(QFileDialog.AnyFile)
        # noinspection PyArgumentList
        a = dlg.getOpenFileName(self, 'Open file', os.getcwd()+'/analysedata', 'Text files (*.txt)')
        if a[0] != '':
            self.ui.le_analyseFileName.setText(os.path.basename(a[0]))
        else:
            self.logger.warning('selectAnalyseFile -> no file selected')

    def selectImageDirectoryName(self):
        dlg = QFileDialog()
        dlg.setViewMode(QFileDialog.List)
        dlg.setFileMode(QFileDialog.DirectoryOnly)
        # noinspection PyArgumentList
        a = dlg.getExistingDirectory(self, 'Select directory', os.getcwd())
        if len(a) > 0:
            self.ui.le_imageDirectoryName.setText(a)
        else:
            self.logger.warning('selectModelPointsFile -> no file selected')

    def selectHorizonPointsFileName(self):
        dlg = QFileDialog()
        dlg.setViewMode(QFileDialog.List)
        dlg.setNameFilter("Text files (*.txt)")
        dlg.setFileMode(QFileDialog.ExistingFile)
        # noinspection PyArgumentList
        a = dlg.getOpenFileName(self, 'Open file', os.getcwd()+'/config', 'Text files (*.txt)')
        if a[0] != '':
            self.ui.le_horizonPointsFileName.setText(os.path.basename(a[0]))

    def mountPark(self):
        self.commandQueue.put('hP')

    def mountUnpark(self):
        self.commandQueue.put('PO')

    def startTracking(self):
        self.commandQueue.put('AP')

    def setTrackingLunar(self):
        self.commandQueue.put('RT0')

    def setTrackingSolar(self):
        self.commandQueue.put('RT1')

    def setTrackingSideral(self):
        self.commandQueue.put('RT2')

    def stopTracking(self):
        self.commandQueue.put('RT9')

    def stop(self):
        self.commandQueue.put('STOP')

    def flipMount(self):
        self.commandQueue.put('FLIP')

    def shutdownQuit(self):
        self.saveConfig()
        self.commandQueue.put('shutdown')
        time.sleep(1)
        # noinspection PyArgumentList
        QCoreApplication.instance().quit()

    def setHorizonLimitHigh(self):
        _value = int(self.ui.le_horizonLimitHigh.text())
        if _value < 0:
            _value = 0
        elif _value > 90:
            _value = 90
        self.commandQueue.put('Sh+{0:02d}'.format(_value))

    def setHorizonLimitLow(self):
        _value = int(self.ui.le_horizonLimitLow.text())
        if _value < 0:
            _value = 0
        elif _value > 90:
            _value = 90
        self.commandQueue.put('So+{0:02d}'.format(_value))

    def setDualTracking(self):
        _value = self.ui.le_telescopeDualTrack.text()
        if _value == 'ON':
            _value = 0
            self.ui.le_telescopeDualTrack.setText('OFF')
        else:
            _value = 1
            self.ui.le_telescopeDualTrack.setText('ON')
        self.commandQueue.put('Sdat{0:01d}'.format(_value))

    def setUnattendedFlip(self):
        _value = self.ui.le_telescopeUnattendedFlip.text()
        if _value == 'ON':
            _value = 0
            self.ui.le_telescopeUnattendedFlip.setText('OFF')
        else:
            _value = 1
            self.ui.le_telescopeUnattendedFlip.setText('ON')
        self.commandQueue.put('Suaf{0: 01d}'.format(_value))

    def setRefractionCorrection(self):
        _value = self.ui.le_refractionStatus.text()
        if _value == 'ON':
            _value = 0
            self.ui.le_refractionStatus.setText('OFF')
        else:
            _value = 1
            self.ui.le_refractionStatus.setText('ON')
        self.commandQueue.put('SREF{0: 01d}'.format(_value))

    def setRefractionParameters(self):
        self.commandQueue.put('SetRefractionParameter')

    def mountPosition1(self):
        self.commandQueue.put('PO')                                                                                         # unpark first
        self.commandQueue.put('Sz{0:03d}*00'.format(int(self.ui.le_azParkPos1.text())))                                     # set az
        self.commandQueue.put('Sa+{0:02d}*00'.format(int(self.ui.le_altParkPos1.text())))                                   # set alt
        self.commandQueue.put('MA')                                                                                         # start Slewing

    def mountPosition2(self):
        self.commandQueue.put('PO')                                                                                         # unpark first
        self.commandQueue.put('Sz{0:03d}*00'.format(int(self.ui.le_azParkPos2.text())))                                     # set az
        self.commandQueue.put('Sa+{0:02d}*00'.format(int(self.ui.le_altParkPos2.text())))                                   # set alt
        self.commandQueue.put('MA')                                                                                         # start Slewing

    def mountPosition3(self):
        self.commandQueue.put('PO')                                                                                         # unpark first
        self.commandQueue.put('Sz{0:03d}*00'.format(int(self.ui.le_azParkPos3.text())))                                     # set az
        self.commandQueue.put('Sa+{0:02d}*00'.format(int(self.ui.le_altParkPos3.text())))                                   # set alt
        self.commandQueue.put('MA')                                                                                         # start Slewing

    def mountPosition4(self):
        self.commandQueue.put('PO')                                                                                         # unpark first
        self.commandQueue.put('Sz{0:03d}*00'.format(int(self.ui.le_azParkPos4.text())))                                     # set az
        self.commandQueue.put('Sa+{0:02d}*00'.format(int(self.ui.le_altParkPos4.text())))                                   # set alt
        self.commandQueue.put('MA')                                                                                         # start Slewing
    #
    # mount handling
    #

    def setMountStatus(self, status):
        if status:
            self.ui.le_driverMountConnected.setStyleSheet('QLineEdit {background-color: green;}')
        else:
            self.ui.le_driverMountConnected.setStyleSheet('QLineEdit {background-color: red;}')

    def getAlignmentModel(self):
        self.commandQueue.put('GetAlignmentModel')

    def runTargetRMSAlignment(self):
        self.commandQueue.put('RunTargetRMSAlignment')

    def backupModel(self):
        self.commandQueue.put('BackupModel')

    def restoreModel(self):
        self.commandQueue.put('RestoreModel')

    def saveSimpleModel(self):
        self.commandQueue.put('SaveSimpleModel')

    def loadSimpleModel(self):
        self.commandQueue.put('LoadSimpleModel')

    def setupMountDriver(self):
        self.mount.setupDriver()

    def fillMountData(self, data):
        if data['Name'] == 'Reply':
            pass
            # print(data['Value'])
        if data['Name'] == 'GetDualAxisTracking':
            if data['Value'] == '1':
                self.ui.le_telescopeDualTrack.setText('ON')
            else:
                self.ui.le_telescopeDualTrack.setText('OFF')
        if data['Name'] == 'NumberAlignmentStars':
            self.ui.le_alignNumberStars.setText(str(data['Value']))
        if data['Name'] == 'ModelRMSError':
            self.ui.le_alignError.setText(str(data['Value']))
        if data['Name'] == 'ModelStarError':
            if data['Value'] == 'delete':
                self.ui.alignErrorStars.setText('')
            else:
                self.ui.alignErrorStars.setText(self.ui.alignErrorStars.toPlainText() + data['Value'])
                self.ui.alignErrorStars.moveCursor(QTextCursor.End)
        if data['Name'] == 'GetCurrentHorizonLimitLow':
            self.ui.le_horizonLimitLow.setText(str(data['Value']))
        if data['Name'] == 'GetCurrentHorizonLimitHigh':
            self.ui.le_horizonLimitHigh.setText(str(data['Value']))
        if data['Name'] == 'GetCurrentSiteLongitude':
            self.ui.le_siteLongitude.setText(str(data['Value']))
        if data['Name'] == 'GetCurrentSiteLatitude':
            self.ui.le_siteLatitude.setText(str(data['Value']))
        if data['Name'] == 'GetCurrentSiteElevation':
            self.ui.le_siteElevation.setText(str(data['Value']))
        if data['Name'] == 'GetLocalTime':
            self.ui.le_localTime.setText(str(data['Value']))
        if data['Name'] == 'GetTelescopeTempRA':
            self.ui.le_telescopeTempRAMotor.setText(str(data['Value']))
        if data['Name'] == 'GetTelescopeTempDEC':
            self.ui.le_telescopeTempDECMotor.setText(str(data['Value']))
        if data['Name'] == 'GetRefractionTemperature':
            self.ui.le_refractionTemperature.setText(str(data['Value']))
        if data['Name'] == 'GetRefractionPressure':
            self.ui.le_refractionPressure.setText(str(data['Value']))
        if data['Name'] == 'GetRefractionStatus':
            if data['Value'] == '1':
                self.ui.le_refractionStatus.setText('ON')
            else:
                self.ui.le_refractionStatus.setText('OFF')
        if data['Name'] == 'GetMountStatus':
            self.ui.le_mountStatus.setText(str(self.mount.statusReference[data['Value']]))
            self.ui.btn_startTracking.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
            self.ui.btn_stopTracking.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
            self.ui.btn_mountPark.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
            self.ui.btn_mountUnpark.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
            self.ui.btn_stop.setStyleSheet('background-color: rgb(32,32,32); color: rgb(192,192,192)')
            if data['Value'] == '0':
                self.ui.btn_startTracking.setStyleSheet('background-color: rgb(42, 130, 218)')
                self.ui.btn_mountUnpark.setStyleSheet('background-color: rgb(42, 130, 218)')
            elif data['Value'] == '1':
                self.ui.btn_stop.setStyleSheet('background-color: rgb(42, 130, 218)')
                self.ui.btn_stopTracking.setStyleSheet('background-color: rgb(42, 130, 218)')
                self.ui.btn_mountUnpark.setStyleSheet('background-color: rgb(42, 130, 218)')
            elif data['Value'] == '5':
                self.ui.btn_mountPark.setStyleSheet('background-color: rgb(42, 130, 218)')
                self.ui.btn_stopTracking.setStyleSheet('background-color: rgb(42, 130, 218)')
            elif data['Value'] == '7':
                self.ui.btn_stopTracking.setStyleSheet('background-color: rgb(42, 130, 218)')
                self.ui.btn_mountUnpark.setStyleSheet('background-color: rgb(42, 130, 218)')
        if data['Name'] == 'GetTelescopeDEC':
            self.ui.le_telescopeDEC.setText(data['Value'])
        if data['Name'] == 'GetTelescopeRA':
            self.ui.le_telescopeRA.setText(str(data['Value']))
        if data['Name'] == 'GetTelescopeAltitude':
            self.ui.le_telescopeAltitude.setText(str(data['Value']))
        if data['Name'] == 'GetTelescopeAzimuth':
            self.ui.le_telescopeAzimut.setText(str(data['Value']))
        if data['Name'] == 'GetSlewRate':
            self.ui.le_slewRate.setText(str(data['Value']))
        if data['Name'] == 'GetUnattendedFlip':
            if data['Value'] == '1':
                self.ui.le_telescopeUnattendedFlip.setText('ON')
            else:
                self.ui.le_telescopeUnattendedFlip.setText('OFF')
        if data['Name'] == 'GetFirmwareProductName':
            self.ui.le_firmwareProductName.setText(str(data['Value']))
        if data['Name'] == 'GetFirmwareNumber':
            self.ui.le_firmwareNumber.setText(str(data['Value']))
        if data['Name'] == 'GetFirmwareDate':
            self.ui.le_firmwareDate.setText(str(data['Value']))
        if data['Name'] == 'GetFirmwareTime':
            self.ui.le_firmwareTime.setText(str(data['Value']))
        if data['Name'] == 'GetHardwareVersion':
            self.ui.le_hardwareVersion.setText(str(data['Value']))
        if data['Name'] == 'GetTelescopePierSide':
            self.ui.le_telescopePierSide.setText(str(data['Value']))
        if data['Name'] == 'GetTimeToTrackingLimit':
            self.ui.le_timeToTrackingLimit.setText(str(data['Value']))

    #
    # stick handling
    #
    def setupStickDriver(self):
        self.stick.setupDriver()

    def setStickStatus(self, status):
        if status:
            self.ui.le_driverStickConnected.setStyleSheet('QLineEdit {background-color: green;}')
        else:
            self.ui.le_driverStickConnected.setStyleSheet('QLineEdit {background-color: red;}')

    def fillStickData(self, data):
        # data from Stickstation via signal connected
        self.ui.le_dewPointStick.setText(str(data['DewPoint']))
        self.ui.le_temperatureStick.setText(str(data['Temperature']))
        self.ui.le_humidityStick.setText(str(data['Humidity']))
        self.ui.le_pressureStick.setText(str(data['Pressure']))

    #
    # open weather handling
    #
    def setupWeatherDriver(self):
        self.weather.setupDriver()

    def setWeatherStatus(self, status):
        if status:
            self.ui.le_driverWeatherConnected.setStyleSheet('QLineEdit {background-color: green;}')
        else:
            self.ui.le_driverWeatherConnected.setStyleSheet('QLineEdit {background-color: red;}')

    def fillWeatherData(self, data):
        # data from Stickstation via signal connected
        self.ui.le_dewPointWeather.setText(str(data['DewPoint']))
        self.ui.le_temperatureWeather.setText(str(data['Temperature']))
        self.ui.le_humidityWeather.setText(str(data['Humidity']))
        self.ui.le_pressureWeather.setText(str(data['Pressure']))
        self.ui.le_cloudCoverWeather.setText(str(data['CloudCover']))
        self.ui.le_rainRateWeather.setText(str(data['RainRate']))
        self.ui.le_windSpeedWeather.setText(str(data['WindSpeed']))
        self.ui.le_windDirectionWeather.setText(str(data['WindDirection']))
    #
    # Relay Box Handling
    #

    def bootMount(self):
        self.relays.bootMount()

    def switchHeater(self):
        self.relays.switchHeater()

    def switchCCD(self):
        self.relays.switchCCD()
    #
    # SGPRO and Modelling handling
    #

    def setSGProStatus(self, status):
        if status:
            self.ui.le_sgproConnected.setStyleSheet('QLineEdit {background-color: green;}')
        else:
            self.ui.le_sgproConnected.setStyleSheet('QLineEdit {background-color: red;}')

    def setupDomeDriver(self):
        self.dome.setupDriver()

    def setDomeStatus(self, status):
        if status == 1:
            self.ui.le_domeConnected.setStyleSheet('QLineEdit {background-color: green;}')
        elif status == 2:
            self.ui.le_domeConnected.setStyleSheet('QLineEdit {background-color: grey;}')
        else:
            self.ui.le_domeConnected.setStyleSheet('QLineEdit {background-color: red;}')

    def runBaseModel(self):
        self.model.signalModelCommand.emit('RunBaseModel')

    def cancelBaseModel(self):
        self.model.signalModelCommand.emit('CancelBaseModel')

    def runRefinementModel(self):
        self.model.signalModelCommand.emit('RunRefinementModel')

    def cancelRefinementModel(self):
        self.model.signalModelCommand.emit('CancelRefinementModel')

    def sortRefinementPoints(self):
        self.model.signalModelCommand.emit('SortRefinementPoints')

    def deleteBelowHorizonLine(self):
        self.model.signalModelCommand.emit('DeleteBelowHorizonLine')

    def clearAlignmentModel(self):
        self.model.signalModelCommand.emit('ClearAlignmentModel')

    def loadModelBasePoints(self):
        self.model.loadModelPoints(self.ui.le_modelPointsFileName.text(), 'base')
        self.showBasePoints()

    def loadModelRefinementPoints(self):
        self.model.loadModelPoints(self.ui.le_modelPointsFileName.text(), 'refinement')
        self.showRefinementPoints()

    def generateDSOPoints(self):
        self.model.signalModelCommand.emit('GenerateDSOPoints')

    def generateDensePoints(self):
        self.model.signalModelCommand.emit('GenerateDensePoints')

    def generateNormalPoints(self):
        self.model.signalModelCommand.emit('GenerateNormalPoints')

    def generateGridPoints(self):
        self.model.signalModelCommand.emit('GenerateGridPoints')

    def generateBasePoints(self):
        self.model.signalModelCommand.emit('GenerateBasePoints')

    def runAnalyseModel(self):
        self.model.signalModelCommand.emit('RunAnalyseModel')

    def cancelAnalyseModel(self):
        self.model.signalModelCommand.emit('CancelAnalyseModel')

    def runTimeChangeModel(self):
        self.model.signalModelCommand.emit('RunTimeChangeModel')

    def cancelTimeChangeModel(self):
        self.model.signalModelCommand.emit('CancelTimeChangeModel')

    def runHystereseModel(self):
        self.model.signalModelCommand.emit('RunHystereseModel')

    def cancelHystereseModel(self):
        self.model.signalModelCommand.emit('CancelHystereseModel')

    def runPlotAnalyse(self):
        data = self.analyse.loadData(self.ui.le_analyseFileName.text())                                                     # load data file
        if len(data) > 0:                                                                                                   # if data is in the file‚
            self.analyse.plotData(data, self.ui.scalePlotRA.value(), self.ui.scalePlotDEC.value())                          # show plots
    #
    # basis loop for cyclic topic in gui
    #

    def mainLoop(self):
        while not self.modelLogQueue.empty():                                                                               # checking if in queue is something to do
            text = self.modelLogQueue.get()                                                                                 # if yes, getting the work command
            if text == 'delete':                                                                                            # delete logfile for modeling
                self.ui.modellingLog.setText('')                                                                            # reset window text
            else:
                self.ui.modellingLog.setText(self.ui.modellingLog.toPlainText() + text)                                     # otherwise add text at the end
            self.ui.modellingLog.moveCursor(QTextCursor.End)                                                                # and move cursor up
            self.modelLogQueue.task_done()
        while not self.mountDataQueue.empty():                                                                              # checking data transfer from mount to GUI
            data = self.mountDataQueue.get()                                                                                # get the data from the queue
            self.fillMountData(data)                                                                                        # write dta in gui
            self.mountDataQueue.task_done()
        while not self.messageQueue.empty():                                                                                # do i have error messages ?
            text = self.messageQueue.get()                                                                                  # get the message
            self.ui.errorStatus.setText(self.ui.errorStatus.toPlainText() + text + '\n')                                    # write it to window
            self.messageQueue.task_done()
        self.ui.errorStatus.moveCursor(QTextCursor.End)                                                                     # move cursor
        # noinspection PyCallByClass,PyTypeChecker
        QTimer.singleShot(200, self.mainLoop)                                                                               # 200ms repeat time cyclic

if __name__ == "__main__":

    def except_hook(typeException, valueException, tbackException):                                                         # manage unhandled exception here
        logging.error('Exception: type:{0} value:{1} tback:{2}'.format(typeException, valueException, tbackException))      # write to logger
        sys.__excepthook__(typeException, valueException, tbackException)                                                   # then call the default handler

    if len(sys.argv) > 1:                                                                                                   # some arguments are given, at least 1
        if sys.argv[1] == '-d':                                                                                             # than we can check for debug option
            logging.basicConfig(filename='mount.log', level=logging.DEBUG, format='%(asctime)s --- %(message)s', datefmt='%Y-%m-%d %I:%M:%S')
    else:                                                                                                                   # set logging level accordingly
        logging.basicConfig(filename='mount.log', level=logging.ERROR, format='%(asctime)s --- %(message)s', datefmt='%Y-%m-%d %I:%M:%S')
    if not os.path.isdir(os.getcwd() + '/analysedata'):                                                                     # if analyse dir doesn't exist, make it
        os.makedirs(os.getcwd() + '/analysedata')                                                                           # if path doesn't exist, generate is
    if not os.path.isdir(os.getcwd() + '/images'):                                                                          # if images dir doesn't exist, make it
        os.makedirs(os.getcwd() + '/images')                                                                                # if path doesn't exist, generate is
    if not os.path.isdir(os.getcwd() + '/config'):                                                                          # if config dir doesn't exist, make it
        os.makedirs(os.getcwd() + '/config')                                                                                # if path doesn't exist, generate is
    logging.error('MountWizzard started !\n')                                                                               # start message logger
    app = QApplication(sys.argv)                                                                                            # built application
    sys.excepthook = except_hook                                                                                            # manage except hooks for logging
    # noinspection PyCallByClass,PyTypeChecker,PyArgumentList
    app.setStyle(QStyleFactory.create('Fusion'))                                                                            # set theme
    mountApp = MountWizzardApp()                                                                                            # instantiate Application
    sys.exit(app.exec_())                                                                                                   # close application
    logging.error('MountWizzard stopped !\n')                                                                               # stop message logger
