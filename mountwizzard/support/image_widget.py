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
# standard solutions
import logging
import time
import os
# import for the PyQt5 Framework
import PyQt5.QtWidgets
from support.mw_widget import MwWidget
from support.image_dialog_ui import Ui_ImageDialog
# FIT file handling
import pyfits
# numpy
import numpy
# matplotlib
import matplotlib
matplotlib.use('Qt5Agg')
# when using multiple embedded plots in different windows you should use figure instead of pyplot, because the state
# machine from pyplot mixed multiple instances up.
from matplotlib import figure as figure
from matplotlib.colors import LogNorm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class ShowImageData(FigureCanvas):

    def __init__(self, parent=None):
        self.fig = figure.Figure(dpi=75, frameon=True, facecolor=(25/256, 25/256, 25/256))
        self.axes = self.fig.add_axes([0., 0., 1., 1.])
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.updateGeometry(self)


class ShowImagePopup(MwWidget):
    logger = logging.getLogger(__name__)
    BASENAME = 'exposure-'

    def __init__(self, app):
        super(ShowImagePopup, self).__init__()
        self.app = app
        self.showStatus = False
        self.sizeX = 10
        self.sizeY = 10
        self.imageVmin = 1
        self.imageVmax = 65535
        self.image = numpy.random.randint(low=5, high=100, size=(20, 20))
        self.cmapColor = 'gray'
        self.ui = Ui_ImageDialog()                                                                                          # PyQt5 dialog ui
        self.ui.setupUi(self)                                                                                               # setup the ui
        self.ui.btn_strechLow.setChecked(True)
        self.ui.btn_size100.setChecked(True)
        self.ui.btn_colorGray.setChecked(True)
        self.initUI()                                                                                                       # adaptions to ui setup
        self.ui.windowTitle.setPalette(self.palette)                                                                        # set windows palette
        self.show()                                                                                                         # construct the window
        self.setVisible(False)                                                                                              # but hide it first
        helper = PyQt5.QtWidgets.QVBoxLayout(self.ui.image)
        self.imageWidget = ShowImageData(self.ui.image)
        helper.addWidget(self.imageWidget)
        self.imageWidget.axes.set_facecolor((25/256, 25/256, 25/256))
        self.initConfig()

        self.ui.btn_connectCamPS.clicked.connect(self.connectCamPS)
        self.ui.btn_disconnectCamPS.clicked.connect(self.disconnectCamPS)
        self.ui.btn_expose.clicked.connect(self.expose)
        self.ui.btn_colorGray.clicked.connect(self.setColor)
        self.ui.btn_colorCool.clicked.connect(self.setColor)
        self.ui.btn_colorRainbow.clicked.connect(self.setColor)
        self.ui.btn_size25.clicked.connect(self.setZoom)
        self.ui.btn_size50.clicked.connect(self.setZoom)
        self.ui.btn_size100.clicked.connect(self.setZoom)
        self.ui.btn_strechLow.clicked.connect(self.setStrech)
        self.ui.btn_strechMid.clicked.connect(self.setStrech)
        self.ui.btn_strechHigh.clicked.connect(self.setStrech)

    def initConfig(self):
        try:
            if 'ImagePopupWindowPositionX' in self.app.config:
                self.move(self.app.config['ImagePopupWindowPositionX'], self.app.config['ImagePopupWindowPositionY'])
            if 'ImagePopupWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['ImagePopupWindowShowStatus']
        except Exception as e:
            self.logger.error('initConfig -> item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['ImagePopupWindowPositionX'] = self.pos().x()
        self.app.config['ImagePopupWindowPositionY'] = self.pos().y()
        self.app.config['ImagePopupWindowShowStatus'] = self.showStatus

    def connectCamPS(self):
        self.app.model.AscomCamera.connectCameraPlateSolver()

    def disconnectCamPS(self):
        self.app.model.AscomCamera.disconnectCameraPlateSolver()

    def setColor(self):
        if self.ui.btn_colorCool.isChecked():
            self.setColorCool()
        elif self.ui.btn_colorRainbow.isChecked():
            self.setColorRainbow()
        else:
            self.setColorGrey()
        self.setStrech()

    def setColorGrey(self):
        self.cmapColor = 'gray'

    def setColorCool(self):
        self.cmapColor = 'plasma'

    def setColorRainbow(self):
        self.cmapColor = 'rainbow'

    def setStrech(self):
        if self.ui.btn_strechLow.isChecked():
            self.strechLow()
        elif self.ui.btn_strechMid.isChecked():
            self.strechMid()
        else:
            self.strechHigh()

    def strechLow(self):
        self.imageVmin = numpy.min(self.image) * 1
        self.imageVmax = max(numpy.max(self.image) / 2, self.imageVmin + 1)
        self.imageWidget.axes.imshow(self.image, cmap=self.cmapColor, norm=LogNorm(self.imageVmin, self.imageVmax))
        self.imageWidget.draw()

    def strechMid(self):
        self.imageVmin = numpy.min(self.image) * 1.05
        self.imageVmax = max(numpy.max(self.image) / 10, self.imageVmin + 1)
        self.imageWidget.axes.imshow(self.image, cmap=self.cmapColor, norm=LogNorm(self.imageVmin, self.imageVmax))
        self.imageWidget.draw()

    def strechHigh(self):
        self.imageVmin = numpy.min(self.image) * 1.1
        self.imageVmax = max(numpy.max(self.image) / 20, self.imageVmin + 1)
        self.imageWidget.axes.imshow(self.image, cmap=self.cmapColor, norm=LogNorm(self.imageVmin, self.imageVmax))
        self.imageWidget.draw()

    def setZoom(self):
        if self.ui.btn_size25.isChecked():
            self.zoom25()
        elif self.ui.btn_size50.isChecked():
            self.zoom50()
        else:
            self.zoom100()

    def zoom25(self):
        if self.sizeX:
            minx = int(self.sizeX * 3 / 8)
            maxx = minx + int(self.sizeX / 4)
            miny = int(self.sizeY * 3 / 8)
            maxy = miny + int(self.sizeY / 4)
            self.imageWidget.axes.set_xlim(xmin=minx, xmax=maxx)
            self.imageWidget.axes.set_ylim(ymin=miny, ymax=maxy)
            self.imageWidget.draw()

    def zoom50(self):
        if self.sizeX:
            minx = int(self.sizeX / 4)
            maxx = minx + int(self.sizeX / 2)
            miny = int(self.sizeY / 4)
            maxy = miny + int(self.sizeY / 2)
            self.imageWidget.axes.set_xlim(xmin=minx, xmax=maxx)
            self.imageWidget.axes.set_ylim(ymin=miny, ymax=maxy)
            self.imageWidget.draw()

    def zoom100(self):
        if self.sizeX:
            minx = 0
            maxx = self.sizeX
            miny = 0
            maxy = self.sizeY
            self.imageWidget.axes.set_xlim(xmin=minx, xmax=maxx)
            self.imageWidget.axes.set_ylim(ymin=miny, ymax=maxy)
            self.imageWidget.draw()

    def showFitsImage(self, filename):
        hdulist = pyfits.open(filename)
        self.image = hdulist[0].data
        self.sizeY, self.sizeX = self.image.shape
        self.setStrech()
        self.setZoom()

    def showImage(self, imagedata):
        self.image = imagedata
        self.sizeY, self.sizeX = self.image.shape
        self.setStrech()
        self.setZoom()

    def expose(self):
        if self.app.model.AscomCamera.connectedCamera:
            param = {}
            suc, mes, sizeX, sizeY, canSubframe, gainValue = self.app.model.AscomCamera.getCameraProps()
            param['binning'] = 1
            param['exposure'] = 1
            directory = time.strftime("%Y-%m-%d-exposure", time.gmtime())
            param['base_dir_images'] = self.app.ui.le_imageDirectoryName.text() + '/' + directory
            number = 0
            while os.path.isfile(param['base_dir_images'] + '/' + self.BASENAME + '{0:04d}.fit'.format(number)):
                number += 1
            param['file'] = self.BASENAME + '{0:04d}.fit'.format(number)
            param = self.app.model.prepareCaptureImageSubframes(1, sizeX, sizeY, canSubframe, param)
            if not os.path.isdir(param['base_dir_images']):
                os.makedirs(param['base_dir_images'])
            suc, mes, image = self.app.model.AscomCamera.getImageRaw(param)
            if suc:
                self.showImage(image)
