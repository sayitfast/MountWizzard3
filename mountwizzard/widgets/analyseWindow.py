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
import math
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
        self.data = {}
        self.analyseView = 1

        self.analyse = analysedata.Analyse(self.app)
        self.ui = analyse_dialog_ui.Ui_AnalyseDialog()
        self.ui.setupUi(self)
        self.initUI()
        self.initConfig()

        self.analyseMatplotlib = widget.IntegrateMatplotlib(self.ui.analyse)
        self.analyseMatplotlib.fig.subplots_adjust(left=0.075, right=0.925, bottom=0.075, top=0.925)

        self.ui.btn_errorOverview.clicked.connect(self.showErrorOverview)
        self.ui.btn_errorTime.clicked.connect(self.showErrorTime)
        self.ui.btn_errorAzAlt.clicked.connect(self.showErrorAzAlt)

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
            if 'AnalyseView' in self.app.config:
                self.analyseView = self.app.config['AnalyseView']
        except Exception as e:
            self.logger.error('Item in config.cfg not be initialized for analyse window, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['AnalysePopupWindowPositionX'] = self.pos().x()
        self.app.config['AnalysePopupWindowPositionY'] = self.pos().y()
        self.app.config['AnalyseView'] = self.analyseView
        self.app.config['AnalysePopupWindowShowStatus'] = self.showStatus

    def showWindow(self):
        self.getData()
        self.setWindowTitle('Analyse:    ' + self.app.ui.le_analyseFileName.text())
        if self.analyseView == 1:
            self.showErrorOverview()
        elif self.analyseView == 2:
            self.showErrorTime()
        elif self.analyseView == 3:
            self.showErrorAzAlt()
        self.showStatus = True
        self.setVisible(True)
        self.show()

    def getData(self):
        filename = self.app.ui.le_analyseFileName.text()
        if filename == '':
            return False
        self.data = self.analyse.loadData(filename)
        return True

    def setStyle(self, axes):
        if 'bottom' in axes.spines:
            axes.spines['bottom'].set_color('#2090C0')
            axes.spines['top'].set_color('#2090C0')
            axes.spines['left'].set_color('#2090C0')
            axes.spines['right'].set_color('#2090C0')
        elif 'polar' in axes.spines:
            axes.spines['polar'].set_color('#2090C0')

        axes.tick_params(axis='y', colors='#2090C0', labelleft='on', labelsize=12)
        axes.grid(True, color='#404040')
        axes.set_facecolor((32 / 256, 32 / 256, 32 / 256))
        axes.tick_params(axis='x', colors='#2090C0', labelsize=12)

    def setFigure(self, projection=None):
        self.analyseMatplotlib.fig.clf()
        self.analyseMatplotlib.axes = self.analyseMatplotlib.fig.add_subplot(1, 1, 1, projection=projection)
        self.setStyle(self.analyseMatplotlib.axes)

    def showErrorOverview(self):
        if len(self.data) == 0:
            return
        self.analyseView = 1
        self.analyseMatplotlib.fig.clf()
        axe1 = self.analyseMatplotlib.fig.add_subplot(1, 2, 1)
        self.setStyle(axe1)
        axe2 = self.analyseMatplotlib.fig.add_subplot(1, 2, 2, polar=True)
        self.setStyle(axe2)

        axe1.set_title('Model error', color='white', fontweight='bold')
        axe1.set_ylabel('DEC error (arcsec)', color='#C0C0C0')
        axe1.set_xlabel('RA error (arcsec)', color='#C0C0C0')
        axe1.plot(self.data['RaError'], self.data['DecError'], color='#181818', zorder=-10)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe1.scatter(self.data['RaError'], self.data['DecError'], c=colors, s=30, zorder=10)
        x0, x1 = axe1.get_xlim()
        y0, y1 = axe1.get_ylim()
        axe1.set_aspect((x1 - x0) / (y1 - y0))

        axe2.set_title('Polar error plot\n ', color='white', fontweight='bold')
        axe2.set_xlabel('North = 0°', color='white', fontweight='bold')
        axe2.set_theta_zero_location('N')
        axe2.set_theta_direction(-1)
        axe2.set_yticks(range(0, 90, 10))
        yLabel = ['', '80', '', '60', '', '40', '', '20', '', '0']
        axe2.set_yticklabels(yLabel)
        azimuth = numpy.asarray(self.data['Azimuth'])
        altitude = numpy.asarray(self.data['Altitude'])
        cm = matplotlib.pyplot.cm.get_cmap('RdYlGn_r')
        colors = numpy.asarray(self.data['ModelError'])
        scaleErrorMax = max(colors)
        scaleErrorMin = min(colors)
        theta = azimuth / 180.0 * math.pi
        r = 90 - altitude
        scatter = axe2.scatter(theta, r, c=colors, vmin=scaleErrorMin, vmax=scaleErrorMax, cmap=cm, zorder=10)
        scatter.set_alpha(0.75)
        colorbar = self.analyseMatplotlib.fig.colorbar(scatter, pad=0.1)
        colorbar.set_label('Error [arcsec]', color='white')
        matplotlib.pyplot.setp(matplotlib.pyplot.getp(colorbar.ax.axes, 'yticklabels'), color='white')
        axe2.set_rmax(90)
        axe2.set_rmin(0)

        self.analyseMatplotlib.draw()

    def showErrorTime(self):
        if len(self.data) == 0:
            return
        self.analyseView = 2
        self.analyseMatplotlib.fig.clf()
        axe1 = self.analyseMatplotlib.fig.add_subplot(2, 1, 1)
        self.setStyle(axe1)
        axe2 = self.analyseMatplotlib.fig.add_subplot(2, 1, 2)
        self.setStyle(axe2)

        axe1.set_title('Model error over modeled stars', color='white', fontweight='bold')
        axe1.set_ylabel('DEC error (arcsec)', color='#C0C0C0')
        axe1.set_xlim(1, len(self.data['Index']))
        axe1.plot(self.data['Index'], self.data['DecError'], color='#181818', zorder=-10)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe1.scatter(self.data['Index'], self.data['DecError'], c=colors, s=30, zorder=10)

        axe2.set_xlabel('Number of modeled point', color='white', fontweight='bold')
        axe2.set_ylabel('RA error (arcsec)', color='#C0C0C0')
        axe2.set_xlim(1, len(self.data['Index']))
        axe2.plot(self.data['Index'], self.data['RaError'], color='#181818', zorder=-10)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe2.scatter(self.data['Index'], self.data['RaError'], c=colors, s=30, zorder=10)

        self.analyseMatplotlib.draw()

    def showErrorAzAlt(self):
        if len(self.data) == 0:
            return
        self.analyseView = 3

        self.analyseMatplotlib.fig.clf()
        axe1 = self.analyseMatplotlib.fig.add_subplot(2, 2, 1)
        self.setStyle(axe1)
        axe2 = self.analyseMatplotlib.fig.add_subplot(2, 2, 3)
        self.setStyle(axe2)
        axe3 = self.analyseMatplotlib.fig.add_subplot(2, 2, 2)
        self.setStyle(axe3)
        axe4 = self.analyseMatplotlib.fig.add_subplot(2, 2, 4)
        self.setStyle(axe4)

        axe1.set_title('Model error over Azimuth', color='white', fontweight='bold')
        axe1.set_ylabel('RA error (arcsec)', color='#C0C0C0')
        axe1.set_xlim(0, 360)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe1.scatter(self.data['Azimuth'], self.data['RaError'], marker='o', c=colors, s=30, zorder=10)

        axe2.set_ylabel('DEC error (arcsec)', color='#C0C0C0')
        axe2.set_xlabel('Azimuth', color='white', fontweight='bold')
        axe2.set_xlim(0, 360)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe2.scatter(self.data['Azimuth'], self.data['DecError'], marker='D', c=colors, s=30, zorder=10)

        axe3.set_title('Model error over Altitude', color='white', fontweight='bold')
        axe3.set_ylabel('RA error (arcsec)', color='#C0C0C0')
        axe3.set_xlim(0, 90)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe3.scatter(self.data['Altitude'], self.data['RaError'], marker='o', c=colors, s=30, zorder=10)
        axe4.set_xlabel('Altitude', color='white', fontweight='bold')
        axe4.set_ylabel('DEC error (arcsec)', color='#C0C0C0')
        axe4.set_xlim(0, 90)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe4.scatter(self.data['Altitude'], self.data['DecError'], marker='D', c=colors, s=30, zorder=10)

        self.analyseMatplotlib.draw()
