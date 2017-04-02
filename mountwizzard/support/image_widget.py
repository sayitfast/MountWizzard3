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
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class ShowImageData(FigureCanvas):

    def __init__(self, parent=None):
        self.plt = plt
        self.fig = self.plt.figure(dpi=75, frameon=True)
        rect = self.fig.patch
        rect.set_facecolor((25/256, 25/256, 25/256))
        plt.axis('off')
        ax = plt.Axes(self.fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        self.fig.add_axes(ax)
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
        self.param = {}
        self.imageVmin = 1
        self.imageVmax = 65535
        self.image = None
        self.ui = Ui_ImageDialog()                                                                                          # PyQt5 dialog ui
        self.ui.setupUi(self)                                                                                               # setup the ui
        self.ui.btn_strechLow.setChecked(True)
        self.ui.btn_size100.setChecked(True)
        self.initUI()                                                                                                       # adaptions to ui setup
        self.ui.windowTitle.setPalette(self.palette)                                                                        # set windows palette
        self.show()                                                                                                         # construct the window
        self.setVisible(False)                                                                                              # but hide it first
        helper = PyQt5.QtWidgets.QVBoxLayout(self.ui.image)
        self.imageWidget = ShowImageData(self.ui.image)
        helper.addWidget(self.imageWidget)

        self.ui.btn_connectCamPS.clicked.connect(self.connectCamPS)
        self.ui.btn_disconnectCamPS.clicked.connect(self.disconnectCamPS)
        self.ui.btn_expose.clicked.connect(self.expose)
        self.ui.btn_size25.clicked.connect(self.zoom25)
        self.ui.btn_size50.clicked.connect(self.zoom50)
        self.ui.btn_size100.clicked.connect(self.zoom100)
        self.ui.btn_strechLow.clicked.connect(self.strechLow)
        self.ui.btn_strechMid.clicked.connect(self.strechMid)
        self.ui.btn_strechHigh.clicked.connect(self.strechHigh)

    def connectCamPS(self):
        self.app.AscomCamera.connectCameraPlateSolver()

    def disconnectCamPS(self):
        self.app.AscomCamera.disconnectCameraPlateSolver()

    def strechLow(self):
        self.imageVmin = numpy.min(self.image) * 1
        self.imageVmax = numpy.max(self.image) / 2
        self.imageWidget.plt.imshow(self.image, cmap='gray', norm=LogNorm(self.imageVmin, self.imageVmax))
        self.imageWidget.draw()

    def strechMid(self):
        self.imageVmin = numpy.min(self.image) * 1.05
        self.imageVmax = numpy.max(self.image) / 10
        self.imageWidget.plt.imshow(self.image, cmap='gray', norm=LogNorm(self.imageVmin, self.imageVmax))
        self.imageWidget.draw()

    def strechHigh(self):
        self.imageVmin = numpy.min(self.image) * 1.1
        self.imageVmax = numpy.max(self.image) / 20
        self.imageWidget.plt.imshow(self.image, cmap='gray', norm=LogNorm(self.imageVmin, self.imageVmax))
        self.imageWidget.draw()

    def zoom25(self):
        if self.param['sizeX']:
            minx = int(self.param['sizeX'] * 3 / 8)
            maxx = minx + int(self.param['sizeX'] / 4)
            miny = int(self.param['sizeY'] * 3 / 8)
            maxy = miny + int(self.param['sizeY'] / 4)
            plt.xlim(minx, maxx)
            plt.ylim(miny, maxy)
            self.imageWidget.draw()

    def zoom50(self):
        if self.param['sizeX']:
            minx = int(self.param['sizeX'] / 4)
            maxx = minx + int(self.param['sizeX'] / 2)
            miny = int(self.param['sizeY'] / 4)
            maxy = miny + int(self.param['sizeY'] / 2)
            plt.xlim(minx, maxx)
            plt.ylim(miny, maxy)
            self.imageWidget.draw()

    def zoom100(self):
        if self.param['sizeX']:
            minx = 0
            maxx = self.param['sizeX']
            miny = 0
            maxy = self.param['sizeY']
            plt.xlim(minx, maxx)
            plt.ylim(miny, maxy)
            self.imageWidget.draw()

    def showFitsImage(self, filename):
        hdulist = pyfits.open(filename)
        self.image = hdulist[0].data
        self.strechLow()

    def showImage(self, imagedata):
        self.image = imagedata
        self.imageWidget.plt.imshow(self.image)
        self.imageWidget.draw()

    def expose(self):
        if self.app.AscomCamera.connectedCamera:
            suc, mes, sizeX, sizeY, canSubframe, gainValue = self.app.AscomCamera.getCameraProps()
            self.param['binning'] = 1
            self.param['exposure'] = 1
            directory = time.strftime("%Y-%m-%d-exposure", time.gmtime())
            self.param['base_dir_images'] = self.app.ui.le_imageDirectoryName.text() + '/' + directory
            number = 0
            while os.path.isfile(self.param['base_dir_images'] + '/' + self.BASENAME + '{0:04d}.fit'.format(number)):
                number += 1
            self.param['file'] = self.BASENAME + '{0:04d}.fit'.format(number)
            self.param = self.app.model.prepareCaptureImageSubframes(1, sizeX, sizeY, canSubframe, self.param)
            if not os.path.isdir(self.param['base_dir_images']):
                os.makedirs(self.param['base_dir_images'])
            # suc, mes, image = self.app.AscomCamera.getImageRaw(param)
            if suc:
                self.showFitsImage('C:/Program Files (x86)/Common Files/ASCOM/Camera/ASCOM.Simulator.Camera/M101.fit')
