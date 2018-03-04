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
import time
import numpy
import PyQt5
import astropy.io.fits as pyfits
from astropy.visualization import MinMaxInterval, ImageNormalize, AsymmetricPercentileInterval, PowerStretch
from matplotlib import use
from baseclasses import widget
from astrometry import transform
from gui import image_dialog_ui
use('Qt5Agg')
# from matplotlib.colors import LogNorm, SymLogNorm, PowerNorm


class ImagesWindow(widget.MwWidget):
    logger = logging.getLogger(__name__)
    BASENAME = 'exposure-'

    def __init__(self, app):
        super(ImagesWindow, self).__init__()
        self.app = app
        self.showStatus = False
        self.imagePath = ''

        self.transform = transform.Transform(self.app)

        self.sizeX = 10
        self.sizeY = 10
        self.imageVmin = 1
        self.imageVmax = 65535
        self.image = numpy.random.randint(low=5, high=100, size=(20, 20))
        self.cmapColor = 'gray'
        self.ui = image_dialog_ui.Ui_ImageDialog()
        self.ui.setupUi(self)
        self.ui.btn_strechLow.setChecked(True)
        self.ui.btn_size100.setChecked(True)
        self.ui.btn_colorGrey.setChecked(True)
        self.initUI()
        self.initConfig()

        self.imageMatplotlib = widget.IntegrateMatplotlib(self.ui.image)
        self.imageMatplotlib.axes = self.imageMatplotlib.fig.add_axes([0., 0., 1., 1.])
        self.imageMatplotlib.axes.set_facecolor((25/256, 25/256, 25/256))
        self.imageMatplotlib.axes.set_axis_off()

        self.ui.btn_expose.clicked.connect(self.exposeOnce)
        self.ui.btn_solve.clicked.connect(self.solveOnce)
        self.ui.btn_crosshair.clicked.connect(self.crosshairOnOff)
        self.ui.btn_colorGrey.clicked.connect(self.setColor)
        self.ui.btn_colorCool.clicked.connect(self.setColor)
        self.ui.btn_colorRainbow.clicked.connect(self.setColor)
        self.ui.btn_size25.clicked.connect(self.setZoom)
        self.ui.btn_size50.clicked.connect(self.setZoom)
        self.ui.btn_size100.clicked.connect(self.setZoom)
        self.ui.btn_strechLow.clicked.connect(self.setStrech)
        self.ui.btn_strechMid.clicked.connect(self.setStrech)
        self.ui.btn_strechHigh.clicked.connect(self.setStrech)
        self.setVisible(False)
        self.ui.cross1.setVisible(False)
        self.ui.cross2.setVisible(False)
        self.ui.cross3.setVisible(False)
        self.ui.cross4.setVisible(False)

    def initConfig(self):
        try:
            if 'ImagePopupWindowPositionX' in self.app.config:
                x = self.app.config['ImagePopupWindowPositionX']
                y = self.app.config['ImagePopupWindowPositionY']
                if x > self.screenSizeX:
                    x = 0
                if y > self.screenSizeY:
                    y = 0
                self.move(x, y)
            if 'ImagePopupWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['ImagePopupWindowShowStatus']
            if 'ImagePath' in self.app.config:
                self.imagePath = self.app.config['ImagePath']
                self.ui.le_imageFile.setText(self.imagePath)
                if os.path.isfile(self.imagePath):
                    self.showFitsImage(self.imagePath)
        except Exception as e:
            self.logger.error('Item in config.cfg not be initialized for image window, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['ImagePopupWindowPositionX'] = self.pos().x()
        self.app.config['ImagePopupWindowPositionY'] = self.pos().y()
        self.app.config['ImagePopupWindowShowStatus'] = self.showStatus
        self.app.config['ImagePath'] = self.imagePath

    def showWindow(self):
        self.showStatus = True
        self.setVisible(True)
        self.show()

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
        # Create interval object
        interval = AsymmetricPercentileInterval(25, 99.99)
        vmin, vmax = interval.get_limits(self.image)
        # Create an ImageNormalize object using a LogStrech object
        norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=PowerStretch(1))
        # Display the image
        self.imageMatplotlib.axes.imshow(self.image, cmap=self.cmapColor, norm=norm)
        self.imageMatplotlib.draw()

    def strechMid(self):
        # Create interval object
        interval = AsymmetricPercentileInterval(25, 99.8)
        vmin, vmax = interval.get_limits(self.image)
        # Create an ImageNormalize object using a LogStrech object
        norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=PowerStretch(1))
        # Display the image
        self.imageMatplotlib.axes.imshow(self.image, cmap=self.cmapColor, norm=norm)
        self.imageMatplotlib.draw()

    def strechHigh(self):
        # Create interval object
        interval = AsymmetricPercentileInterval(25, 99.5)
        vmin, vmax = interval.get_limits(self.image)
        # Create an ImageNormalize object using a LogStrech object
        norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=PowerStretch(1))
        # Display the image
        self.imageMatplotlib.axes.imshow(self.image, cmap=self.cmapColor, norm=norm)
        self.imageMatplotlib.draw()

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
            self.imageMatplotlib.axes.set_xlim(xmin=minx, xmax=maxx)
            self.imageMatplotlib.axes.set_ylim(ymin=miny, ymax=maxy)
            self.imageMatplotlib.draw()

    def zoom50(self):
        if self.sizeX:
            minx = int(self.sizeX / 4)
            maxx = minx + int(self.sizeX / 2)
            miny = int(self.sizeY / 4)
            maxy = miny + int(self.sizeY / 2)
            self.imageMatplotlib.axes.set_xlim(xmin=minx, xmax=maxx)
            self.imageMatplotlib.axes.set_ylim(ymin=miny, ymax=maxy)
            self.imageMatplotlib.draw()

    def zoom100(self):
        if self.sizeX:
            minx = 0
            maxx = self.sizeX
            miny = 0
            maxy = self.sizeY
            self.imageMatplotlib.axes.set_xlim(xmin=minx, xmax=maxx)
            self.imageMatplotlib.axes.set_ylim(ymin=miny, ymax=maxy)
            self.imageMatplotlib.draw()

    def showFitsImage(self, filename):
        hdulist = pyfits.open(filename)
        self.image = hdulist[0].data
        self.sizeY, self.sizeX = self.image.shape
        self.setStrech()
        self.setZoom()

    def disableExposures(self):
        self.ui.btn_expose.setEnabled(False)
        self.ui.btn_startContExposures.setEnabled(False)
        self.ui.btn_stopContExposures.setEnabled(False)
        self.setWindowTitle('Image Window - Modeling running - No manual exposures possible')

    def enableExposures(self):
        self.ui.btn_expose.setEnabled(True)
        self.ui.btn_startContExposures.setEnabled(True)
        self.ui.btn_stopContExposures.setEnabled(True)
        self.setWindowTitle('Image Window')

    def crosshairOnOff(self):
        if self.ui.cross1.isVisible():
            self.ui.cross1.setVisible(False)
            self.ui.cross2.setVisible(False)
            self.ui.cross3.setVisible(False)
            self.ui.cross4.setVisible(False)
        else:
            self.ui.cross1.setVisible(True)
            self.ui.cross2.setVisible(True)
            self.ui.cross3.setVisible(True)
            self.ui.cross4.setVisible(True)

    def exposeOnce(self):
        # link to cam and check if available
        if 'CONNECTION' in self.app.workerImaging.data:
            if self.app.workerImaging.data['CONNECTION']['CONNECT'] == 'Off':
                return
        else:
            return
        # start prep imaging
        imageParams = dict()
        imageParams['Imagepath'] = ''
        imageParams['Exposure'] = self.app.ui.cameraExposure.value()
        imageParams['Directory'] = time.strftime('%Y-%m-%d', time.gmtime())
        imageParams['File'] = self.BASENAME + time.strftime('%H-%M-%S', time.gmtime()) + '.fit'
        self.app.workerImaging.imagingCommandQueue.put(imageParams)

        while imageParams['Imagepath'] == '':
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()

        self.imagePath = imageParams['Imagepath']
        self.showFitsImage(self.imagePath)
        self.ui.le_imageFile.setText(imageParams['Imagepath'])

    def solveOnce(self):
        if self.imagePath == '':
            return
        if not os.path.isfile(self.imagePath):
            return
        self.ui.le_RaJ2000.setText('')
        self.ui.le_DecJ2000.setText('')

        imageParams = dict()
        imageParams['Imagepath'] = self.imagePath
        fitsFileHandle = pyfits.open(imageParams['Imagepath'], mode='update')
        fitsHeader = fitsFileHandle[0].header
        imageParams['RaJ2000'] = self.transform.degStringToDecimal(fitsHeader['OBJCTRA'], ' ')
        imageParams['DecJ2000'] = self.transform.degStringToDecimal(fitsHeader['OBJCTDEC'], ' ')
        imageParams['ScaleHint'] = float(fitsHeader['PIXSCALE'])
        fitsFileHandle.close()

        self.app.workerAstrometry.astrometryCommandQueue.put(imageParams)
        while 'Solved' not in imageParams:
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        if imageParams['Solved']:
            self.ui.le_RaJ2000.setText(self.transform.decimalToDegree(imageParams['RaJ2000Solved'], False, False))
            self.ui.le_DecJ2000.setText(self.transform.decimalToDegree(imageParams['DecJ2000Solved'], True, False))
        else:
            self.ui.le_RaJ2000.setText('not solved')
            self.ui.le_DecJ2000.setText('not solved')
