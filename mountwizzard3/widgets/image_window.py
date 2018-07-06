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
import copy
import PyQt5
import astropy.io.fits as pyfits
from astropy.visualization import MinMaxInterval, ImageNormalize, AsymmetricPercentileInterval, PowerStretch
from matplotlib import use
from baseclasses import widget
from astrometry import transform
from gui import image_window_ui
use('Qt5Agg')


class WorkerSignals(PyQt5.QtCore.QObject):

    finished = PyQt5.QtCore.pyqtSignal()
    error = PyQt5.QtCore.pyqtSignal(object)
    result = PyQt5.QtCore.pyqtSignal(object)


class Worker(PyQt5.QtCore.QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @PyQt5.QtCore.pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            self.signals.error.emit(e)
            print(e)
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()


class ImagesWindow(widget.MwWidget):
    logger = logging.getLogger(__name__)
    BASENAME = 'exposure-'
    signalShowFitsImage = PyQt5.QtCore.pyqtSignal(str)
    signalSolveFitsImage = PyQt5.QtCore.pyqtSignal(str)
    signalSetRaSolved = PyQt5.QtCore.pyqtSignal(str)
    signalSetDecSolved = PyQt5.QtCore.pyqtSignal(str)
    signalSetAngleSolved = PyQt5.QtCore.pyqtSignal(str)
    signalSetManualEnable = PyQt5.QtCore.pyqtSignal(bool)
    signalDisplayImage = PyQt5.QtCore.pyqtSignal(object)

    def __init__(self, app):
        super(ImagesWindow, self).__init__()
        self.app = app
        self.showStatus = False
        self.cancel = False
        self.imagePath = ''
        self.imageReady = False
        self.solveReady = False
        self.transform = transform.Transform(self.app)
        self.ui = image_window_ui.Ui_ImageDialog()
        self.ui.setupUi(self)
        self.initUI()
        # allow sizing of the window
        self.setFixedSize(PyQt5.QtCore.QSize(16777215, 16777215))
        # set the minimum size
        self.setMinimumSize(791, 400)
        self.image = numpy.zeros([20, 20])
        self.ui.btn_strechLow.setChecked(True)
        self.ui.btn_size100.setChecked(True)
        self.ui.btn_colorGrey.setChecked(True)
        self.threadpool = PyQt5.QtCore.QThreadPool()

        # adding the matplotlib integration
        self.imageMatplotlib = widget.IntegrateMatplotlib(self.ui.image)
        # making background looking transparent
        self.imageMatplotlib.fig.patch.set_facecolor('none')
        background = self.imageMatplotlib.fig.canvas.parentWidget()
        background.setStyleSheet('background-color: transparent;')
        self.imageMatplotlib.axes = self.imageMatplotlib.fig.add_subplot(111)
        self.imageMatplotlib.axes.set_axis_off()
        self.imageMatplotlib.fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.99)

        self.imageMatplotlibMarker = widget.IntegrateMatplotlib(self.ui.imageMarker)
        # making background looking transparent
        self.imageMatplotlibMarker.fig.patch.set_facecolor('none')
        background = self.imageMatplotlibMarker.fig.canvas.parentWidget()
        background.setStyleSheet('background-color: transparent;')
        self.imageMatplotlibMarker.axes = self.imageMatplotlibMarker.fig.add_subplot(111)
        self.imageMatplotlibMarker.axes.set_axis_off()
        self.imageMatplotlibMarker.fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.99)

        # slots for gui elements
        self.ui.btn_expose.clicked.connect(self.exposeOnce)
        self.ui.btn_exposeCont.clicked.connect(self.exposeCont)
        self.ui.btn_solve.clicked.connect(self.solveOnce)
        self.ui.btn_colorGrey.clicked.connect(self.setColor)
        self.ui.btn_colorCool.clicked.connect(self.setColor)
        self.ui.btn_colorRainbow.clicked.connect(self.setColor)
        self.ui.btn_colorSpectral.clicked.connect(self.setColor)
        self.ui.btn_size12.clicked.connect(self.setZoom)
        self.ui.btn_size25.clicked.connect(self.setZoom)
        self.ui.btn_size50.clicked.connect(self.setZoom)
        self.ui.btn_size100.clicked.connect(self.setZoom)
        self.ui.btn_strechLow.clicked.connect(self.setStrech)
        self.ui.btn_strechMid.clicked.connect(self.setStrech)
        self.ui.btn_strechHigh.clicked.connect(self.setStrech)
        self.ui.btn_strechSuper.clicked.connect(self.setStrech)
        self.ui.btn_cancel.clicked.connect(self.cancelAction)
        self.ui.checkShowCrosshairs.stateChanged.connect(self.setCrosshairOnOff)

        # define the slots for signals
        self.signalShowFitsImage.connect(self.showFitsImage)
        self.signalSolveFitsImage.connect(self.solveFitsImage)
        self.signalSetRaSolved.connect(self.setRaSolved)
        self.signalSetDecSolved.connect(self.setDecSolved)
        self.signalSetAngleSolved.connect(self.setAngleSolved)
        self.ui.btn_loadFits.clicked.connect(self.loadFitsFileFrom)
        self.app.workerImaging.imageSaved.connect(self.setImageReady)
        self.app.workerAstrometry.imageDataDownloaded.connect(self.setSolveReady)
        self.signalSetManualEnable.connect(self.setManualEnable)
        self.signalDisplayImage.connect(self.displayImage)

    def resizeEvent(self, QResizeEvent):
        # allow message window to be resized in height
        self.ui.image.setGeometry(5, 125, self.width() - 10, self.height() - 125)
        self.ui.imageMarker.setGeometry(5, 125, self.width() - 10, self.height() - 125)
        # getting position of axis
        axesPos = self.imageMatplotlibMarker.axes.get_position()
        # and using it fo the other plot widgets to be identically same size and position
        self.imageMatplotlib.axes.set_position(axesPos)
        # size the header window as well
        self.ui.imageBackground.setGeometry(0, 0, self.width(), 126)

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
            if 'ImageWindowHeight' in self.app.config and 'ImageWindowWidth' in self.app.config:
                self.resize(self.app.config['ImageWindowWidth'], self.app.config['ImageWindowHeight'])
            if 'ImagePath' in self.app.config:
                self.imagePath = self.app.config['ImagePath']
                self.ui.le_imageFile.setText(os.path.basename(self.imagePath))
            if 'CheckShowCrosshairs' in self.app.config:
                self.ui.checkShowCrosshairs.setChecked(self.app.config['CheckShowCrosshairs'])
            if 'ColorCool' in self.app.config:
                self.ui.btn_colorCool.setChecked(self.app.config['ColorCool'])
            if 'ColorRainbow' in self.app.config:
                self.ui.btn_colorRainbow.setChecked(self.app.config['ColorRainbow'])
            if 'ColorSpectral' in self.app.config:
                self.ui.btn_colorSpectral.setChecked(self.app.config['ColorSpectral'])
            if 'ColorGrey' in self.app.config:
                self.ui.btn_colorGrey.setChecked(self.app.config['ColorGrey'])
            if 'Size12' in self.app.config:
                self.ui.btn_size12.setChecked(self.app.config['Size12'])
            if 'Size25' in self.app.config:
                self.ui.btn_size25.setChecked(self.app.config['Size25'])
            if 'Size50' in self.app.config:
                self.ui.btn_size50.setChecked(self.app.config['Size50'])
            if 'Size100' in self.app.config:
                self.ui.btn_size100.setChecked(self.app.config['Size100'])
            if 'StrechLow' in self.app.config:
                self.ui.btn_strechLow.setChecked(self.app.config['StrechLow'])
            if 'StrechMid' in self.app.config:
                self.ui.btn_strechMid.setChecked(self.app.config['StrechMid'])
            if 'StrechHigh' in self.app.config:
                self.ui.btn_strechHigh.setChecked(self.app.config['StrechHigh'])
            if 'StrechSuper' in self.app.config:
                self.ui.btn_strechSuper.setChecked(self.app.config['StrechSuper'])

        except Exception as e:
            self.logger.error('Item in config.cfg not be initialized for image window, error:{0}'.format(e))
        finally:
            pass
        self.setCrosshairOnOff()

    def storeConfig(self):
        self.app.config['ImagePopupWindowPositionX'] = self.pos().x()
        self.app.config['ImagePopupWindowPositionY'] = self.pos().y()
        self.app.config['ImagePopupWindowShowStatus'] = self.showStatus
        self.app.config['ColorCool'] = self.ui.btn_colorCool.isChecked()
        self.app.config['ColorRainbow'] = self.ui.btn_colorRainbow.isChecked()
        self.app.config['ColorSpectral'] = self.ui.btn_colorSpectral.isChecked()
        self.app.config['ColorGrey'] = self.ui.btn_colorGrey.isChecked()
        self.app.config['Size12'] = self.ui.btn_size12.isChecked()
        self.app.config['Size25'] = self.ui.btn_size25.isChecked()
        self.app.config['Size50'] = self.ui.btn_size50.isChecked()
        self.app.config['Size100'] = self.ui.btn_size100.isChecked()
        self.app.config['StrechLow'] = self.ui.btn_strechLow.isChecked()
        self.app.config['StrechMid'] = self.ui.btn_strechMid.isChecked()
        self.app.config['StrechHigh'] = self.ui.btn_strechHigh.isChecked()
        self.app.config['StrechSuper'] = self.ui.btn_strechSuper.isChecked()
        self.app.config['ImagePath'] = self.imagePath
        self.app.config['CheckShowCrosshairs'] = self.ui.checkShowCrosshairs.isChecked()
        self.app.config['ImageWindowHeight'] = self.height()
        self.app.config['ImageWindowWidth'] = self.width()

    def toggleWindow(self):
        self.showStatus = not self.showStatus
        if self.showStatus:
            self.showWindow()
        else:
            self.close()

    def showWindow(self):
        self.showStatus = True
        self.signalShowFitsImage.emit(self.imagePath)
        self.app.signalChangeStylesheet.emit(self.app.ui.btn_openImageWindow, 'running', 'true')
        self.setVisible(True)

    def closeEvent(self, closeEvent):
        super().closeEvent(closeEvent)
        self.app.signalChangeStylesheet.emit(self.app.ui.btn_openImageWindow, 'running', 'false')

    def cancelAction(self):
        self.cancel = True
        self.app.workerAstrometry.astrometryCancel.emit()
        self.app.workerImaging.imagingCancel.emit()

    def setRaSolved(self, text):
        self.ui.le_RaJ2000.setText(text)

    def setDecSolved(self, text):
        self.ui.le_DecJ2000.setText(text)

    def setAngleSolved(self, text):
        self.ui.le_AngleJ2000.setText(text)

    def setImageReady(self):
        self.imageReady = True

    def setSolveReady(self):
        self.solveReady = True

    def loadFitsFileFrom(self):
        value, ext = self.selectFile(self, 'Open FITS file', '/images', 'FITS files (*.fit*)', True)
        if value != '':
            self.signalShowFitsImage.emit(value + ext)
        else:
            self.logger.warning('No Fits file file selected')

    def drawMarkers(self):
        # fixed points and horizon plane
        self.ui.image.stackUnder(self.ui.imageMarker)
        self.imageMatplotlibMarker.axes.cla()
        self.imageMatplotlibMarker.axes.set_xlim(0, 400)
        self.imageMatplotlibMarker.axes.set_ylim(0, 400)
        self.imageMatplotlibMarker.axes.grid(True, color='#606060', ls='dotted')
        self.imageMatplotlibMarker.axes.spines['bottom'].set_color((0, 0, 0, 0))
        self.imageMatplotlibMarker.axes.spines['top'].set_color((0, 0, 0, 0))
        self.imageMatplotlibMarker.axes.spines['left'].set_color((0, 0, 0, 0))
        self.imageMatplotlibMarker.axes.spines['right'].set_color((0, 0, 0, 0))
        self.imageMatplotlibMarker.axes.set_facecolor((0, 0, 0, 0))
        self.imageMatplotlibMarker.axes.set_xticks(numpy.arange(20, 381, 40))
        self.imageMatplotlibMarker.axes.set_yticks(numpy.arange(20, 381, 40))
        self.imageMatplotlibMarker.axes.set_xticklabels([])
        self.imageMatplotlibMarker.axes.set_yticklabels([])
        self.imageMatplotlibMarker.axes.plot(200, 200, zorder=10, color='#606060', marker='o', markersize=25, markeredgewidth=2, fillstyle='none')
        self.imageMatplotlibMarker.axes.plot(200, 200, zorder=10, color='#606060', marker='o', markersize=10, markeredgewidth=1, fillstyle='none')
        self.imageMatplotlibMarker.fig.canvas.draw()

    @PyQt5.QtCore.pyqtSlot(str)
    def showFitsImage(self, filename):
        # fits file ahs to be there
        if not os.path.isfile(filename):
            return
        # image window has to be present
        if not self.showStatus:
            return
        self.signalSetRaSolved.emit('')
        self.signalSetDecSolved.emit('')
        self.signalSetAngleSolved.emit('')
        self.imagePath = filename
        self.ui.le_imageFile.setText(os.path.basename(self.imagePath))
        try:
            fitsFileHandle = pyfits.open(filename)
            error = False
        except Exception as e:
            error = True
            if fitsFileHandle:
                fitsFileHandle.close()
            self.logger.error('File {0} could not be loaded, error: {1}'.format(self.imagePath, e))
        finally:
            if error:
                return
        self.image = copy.copy(fitsFileHandle[0].data)
        fitsFileHandle.close()
        strechMode = self.getStrechMode()
        colorMode = self.getColorMode()
        zoomMode = self.getZoomMode()
        worker = Worker(self.calculateImage, self.image, strechMode, colorMode, zoomMode)
        worker.signals.result.connect(self.signalDisplayImage)
        self.threadpool.start(worker)

    @PyQt5.QtCore.pyqtSlot(object)
    def displayImage(self, result):
        image = result[0]
        color = result[1]
        norm = result[2]
        self.imageMatplotlib.axes.imshow(image, cmap=color, norm=norm)
        self.imageMatplotlib.fig.canvas.draw()
        self.drawMarkers()
        self.resizeEvent(0)

    @staticmethod
    def calculateImage(imageOrig, strechMode, colorMode, zoomMode):
        sizeX, sizeY = imageOrig.shape
        # calculate the cropping parameters
        if zoomMode == 12:
            minx = int(sizeX * 7 / 16)
            maxx = minx + int(sizeX / 8)
            miny = int(sizeY * 7 / 16)
            maxy = miny + int(sizeY / 8)
        elif zoomMode == 25:
            minx = int(sizeX * 3 / 8)
            maxx = minx + int(sizeX / 4)
            miny = int(sizeY * 3 / 8)
            maxy = miny + int(sizeY / 4)
        elif zoomMode == 50:
            minx = int(sizeX / 4)
            maxx = minx + int(sizeX / 2)
            miny = int(sizeY / 4)
            maxy = miny + int(sizeY / 2)
        else:
            minx = 0
            maxx = sizeX
            miny = 0
            maxy = sizeY
        # crop image
        image = imageOrig[minx:maxx, miny:maxy]
        # calculation the strech
        if strechMode == 'Low':
            interval = AsymmetricPercentileInterval(98, 99.998)
        elif strechMode == 'Mid':
            interval = AsymmetricPercentileInterval(25, 99.95)
        elif strechMode == 'High':
            interval = AsymmetricPercentileInterval(12, 99.9)
        else:
            interval = AsymmetricPercentileInterval(1, 99.8)
        vmin, vmax = interval.get_limits(image)
        # Create an ImageNormalize object using a LogStrech object
        norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=PowerStretch(1))
        result = (image, colorMode, norm)
        return result

    def setStrech(self):
        strechMode = self.getStrechMode()
        colorMode = self.getColorMode()
        zoomMode = self.getZoomMode()
        worker = Worker(self.calculateImage, self.image, strechMode, colorMode, zoomMode)
        worker.signals.result.connect(self.signalDisplayImage)
        self.threadpool.start(worker)

    def setColor(self):
        strechMode = self.getStrechMode()
        colorMode = self.getColorMode()
        zoomMode = self.getZoomMode()
        worker = Worker(self.calculateImage, self.image, strechMode, colorMode, zoomMode)
        worker.signals.result.connect(self.signalDisplayImage)
        self.threadpool.start(worker)

    def setZoom(self):
        strechMode = self.getStrechMode()
        colorMode = self.getColorMode()
        zoomMode = self.getZoomMode()
        worker = Worker(self.calculateImage, self.image, strechMode, colorMode, zoomMode)
        worker.signals.result.connect(self.signalDisplayImage)
        self.threadpool.start(worker)

    def getColorMode(self):
        if self.ui.btn_colorCool.isChecked():
            color = 'plasma'
        elif self.ui.btn_colorRainbow.isChecked():
            color = 'rainbow'
        elif self.ui.btn_colorSpectral.isChecked():
            color = 'nipy_spectral'
        else:
            color = 'gray'
        return color

    def getStrechMode(self):
        if self.ui.btn_strechLow.isChecked():
            strech = 'Low'
        elif self.ui.btn_strechMid.isChecked():
            strech = 'Mid'
        elif self.ui.btn_strechHigh.isChecked():
            strech = 'High'
        else:
            strech = 'Super'
        return strech

    def getZoomMode(self):
        if self.ui.btn_size12.isChecked():
            zoom = 12
        elif self.ui.btn_size25.isChecked():
            zoom = 25
        elif self.ui.btn_size50.isChecked():
            zoom = 50
        else:
            zoom = 100
        return zoom

    def setManualEnable(self, stat):
        self.ui.btn_expose.setEnabled(stat)
        self.ui.btn_solve.setEnabled(stat)
        self.ui.btn_cancel.setEnabled(stat)
        self.ui.btn_exposeCont.setEnabled(stat)
        self.ui.btn_loadFits.setEnabled(stat)
        if stat:
            self.setWindowTitle('Image Window')
        else:
            self.setWindowTitle('Image Window - Model Build Running - No manual exposures possible')

    def setCrosshairOnOff(self):
        if self.ui.checkShowCrosshairs.isChecked():
            self.ui.imageMarker.setVisible(True)
        else:
            self.ui.imageMarker.setVisible(False)

    @PyQt5.QtCore.pyqtSlot(str)
    def solveFitsImage(self, filename):
        self.imagePath = filename
        self.solveOnce()

    def exposeOnce(self):
        self.cancel = False
        # link to cam and check if available
        while not self.cancel:
            self.app.signalChangeStylesheet.emit(self.ui.btn_expose, 'running', True)
            if 'CONNECTION' in self.app.workerImaging.data:
                if self.app.workerImaging.data['CONNECTION']['CONNECT'] == 'Off':
                    break
            else:
                break
            # start prep imaging
            imageParams = dict()
            imageParams['Imagepath'] = ''
            imageParams['Exposure'] = self.app.ui.cameraExposure.value()
            imageParams['Directory'] = time.strftime('%Y-%m-%d', time.gmtime())
            imageParams['File'] = self.BASENAME + time.strftime('%H-%M-%S', time.gmtime()) + '.fit'
            self.app.messageQueue.put('#BWExposing Image: {0} for {1} seconds\n'.format(imageParams['File'], imageParams['Exposure']))
            self.imageReady = False
            self.app.workerImaging.imagingCommandQueue.put(imageParams)
            while not self.imageReady and not self.cancel:
                time.sleep(0.1)
                PyQt5.QtWidgets.QApplication.processEvents()
            if not os.path.isfile(imageParams['Imagepath']):
                self.app.messageQueue.put('#BWImaging failed\n')
                break
            self.signalShowFitsImage.emit(imageParams['Imagepath'])
            break
        self.app.signalChangeStylesheet.emit(self.ui.btn_expose, 'running', False)

    def solveOnce(self):
        self.cancel = False
        while not self.cancel:
            if self.imagePath == '':
                break
            if not os.path.isfile(self.imagePath):
                break
            self.app.signalChangeStylesheet.emit(self.ui.btn_solve, 'running', True)
            self.signalSetRaSolved.emit('')
            self.signalSetDecSolved.emit('')
            self.signalSetAngleSolved.emit('')
            imageParams = dict()
            imageParams['Imagepath'] = self.imagePath
            self.app.messageQueue.put('#BWSolving Image: {0}\n'.format(imageParams['Imagepath']))
            self.solveReady = False
            self.app.workerAstrometry.astrometryCommandQueue.put(imageParams)
            while not self.solveReady and not self.cancel:
                time.sleep(0.1)
                PyQt5.QtWidgets.QApplication.processEvents()
            if 'Solved' in imageParams:
                if imageParams['Solved']:
                    self.app.messageQueue.put('#BWSolving result: RA: {0}, DEC: {1}\n'.format(self.transform.decimalToDegree(imageParams['RaJ2000Solved'], False, False),
                                                                                              self.transform.decimalToDegree(imageParams['DecJ2000Solved'], True, False)))
                else:
                    self.app.messageQueue.put('#BWImage could not be solved: {0}\n'.format(imageParams['Message']))
            else:
                self.app.messageQueue.put('#BWSolve error\n')
            break
        self.app.signalChangeStylesheet.emit(self.ui.btn_solve, 'running', False)

    def exposeCont(self):
        self.cancel = False
        # link to cam and check if available
        while not self.cancel:
            self.app.signalChangeStylesheet.emit(self.ui.btn_exposeCont, 'running', True)
            if 'CONNECTION' in self.app.workerImaging.data:
                if self.app.workerImaging.data['CONNECTION']['CONNECT'] == 'Off':
                    break
            else:
                break
            # start prep imaging
            imageParams = dict()
            imageParams['Imagepath'] = ''
            imageParams['Exposure'] = self.app.ui.cameraExposure.value()
            imageParams['Directory'] = time.strftime('%Y-%m-%d', time.gmtime())
            imageParams['File'] = self.BASENAME + time.strftime('%H-%M-%S', time.gmtime()) + '.fit'
            self.app.messageQueue.put('#BWExposing Image: {0} for {1} seconds\n'.format(imageParams['File'], imageParams['Exposure']))
            self.imageReady = False
            self.app.workerImaging.imagingCommandQueue.put(imageParams)
            while not self.imageReady and not self.cancel:
                time.sleep(0.1)
                PyQt5.QtWidgets.QApplication.processEvents()
            if not os.path.isfile(imageParams['Imagepath']):
                self.app.messageQueue.put('#BWImaging failed\n')
                break
            self.signalShowFitsImage.emit(imageParams['Imagepath'])
        self.app.signalChangeStylesheet.emit(self.ui.btn_exposeCont, 'running', False)
