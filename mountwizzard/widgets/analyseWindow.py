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
import numpy
from analyse import analysedata
from baseclasses import widget
from gui import analyse_dialog_ui
# matplotlib
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib import pyplot as plt


# noinspection PyTypeChecker
def calculateTimeConstant(x_time, y_value):
    timeconstant = 0
    # print(x_time)
    # print(y_value)
    x = 0
    y = 0
    return timeconstant, x, y


# noinspection PyUnresolvedReferences
class AnalyseWindow(widget.MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(AnalyseWindow, self).__init__()
        self.app = app
        self.showStatus = False
        self.scaleRA = 10
        self.scaleDEC = 10
        self.scaleError = 10
        self.data = {}
        self.analyse = analysedata.Analyse(self.app)
        self.ui = analyse_dialog_ui.Ui_AnalyseDialog()
        self.ui.setupUi(self)
        self.initUI()
        self.ui.scalePlotDEC.valueChanged.connect(self.changedDECScale)
        self.ui.scalePlotRA.valueChanged.connect(self.changedRAScale)
        self.ui.scalePlotError.valueChanged.connect(self.changedPlotError)
        self.ui.btn_selectDecError.clicked.connect(self.showDecError)
        self.ui.btn_selectDecErrorDeviation.clicked.connect(self.showDecErrorDeviation)
        self.ui.btn_selectRaError.clicked.connect(self.showRaError)
        self.ui.btn_selectRaErrorDeviation.clicked.connect(self.showRaErrorDeviation)
        self.ui.btn_selectDecErrorAltitude.clicked.connect(self.showDecErrorAltitude)
        self.ui.btn_selectRaErrorAltitude.clicked.connect(self.showRaErrorAltitude)
        self.ui.btn_selectDecErrorAzimuth.clicked.connect(self.showDecErrorAzimuth)
        self.ui.btn_selectRaErrorAzimuth.clicked.connect(self.showRaErrorAzimuth)
        self.ui.btn_selectModelPointPolar.clicked.connect(self.showModelPointPolar)
        self.ui.btn_selectModelPointErrorPolar.clicked.connect(self.showModelPointErrorPolar)

        self.plotMatplotlib = widget.IntegrateMatplotlib(self.ui.plot)
        self.plotMatplotlib.axes = self.plotMatplotlib.fig.add_subplot(111)
        self.plotMatplotlib.axes.grid(True, color='white')
        self.plotMatplotlib.axes.set_facecolor((32/256, 32/256, 32/256))
        self.plotMatplotlib.axes.tick_params(axis='x', colors='white')
        self.plotMatplotlib.axes.tick_params(axis='y', colors='white')

        self.initConfig()
        # self.show()
        self.setVisible(False)

    def initConfig(self):
        try:
            if 'ScalePlotRA' in self.app.config:
                self.ui.scalePlotRA.setValue(self.app.config['ScalePlotRA'])
            if 'ScalePlotDEC' in self.app.config:
                self.ui.scalePlotDEC.setValue(self.app.config['ScalePlotDEC'])
            if 'ScalePlotError' in self.app.config:
                self.ui.scalePlotError.setValue(self.app.config['ScalePlotError'])
            if 'AnalysePopupWindowPositionX' in self.app.config:
                self.move(self.app.config['AnalysePopupWindowPositionX'], self.app.config['AnalysePopupWindowPositionY'])
            if 'AnalysePopupWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['AnalysePopupWindowShowStatus']
        except Exception as e:
            self.logger.error('Item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['AnalysePopupWindowPositionX'] = self.pos().x()
        self.app.config['AnalysePopupWindowPositionY'] = self.pos().y()
        self.app.config['AnalysePopupWindowShowStatus'] = self.showStatus
        self.app.config['ScalePlotRA'] = self.ui.scalePlotRA.value()
        self.app.config['ScalePlotDEC'] = self.ui.scalePlotDEC.value()
        self.app.config['ScalePlotError'] = self.ui.scalePlotError.value()

    def showWindow(self):
        self.getData()
        self.setWindowTitle('Analyse:    ' + self.app.ui.le_analyseFileName.text())
        self.showDecError()
        self.showStatus = True
        self.setVisible(True)
        self.show()

    def changedDECScale(self):
        if self.getData():
            self.showDecError()

    def changedRAScale(self):
        if self.getData():
            self.showRaError()

    def changedPlotError(self):
        if self.getData():
            self.showModelPointErrorPolar()

    def getData(self):
        filename = self.app.ui.le_analyseFileName.text()
        if filename == '':
            return False
        self.scaleRA = self.ui.scalePlotRA.value()
        self.scaleDEC = self.ui.scalePlotDEC.value()
        self.scaleError = self.ui.scalePlotError.value()
        self.data = self.analyse.loadData(filename)
        return True

    def setFigure(self, projection=None):
        self.plotMatplotlib.fig.clf()
        self.plotMatplotlib.axes = self.plotMatplotlib.fig.add_subplot(1, 1, 1, projection=projection)
        self.plotMatplotlib.axes.grid(True, color='gray')
        self.plotMatplotlib.axes.set_facecolor((32/256, 32/256, 32/256))
        self.plotMatplotlib.axes.tick_params(axis='x', colors='white')
        self.plotMatplotlib.axes.tick_params(axis='y', colors='white')

    def showDecError(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotMatplotlib.axes.set_xlabel('Number of Model Point', color='white')                                             # x axis
        self.plotMatplotlib.axes.set_ylabel('DEC Error (arcsec)', color='white')                                                # y axis
        self.plotMatplotlib.axes.set_title('DEC Error over Modeling\n ', color='white')                                         # title
        self.plotMatplotlib.axes.set_xlim(0, len(self.data['Index']))
        self.plotMatplotlib.axes.set_ylim(-self.scaleDEC, self.scaleDEC)                                                        # defining the scaling of the plot
        self.plotMatplotlib.axes.plot(self.data['Index'], self.data['DecError'], color='black')                                 # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.plotMatplotlib.axes.scatter(self.data['Index'], self.data['DecError'], c=colors, s=50)
        self.plotMatplotlib.draw()                                                                                              # put the plot in the widget

    def showDecErrorDeviation(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        # timeconstant, x, y = calculateTimeConstant(self.data['sidereal_time'], self.data['decError'])
        self.setFigure()
        self.plotMatplotlib.axes.set_xlabel('Number of Model Point', color='white')                                             # x axis
        self.plotMatplotlib.axes.set_ylabel('DEC Error(arcsec)', color='white')                                                 # y axis
        self.plotMatplotlib.axes.set_title('DEC Error referenced to 0 over Modeling\n ', color='white')                         # title
        self.plotMatplotlib.axes.set_xlim(0, len(self.data['Index']))
        self.plotMatplotlib.axes.set_ylim(-self.scaleDEC, self.scaleDEC)                                                        # defining the scaling of the plot
        decErrorDeviation = numpy.asarray(self.data['DecError'])
        self.plotMatplotlib.axes.plot(self.data['Index'], decErrorDeviation - decErrorDeviation[0], color='black')              # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.plotMatplotlib.axes.scatter(self.data['Index'], decErrorDeviation - decErrorDeviation[0], c=colors, s=50)
        self.plotMatplotlib.draw()                                                                                              # put the plot in the widget

    def showRaError(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotMatplotlib.axes.set_xlabel('Number of Model Point', color='white')
        self.plotMatplotlib.axes.set_ylabel('RA Error (arcsec)', color='white')
        self.plotMatplotlib.axes.set_title('RA Error over Modeling\n ', color='white')
        self.plotMatplotlib.axes.set_xlim(0, len(self.data['Index']))
        self.plotMatplotlib.axes.set_ylim(-self.scaleRA, self.scaleRA)
        self.plotMatplotlib.axes.plot(self.data['Index'], self.data['RaError'], color='black')                                   # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.plotMatplotlib.axes.scatter(self.data['Index'], self.data['RaError'], c=colors, s=50)
        self.plotMatplotlib.draw()

    def showRaErrorDeviation(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotMatplotlib.axes.set_xlabel('Number of Model Point', color='white')
        self.plotMatplotlib.axes.set_ylabel('RA Error', color='white')
        self.plotMatplotlib.axes.set_title('RA Error referenced to 0 over Modeling\n ', color='white')
        self.plotMatplotlib.axes.axis([0, len(self.data['Index']), -self.scaleRA, self.scaleRA])
        raErrorDeviation = numpy.asarray(self.data['RaError'])
        self.plotMatplotlib.axes.plot(self.data['Index'], raErrorDeviation - raErrorDeviation[0], color='black')                 # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.plotMatplotlib.axes.scatter(self.data['Index'], raErrorDeviation - raErrorDeviation[0], c=colors, s=50)
        self.plotMatplotlib.draw()

    def showDecErrorAltitude(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotMatplotlib.axes.set_xlabel('Altitude', color='white')
        self.plotMatplotlib.axes.set_ylabel('DEC Error (arcsec)', color='white')
        self.plotMatplotlib.axes.set_title('DEC Error over Altitude\n ', color='white')
        self.plotMatplotlib.axes.set_xlim(0, 90)
        self.plotMatplotlib.axes.set_ylim(-self.scaleDEC, self.scaleDEC)
        self.plotMatplotlib.axes.plot(self.data['Altitude'], self.data['DecError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.plotMatplotlib.axes.scatter(self.data['Altitude'], self.data['DecError'], c=colors, s=50)
        self.plotMatplotlib.draw()

    def showRaErrorAltitude(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotMatplotlib.axes.set_xlabel('Altitude', color='white')
        self.plotMatplotlib.axes.set_ylabel('RA Error (arcsec)', color='white')
        self.plotMatplotlib.axes.set_title('RA Error over Altitude\n ', color='white')
        self.plotMatplotlib.axes.set_xlim(0, 90)
        self.plotMatplotlib.axes.set_ylim(-self.scaleRA, self.scaleRA)
        self.plotMatplotlib.axes.plot(self.data['Altitude'], self.data['RaError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.plotMatplotlib.axes.scatter(self.data['Altitude'], self.data['RaError'], c=colors, s=50)
        self.plotMatplotlib.draw()

    def showDecErrorAzimuth(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotMatplotlib.axes.set_xlabel('Altitude', color='white')
        self.plotMatplotlib.axes.set_ylabel('DEC Error (arcsec)', color='white')
        self.plotMatplotlib.axes.set_title('DEC Error over Azimuth\n ', color='white')
        self.plotMatplotlib.axes.set_xlim(0, 360)
        self.plotMatplotlib.axes.set_ylim(-self.scaleDEC, self.scaleDEC)
        self.plotMatplotlib.axes.plot(self.data['Azimuth'], self.data['DecError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.plotMatplotlib.axes.scatter(self.data['Azimuth'], self.data['DecError'], c=colors, s=50)
        self.plotMatplotlib.draw()

    def showRaErrorAzimuth(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotMatplotlib.axes.set_xlabel('Altitude', color='white')
        self.plotMatplotlib.axes.set_ylabel('RA Error (arcsec)', color='white')
        self.plotMatplotlib.axes.set_title('RA Error over Azimuth\n ', color='white')
        self.plotMatplotlib.axes.set_xlim(0, 360)
        self.plotMatplotlib.axes.set_ylim(-self.scaleRA, self.scaleRA)
        self.plotMatplotlib.axes.plot(self.data['Azimuth'], self.data['RaError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.plotMatplotlib.axes.scatter(self.data['Azimuth'], self.data['RaError'], c=colors, s=50)
        self.plotMatplotlib.draw()

    def showModelPointPolar(self):
        self.setFigure('polar')
        self.plotMatplotlib.axes.set_theta_zero_location('N')
        self.plotMatplotlib.axes.set_theta_direction(-1)
        self.plotMatplotlib.axes.set_yticks(range(0, 90, 10))
        yLabel = ['', '80', '', '60', '', '40', '', '20', '', '0']
        self.plotMatplotlib.axes.set_yticklabels(yLabel, color='white')
        self.plotMatplotlib.axes.set_title('Model Points\n ', color='white')
        azimuth = numpy.asarray(self.data['Azimuth'])
        altitude = numpy.asarray(self.data['Altitude'])
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.plotMatplotlib.axes.plot(azimuth / 180.0 * 3.141593, 90 - altitude, color='black')
        self.plotMatplotlib.axes.scatter(azimuth / 180.0 * 3.141593, 90 - altitude, c=colors, s=50)
        self.plotMatplotlib.axes.set_rmax(90)
        self.plotMatplotlib.axes.set_rmin(0)
        self.plotMatplotlib.draw()

    def showModelPointErrorPolar(self):
        self.setFigure('polar')
        self.plotMatplotlib.axes.set_theta_zero_location('N')
        self.plotMatplotlib.axes.set_theta_direction(-1)
        self.plotMatplotlib.axes.set_yticks(range(0, 90, 10))
        yLabel = ['', '80', '', '60', '', '40', '', '20', '', '0']
        self.plotMatplotlib.axes.set_yticklabels(yLabel, color='white')
        self.plotMatplotlib.axes.set_title('Model Points Error\n ', color='white')
        azimuth = numpy.asarray(self.data['Azimuth'])
        altitude = numpy.asarray(self.data['Altitude'])
        self.plotMatplotlib.axes.plot(azimuth / 180.0 * 3.141593, 90 - altitude, color='black')
        cm = plt.cm.get_cmap('RdYlGn_r')
        colors = numpy.asarray(self.data['ModelError'])
        scaleError = int(max(colors) / 4 + 1) * 4
        area = colors * 100 / self.scaleError + 20
        theta = azimuth / 180.0 * 3.141593
        r = 90 - altitude
        scatter = self.plotMatplotlib.axes.scatter(theta, r, c=colors, vmin=0, vmax=scaleError, s=area, cmap=cm)
        scatter.set_alpha(0.75)
        colorbar = self.plotMatplotlib.fig.colorbar(scatter)
        colorbar.set_label('Error [arcsec]', color='white')
        plt.setp(plt.getp(colorbar.ax.axes, 'yticklabels'), color='white')
        self.plotMatplotlib.axes.set_rmax(90)
        self.plotMatplotlib.axes.set_rmin(0)
        self.plotMatplotlib.draw()
