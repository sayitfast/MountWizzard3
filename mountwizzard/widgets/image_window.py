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
# Python  v3.6.4
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
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
from gui import image_window_ui
use('Qt5Agg')


class ImagesWindow(widget.MwWidget):
    logger = logging.getLogger(__name__)
    BASENAME = 'exposure-'
    signalShowFitsImage = PyQt5.QtCore.pyqtSignal(object)
    signalSetRaSolved = PyQt5.QtCore.pyqtSignal(str)
    signalSetDecSolved = PyQt5.QtCore.pyqtSignal(str)

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
        self.ui = image_window_ui.Ui_ImageDialog()
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
        self.ui.btn_colorGrey.clicked.connect(self.setColor)
        self.ui.btn_colorCool.clicked.connect(self.setColor)
        self.ui.btn_colorRainbow.clicked.connect(self.setColor)
        self.ui.btn_size25.clicked.connect(self.setZoom)
        self.ui.btn_size50.clicked.connect(self.setZoom)
        self.ui.btn_size100.clicked.connect(self.setZoom)
        self.ui.btn_strechLow.clicked.connect(self.setStrech)
        self.ui.btn_strechMid.clicked.connect(self.setStrech)
        self.ui.btn_strechHigh.clicked.connect(self.setStrech)
        self.ui.btn_cancel.clicked.connect(self.cancelAction)
        self.ui.checkShowCrosshairs.stateChanged.connect(self.setCrosshairOnOff)
        self.setVisible(False)
        self.ui.cross1.setVisible(False)
        self.ui.cross2.setVisible(False)
        self.ui.cross3.setVisible(False)
        self.ui.cross4.setVisible(False)
        # define the signals
        self.signalShowFitsImage.connect(self.showFitsImage)
        self.signalSetRaSolved.connect(self.setRaSolved)
        self.signalSetDecSolved.connect(self.setDecSolved)
        self.ui.btn_loadFits.clicked.connect(self.loadFitsFileFrom)

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
                self.ui.le_imageFile.setText(os.path.basename(self.imagePath))
                if os.path.isfile(self.imagePath):
                    self.showFitsImage(self.imagePath)
            if 'CheckShowCrosshairs' in self.app.config:
                self.ui.checkShowCrosshairs.setChecked(self.app.config['CheckShowCrosshairs'])

        except Exception as e:
            self.logger.error('Item in config.cfg not be initialized for image window, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['ImagePopupWindowPositionX'] = self.pos().x()
        self.app.config['ImagePopupWindowPositionY'] = self.pos().y()
        self.app.config['ImagePopupWindowShowStatus'] = self.showStatus
        self.app.config['ImagePath'] = self.imagePath
        self.app.config['CheckShowCrosshairs'] = self.ui.checkShowCrosshairs.isChecked()

    def showWindow(self):
        self.showStatus = True
        self.setVisible(True)
        self.show()

    def cancelAction(self):
        self.app.workerAstrometry.astrometryCancel.emit()
        self.app.workerImaging.imagingCancel.emit()

    def setRaSolved(self, text):
        self.ui.le_RaJ2000.setText(text)

    def setDecSolved(self, text):
        self.ui.le_DecJ2000.setText(text)

    def loadFitsFileFrom(self):
        value = self.selectFile(self, 'Open FITS file', '/images', 'FITS files (*.fit)', '.fit', True)
        if value != '':
            self.signalShowFitsImage.emit(value + '.fit')
        else:
            self.logger.warning('No Fits file file selected')

    def showFitsImage(self, filename):
        # fits file ahs to be there
        if not os.path.isfile(filename):
            return
        # image window has to be present
        if not self.showStatus:
            return
        self.signalSetRaSolved.emit('')
        self.signalSetDecSolved.emit('')
        self.imagePath = filename
        self.ui.le_imageFile.setText(os.path.basename(self.imagePath))
        hdulist = pyfits.open(filename)
        self.image = hdulist[0].data
        self.sizeY, self.sizeX = self.image.shape
        self.setStrech()
        self.setZoom()

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
        interval = AsymmetricPercentileInterval(98, 99.995)
        vmin, vmax = interval.get_limits(self.image)
        # Create an ImageNormalize object using a LogStrech object
        norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=PowerStretch(1))
        # Display the image
        self.imageMatplotlib.axes.imshow(self.image, cmap=self.cmapColor, norm=norm)
        self.imageMatplotlib.draw()

    def strechMid(self):
        # Create interval object
        interval = AsymmetricPercentileInterval(25, 99.995)
        vmin, vmax = interval.get_limits(self.image)
        # Create an ImageNormalize object using a LogStrech object
        norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=PowerStretch(1))
        # Display the image
        self.imageMatplotlib.axes.imshow(self.image, cmap=self.cmapColor, norm=norm)
        self.imageMatplotlib.draw()

    def strechHigh(self):
        # Create interval object
        interval = AsymmetricPercentileInterval(1, 99.995)
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

    def disableExposures(self):
        self.ui.btn_expose.setEnabled(False)
        #self.ui.btn_startContExposures.setEnabled(False)
        #self.ui.btn_stopContExposures.setEnabled(False)
        self.setWindowTitle('Image Window - Modeling running - No manual exposures possible')

    def enableExposures(self):
        self.ui.btn_expose.setEnabled(True)
        #self.ui.btn_startContExposures.setEnabled(True)
        #self.ui.btn_stopContExposures.setEnabled(True)
        self.setWindowTitle('Image Window')

    def setCrosshairOnOff(self):
        if self.ui.checkShowCrosshairs.isChecked():
            self.ui.cross1.setVisible(True)
            self.ui.cross2.setVisible(True)
            self.ui.cross3.setVisible(True)
            self.ui.cross4.setVisible(True)
        else:
            self.ui.cross1.setVisible(False)
            self.ui.cross2.setVisible(False)
            self.ui.cross3.setVisible(False)
            self.ui.cross4.setVisible(False)

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
        self.app.messageQueue.put('#BWExposing Image: {0} for {1} seconds\n'.format(imageParams['File'], imageParams['Exposure']))
        self.app.workerImaging.imagingCommandQueue.put(imageParams)
        while imageParams['Imagepath'] == '':
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        if not os.path.isfile(imageParams['Imagepath']):
            self.app.messageQueue.put('#BWImaging failed\n')
            return
        self.signalShowFitsImage.emit(imageParams['Imagepath'])

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
        if 'OBJCTRA' not in fitsHeader:
            fitsFileHandle.close()
            self.app.messageQueue.put('No coordinate in FITS file')
            return
        imageParams['RaJ2000'] = self.transform.degStringToDecimal(fitsHeader['OBJCTRA'], ' ')
        imageParams['DecJ2000'] = self.transform.degStringToDecimal(fitsHeader['OBJCTDEC'], ' ')
        if 'FOCALLEN' in fitsHeader and 'XPIXSZ' in fitsHeader:
            imageParams['ScaleHint'] = float(fitsHeader['XPIXSZ']) * 206.6 / float(fitsHeader['FOCALLEN'])
        elif 'FOCALLEN' in fitsHeader and 'PIXSIZE1' in fitsHeader:
            imageParams['ScaleHint'] = float(fitsHeader['PIXSIZE1']) * 206.6 / float(fitsHeader['FOCALLEN'])
        else:
            imageParams['ScaleHint'] = self.app.ui.pixelSize.value() * 206.6 / self.app.ui.focalLength.value()
        fitsHeader['PIXSCALE'] = str(imageParams['ScaleHint'])
        fitsFileHandle.flush()
        fitsFileHandle.close()
        self.app.messageQueue.put('#BWSolving Image: {0}\n'.format(imageParams['Imagepath']))
        self.app.workerAstrometry.astrometryCommandQueue.put(imageParams)
        while 'Solved' not in imageParams:
            time.sleep(0.1)
            PyQt5.QtWidgets.QApplication.processEvents()
        if imageParams['Solved']:
            self.app.messageQueue.put('#BWSolving result: RA: {0}, DEC: {1}\n'.format(self.transform.decimalToDegree(imageParams['RaJ2000Solved'], False, False),
                                                                                      self.transform.decimalToDegree(imageParams['DecJ2000Solved'], True, False)))
