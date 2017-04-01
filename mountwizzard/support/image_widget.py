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
        self.showStatus = False                                                                                             # show coordinate window
        self.ui = Ui_ImageDialog()                                                                                          # PyQt5 dialog ui
        self.ui.setupUi(self)                                                                                               # setup the ui
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

    def connectCamPS(self):
        self.app.AscomCamera.connectCameraPlateSolver()

    def disconnectCamPS(self):
        self.app.AscomCamera.disconnectCameraPlateSolver()

    def showFitsImage(self, filename):
        hdulist = pyfits.open(filename)
        image = hdulist[0].data
        self.imageWidget.plt.imshow(image, cmap='gray', norm=LogNorm(vmin=numpy.min(image) * 1.05, vmax=numpy.max(image)/10))
        self.imageWidget.draw()

    def showImage(self, image):
        self.imageWidget.plt.imshow(image)
        self.imageWidget.draw()

    def expose(self):
        if self.app.AscomCamera.connectedCamera:
            param = {}
            suc, mes, sizeX, sizeY, canSubframe, gainValue = self.app.AscomCamera.getCameraProps()
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
            # suc, mes, image = self.app.AscomCamera.getImageRaw(param)
            if suc:
                self.showFitsImage('C:/Program Files (x86)/Common Files/ASCOM/Camera/ASCOM.Simulator.Camera/M101.fit')
