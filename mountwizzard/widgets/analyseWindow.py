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
import numpy
from analyse import analysedata
from baseclasses import widget
from gui import analyse_dialog_ui
# matplotlib
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib import pyplot as plt


class AnalyseWindow(widget.MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(AnalyseWindow, self).__init__()
        self.app = app
        self.scaleRA = 10
        self.scaleDEC = 10
        self.scaleError = 10
        self.data = {}
        self.analyse = analysedata.Analyse(self.app)
        self.ui = analyse_dialog_ui.Ui_AnalyseDialog()
        self.ui.setupUi(self)
        self.initUI()
        self.initConfig()

        self.analyseMatplotlib = widget.IntegrateMatplotlib(self.ui.analyse)
        self.analyseMatplotlib.axes = self.analyseMatplotlib.fig.add_subplot(111)
        self.analyseMatplotlib.fig.subplots_adjust(left=0.075, right=0.925, bottom=0.075, top=0.925)

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

        self.setVisible(False)
        self.showStatus = False

    def initConfig(self):
        try:
            if 'AnalysePopupWindowPositionX' in self.app.config:
                x = self.app.config['AnalysePopupWindowPositionX']
                y = self.app.config['AnalysePopupWindowPositionY']
                if x > self.screenSizeX:
                    x = 0
                if y > self.screenSizeY:
                    y = 0
                self.move(x, y)
            if 'AnalysePopupWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['AnalysePopupWindowShowStatus']
        except Exception as e:
            self.logger.error('Item in config.cfg not be initialized for analyse window, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['AnalysePopupWindowPositionX'] = self.pos().x()
        self.app.config['AnalysePopupWindowPositionY'] = self.pos().y()
        self.app.config['AnalysePopupWindowShowStatus'] = self.showStatus

    def showWindow(self):
        self.getData()
        self.setWindowTitle('Analyse:    ' + self.app.ui.le_analyseFileName.text())
        self.showDecError()
        self.showStatus = True
        self.setVisible(True)
        self.show()

    def getData(self):
        filename = self.app.ui.le_analyseFileName.text()
        if filename == '':
            return False
        self.data = self.analyse.loadData(filename)
        return True

    def setFigure(self, projection=None):
        self.analyseMatplotlib.fig.clf()
        self.analyseMatplotlib.axes = self.analyseMatplotlib.fig.add_subplot(1, 1, 1, projection=projection)
        if 'bottom' in self.analyseMatplotlib.axes.spines:
            self.analyseMatplotlib.axes.spines['bottom'].set_color('#2090C0')
            self.analyseMatplotlib.axes.spines['top'].set_color('#2090C0')
            self.analyseMatplotlib.axes.spines['left'].set_color('#2090C0')
            self.analyseMatplotlib.axes.spines['right'].set_color('#2090C0')
        self.analyseMatplotlib.axes.grid(True, color='#404040')
        self.analyseMatplotlib.axes.set_facecolor((32 / 256, 32 / 256, 32 / 256))
        self.analyseMatplotlib.axes.tick_params(axis='x', colors='#2090C0', labelsize=12)
        self.analyseMatplotlib.axes.tick_params(axis='y', colors='#2090C0', which='both', labelleft='on', labelright='on', labelsize=12)

    def showDecError(self):
        if len(self.data) == 0:
            return
        self.setFigure()
        self.analyseMatplotlib.axes.set_xlabel('Number of Model Point', color='white')                                             # x axis
        self.analyseMatplotlib.axes.set_ylabel('DEC Error (arcsec)', color='white')                                                # y axis
        self.analyseMatplotlib.axes.set_title('DEC Error over Modeling\n ', color='white')                                         # title
        self.analyseMatplotlib.axes.set_xlim(0, len(self.data['Index']))
        self.analyseMatplotlib.axes.plot(self.data['Index'], self.data['DecError'], color='black')                                 # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.analyseMatplotlib.axes.scatter(self.data['Index'], self.data['DecError'], c=colors, s=50)
        self.analyseMatplotlib.draw()                                                                                              # put the plot in the widget

    def showDecErrorDeviation(self):
        if len(self.data) == 0:
            return
        # timeconstant, x, y = calculateTimeConstant(self.data['sidereal_time'], self.data['decError'])
        self.setFigure()
        self.analyseMatplotlib.axes.set_xlabel('Number of Model Point', color='white')                                             # x axis
        self.analyseMatplotlib.axes.set_ylabel('DEC Error(arcsec)', color='white')                                                 # y axis
        self.analyseMatplotlib.axes.set_title('DEC Error referenced to 0 over Modeling\n ', color='white')                         # title
        self.analyseMatplotlib.axes.set_xlim(0, len(self.data['Index']))
        decErrorDeviation = numpy.asarray(self.data['DecError'])
        self.analyseMatplotlib.axes.plot(self.data['Index'], decErrorDeviation - decErrorDeviation[0], color='black')              # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.analyseMatplotlib.axes.scatter(self.data['Index'], decErrorDeviation - decErrorDeviation[0], c=colors, s=50)
        self.analyseMatplotlib.draw()                                                                                              # put the plot in the widget

    def showRaError(self):
        if len(self.data) == 0:
            return
        self.setFigure()
        self.analyseMatplotlib.axes.set_xlabel('Number of Model Point', color='white')
        self.analyseMatplotlib.axes.set_ylabel('RA Error (arcsec)', color='white')
        self.analyseMatplotlib.axes.set_title('RA Error over Modeling\n ', color='white')
        self.analyseMatplotlib.axes.set_xlim(0, len(self.data['Index']))
        self.analyseMatplotlib.axes.plot(self.data['Index'], self.data['RaError'], color='black')                                   # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.analyseMatplotlib.axes.scatter(self.data['Index'], self.data['RaError'], c=colors, s=50)
        self.analyseMatplotlib.draw()

    def showRaErrorDeviation(self):
        if len(self.data) == 0:
            return
        self.setFigure()
        self.analyseMatplotlib.axes.set_xlabel('Number of Model Point', color='white')
        self.analyseMatplotlib.axes.set_ylabel('RA Error', color='white')
        self.analyseMatplotlib.axes.set_title('RA Error referenced to 0 over Modeling\n ', color='white')
        self.analyseMatplotlib.axes.axis([0, len(self.data['Index']), -self.scaleRA, self.scaleRA])
        raErrorDeviation = numpy.asarray(self.data['RaError'])
        self.analyseMatplotlib.axes.plot(self.data['Index'], raErrorDeviation - raErrorDeviation[0], color='black')                 # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.analyseMatplotlib.axes.scatter(self.data['Index'], raErrorDeviation - raErrorDeviation[0], c=colors, s=50)
        self.analyseMatplotlib.draw()

    def showDecErrorAltitude(self):
        if len(self.data) == 0:
            return
        self.setFigure()
        self.analyseMatplotlib.axes.set_xlabel('Altitude', color='white')
        self.analyseMatplotlib.axes.set_ylabel('DEC Error (arcsec)', color='white')
        self.analyseMatplotlib.axes.set_title('DEC Error over Altitude\n ', color='white')
        self.analyseMatplotlib.axes.set_xlim(0, 90)
        self.analyseMatplotlib.axes.plot(self.data['Altitude'], self.data['DecError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.analyseMatplotlib.axes.scatter(self.data['Altitude'], self.data['DecError'], c=colors, s=50)
        self.analyseMatplotlib.draw()

    def showRaErrorAltitude(self):
        if len(self.data) == 0:
            return
        self.setFigure()
        self.analyseMatplotlib.axes.set_xlabel('Altitude', color='white')
        self.analyseMatplotlib.axes.set_ylabel('RA Error (arcsec)', color='white')
        self.analyseMatplotlib.axes.set_title('RA Error over Altitude\n ', color='white')
        self.analyseMatplotlib.axes.set_xlim(0, 90)
        self.analyseMatplotlib.axes.plot(self.data['Altitude'], self.data['RaError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.analyseMatplotlib.axes.scatter(self.data['Altitude'], self.data['RaError'], c=colors, s=50)
        self.analyseMatplotlib.draw()

    def showDecErrorAzimuth(self):
        if len(self.data) == 0:
            return
        self.setFigure()
        self.analyseMatplotlib.axes.set_xlabel('Altitude', color='white')
        self.analyseMatplotlib.axes.set_ylabel('DEC Error (arcsec)', color='white')
        self.analyseMatplotlib.axes.set_title('DEC Error over Azimuth\n ', color='white')
        self.analyseMatplotlib.axes.set_xlim(0, 360)
        self.analyseMatplotlib.axes.plot(self.data['Azimuth'], self.data['DecError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.analyseMatplotlib.axes.scatter(self.data['Azimuth'], self.data['DecError'], c=colors, s=50)
        self.analyseMatplotlib.draw()

    def showRaErrorAzimuth(self):
        if len(self.data) == 0:
            return
        self.setFigure()
        self.analyseMatplotlib.axes.set_xlabel('Altitude', color='white')
        self.analyseMatplotlib.axes.set_ylabel('RA Error (arcsec)', color='white')
        self.analyseMatplotlib.axes.set_title('RA Error over Azimuth\n ', color='white')
        self.analyseMatplotlib.axes.set_xlim(0, 360)
        self.analyseMatplotlib.axes.plot(self.data['Azimuth'], self.data['RaError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.analyseMatplotlib.axes.scatter(self.data['Azimuth'], self.data['RaError'], c=colors, s=50)
        self.analyseMatplotlib.draw()

    def showModelPointPolar(self):
        self.setFigure('polar')
        self.analyseMatplotlib.axes.set_theta_zero_location('N')
        self.analyseMatplotlib.axes.set_theta_direction(-1)
        self.analyseMatplotlib.axes.set_yticks(range(0, 90, 10))
        yLabel = ['', '80', '', '60', '', '40', '', '20', '', '0']
        self.analyseMatplotlib.axes.set_yticklabels(yLabel, color='white')
        self.analyseMatplotlib.axes.set_title('Model Points\n ', color='white')
        azimuth = numpy.asarray(self.data['Azimuth'])
        altitude = numpy.asarray(self.data['Altitude'])
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        self.analyseMatplotlib.axes.plot(azimuth / 180.0 * 3.141593, 90 - altitude, color='black')
        self.analyseMatplotlib.axes.scatter(azimuth / 180.0 * 3.141593, 90 - altitude, c=colors, s=50)
        self.analyseMatplotlib.axes.set_rmax(90)
        self.analyseMatplotlib.axes.set_rmin(0)
        self.analyseMatplotlib.draw()

    def showModelPointErrorPolar(self):
        self.setFigure('polar')
        self.analyseMatplotlib.axes.set_theta_zero_location('N')
        self.analyseMatplotlib.axes.set_theta_direction(-1)
        self.analyseMatplotlib.axes.set_yticks(range(0, 90, 10))
        yLabel = ['', '80', '', '60', '', '40', '', '20', '', '0']
        self.analyseMatplotlib.axes.set_yticklabels(yLabel, color='white')
        self.analyseMatplotlib.axes.set_title('Model Points Error\n ', color='white')
        azimuth = numpy.asarray(self.data['Azimuth'])
        altitude = numpy.asarray(self.data['Altitude'])
        self.analyseMatplotlib.axes.plot(azimuth / 180.0 * 3.141593, 90 - altitude, color='black')
        cm = plt.cm.get_cmap('RdYlGn_r')
        colors = numpy.asarray(self.data['ModelError'])
        scaleError = int(max(colors) / 4 + 1) * 4
        area = colors * 100 / self.scaleError + 20
        theta = azimuth / 180.0 * 3.141593
        r = 90 - altitude
        scatter = self.analyseMatplotlib.axes.scatter(theta, r, c=colors, vmin=0, vmax=scaleError, s=area, cmap=cm)
        scatter.set_alpha(0.75)
        colorbar = self.analyseMatplotlib.fig.colorbar(scatter)
        colorbar.set_label('Error [arcsec]', color='white')
        plt.setp(plt.getp(colorbar.ax.axes, 'yticklabels'), color='white')
        self.analyseMatplotlib.axes.set_rmax(90)
        self.analyseMatplotlib.axes.set_rmin(0)
        self.analyseMatplotlib.draw()
