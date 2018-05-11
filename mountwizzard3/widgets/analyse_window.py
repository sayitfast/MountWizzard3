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
# Python  v3.6.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
import logging
import math
import numpy
import PyQt5
from analyse import analysedata
from baseclasses import widget
from gui import analyse_window_ui
import matplotlib
matplotlib.use('Qt5Agg')


class AnalyseWindow(widget.MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(AnalyseWindow, self).__init__()
        self.app = app
        self.data = {}
        self.analyseView = 1

        self.analyse = analysedata.Analyse(self.app)
        self.ui = analyse_window_ui.Ui_AnalyseDialog()
        self.ui.setupUi(self)
        self.initUI()
        # allow sizing of the window
        self.setFixedSize(PyQt5.QtCore.QSize(16777215, 16777215))
        # set the minimum size
        self.setMinimumSize(791, 400)

        self.analyseMatplotlib = widget.IntegrateMatplotlib(self.ui.analyse)
        self.analyseMatplotlib.fig.set_tight_layout((0.075, 0.075, 0.925, 0.925))

        self.ui.btn_errorOverview.clicked.connect(self.showErrorOverview)
        self.ui.btn_errorTime.clicked.connect(self.showErrorTime)
        self.ui.btn_errorAzAlt.clicked.connect(self.showErrorAzAlt)
        self.ui.checkWinsorize.stateChanged.connect(self.showView)
        self.ui.checkOptimized.stateChanged.connect(self.showView)
        self.ui.winsorizeLimit.valueChanged.connect(self.showView)

        self.setVisible(False)
        self.showStatus = False

    def resizeEvent(self, QResizeEvent):
        # allow message window to be resized in height
        self.ui.analyse.setGeometry(5, 125, self.width() - 10, self.height() - 125)
        # using tight layout because of the axis titles and labels
        self.analyseMatplotlib.fig.set_tight_layout((0.075, 0.075, 0.925, 0.925))
        # size the header window as well
        self.ui.analyseBackground.setGeometry(0, 0, self.width(), 126)

    @staticmethod
    def winsorize(value, limits=None, inclusive=(True, True), inplace=False, axis=None):
        '''
        Copyright (c) 2001, 2002 Enthought, Inc.
        All rights reserved.

        Copyright (c) 2003-2012 SciPy Developers.
        All rights reserved.

        Redistribution and use in source and binary forms, with or without
        modification, are permitted provided that the following conditions are met:

          a. Redistributions of source code must retain the above copyright notice,
             this list of conditions and the following disclaimer.
          b. Redistributions in binary form must reproduce the above copyright
             notice, this list of conditions and the following disclaimer in the
             documentation and/or other materials provided with the distribution.
          c. Neither the name of Enthought nor the names of the SciPy Developers
             may be used to endorse or promote products derived from this software
             without specific prior written permission.


        THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
        AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
        IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
        ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS
        BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
        OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
        SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
        INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
        CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
        ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
        THE POSSIBILITY OF SUCH DAMAGE.
        '''
        def _winsorize1D(a, low_limit, up_limit, low_include, up_include):
            n = a.count()
            idx = a.argsort()
            if low_limit:
                if low_include:
                    lowidx = int(low_limit * n)
                else:
                    lowidx = numpy.round(low_limit * n)
                a[idx[:lowidx]] = a[idx[lowidx]]
            if up_limit is not None:
                if up_include:
                    upidx = n - int(n * up_limit)
                else:
                    upidx = n - numpy.round(n * up_limit)
                a[idx[upidx:]] = a[idx[upidx - 1]]
            return a
        a = numpy.ma.array(value, copy=numpy.logical_not(inplace))
        if limits is None:
            return a
        if (not isinstance(limits, tuple)) and isinstance(limits, float):
            limits = (limits, limits)
        # Check the limits
        (lolim, uplim) = limits
        if lolim is not None:
            if lolim > 1. or lolim < 0:
                raise ValueError(errmsg % 'beginning' + "(got %s)" % lolim)
        if uplim is not None:
            if uplim > 1. or uplim < 0:
                raise ValueError(errmsg % 'end' + "(got %s)" % uplim)
        (loinc, upinc) = inclusive
        if axis is None:
            shp = a.shape
            return _winsorize1D(a.ravel(), lolim, uplim, loinc, upinc).reshape(shp)
        else:
            return ma.apply_along_axis(_winsorize1D, axis, a, lolim, uplim, loinc, upinc)

    def initConfig(self):
        try:
            if 'AnalyseWindowPositionX' in self.app.config:
                x = self.app.config['AnalyseWindowPositionX']
                y = self.app.config['AnalyseWindowPositionY']
                if x > self.screenSizeX:
                    x = 0
                if y > self.screenSizeY:
                    y = 0
                self.move(x, y)
            if 'AnalyseWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['AnalyseWindowShowStatus']
            if 'AnalyseView' in self.app.config:
                self.analyseView = self.app.config['AnalyseView']
            if 'CheckWinsorized' in self.app.config:
                self.ui.checkWinsorize.setChecked(self.app.config['CheckWinsorized'])
            if 'CheckOptimized' in self.app.config:
                self.ui.checkOptimized.setChecked(self.app.config['CheckOptimized'])
            if 'WinsorizedLimit' in self.app.config:
                self.ui.winsorizeLimit.setValue(self.app.config['WinsorizedLimit'])
            if 'AnalyseWindowHeight' in self.app.config and 'AnalyseWindowWidth' in self.app.config:
                self.resize(self.app.config['AnalyseWindowWidth'], self.app.config['AnalyseWindowHeight'])

        except Exception as e:
            self.logger.error('Item in config.cfg not be initialized for analyse window, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['AnalyseWindowPositionX'] = self.pos().x()
        self.app.config['AnalyseWindowPositionY'] = self.pos().y()
        self.app.config['AnalyseView'] = self.analyseView
        self.app.config['AnalyseWindowShowStatus'] = self.showStatus
        self.app.config['CheckWinsorized'] = self.ui.checkWinsorize.isChecked()
        self.app.config['CheckOptimized'] = self.ui.checkOptimized.isChecked()
        self.app.config['WinsorizedLimit'] = self.ui.winsorizeLimit.value()
        self.app.config['AnalyseWindowHeight'] = self.height()
        self.app.config['AnalyseWindowWidth'] = self.width()

    def showWindow(self):
        self.getData()
        self.setWindowTitle('Analyse:    ' + self.app.ui.le_analyseFileName.text())
        self.showStatus = True
        self.setVisible(True)
        self.showView()
        self.show()

    def showView(self):
        if self.analyseView == 1:
            self.showErrorOverview()
        elif self.analyseView == 2:
            self.showErrorTime()
        elif self.analyseView == 3:
            self.showErrorAzAlt()

    def getData(self):
        filename = self.app.ui.le_analyseFileName.text()
        if filename == '':
            return False
        self.data = self.analyse.loadData(filename)
        return True

    @staticmethod
    def setStyle(axes):
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

        if self.ui.checkOptimized.isChecked() and 'DecErrorOptimized' in self.data:
            valueY1 = self.data['DecErrorOptimized']
            valueY2 = self.data['RaErrorOptimized']
            valueY3 = self.data['ModelErrorOptimized']
        else:
            valueY1 = self.data['DecError']
            valueY2 = self.data['RaError']
            valueY3 = self.data['ModelError']

        if self.ui.checkWinsorize.isChecked():
            limit = float(self.ui.winsorizeLimit.text()) / 100.0
            valueY1 = self.winsorize(valueY1, limits=limit)
            valueY2 = self.winsorize(valueY2, limits=limit)
            valueY3 = self.winsorize(valueY3, limits=limit)

        axe1.set_title('Model error', color='white', fontweight='bold')
        axe1.set_ylabel('DEC error (arcsec)', color='#C0C0C0')
        axe1.yaxis.set_label_position('right')
        axe1.set_xlabel('RA error (arcsec)', color='#C0C0C0')
        axe1.plot(valueY2, valueY1, color='#181818', zorder=-10)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe1.scatter(valueY2, valueY1, c=colors, s=30, zorder=10)
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
        colors = numpy.asarray(valueY3)
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

        if self.ui.checkOptimized.isChecked() and 'DecErrorOptimized' in self.data:
            valueY1 = self.data['DecErrorOptimized']
            valueY2 = self.data['RaErrorOptimized']
        else:
            valueY1 = self.data['DecError']
            valueY2 = self.data['RaError']

        if self.ui.checkWinsorize.isChecked():
            limit = float(self.ui.winsorizeLimit.text()) / 100.0
            valueY1 = self.winsorize(valueY1, limits=limit)
            valueY2 = self.winsorize(valueY2, limits=limit)

        axe1.set_title('Model error over modeled stars', color='white', fontweight='bold')
        axe1.set_ylabel('DEC error (arcsec)', color='#C0C0C0')
        axe1.yaxis.set_label_position('right')
        axe1.set_xlim(1, len(self.data['Index']))
        axe1.plot(self.data['Index'], valueY1, color='#181818', zorder=-10)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe1.scatter(self.data['Index'], valueY1, c=colors, s=30, zorder=10)

        axe2.set_xlabel('Number of modeled point', color='white', fontweight='bold')
        axe2.set_ylabel('RA error (arcsec)', color='#C0C0C0')
        axe2.yaxis.set_label_position('right')
        axe2.set_xlim(1, len(self.data['Index']))
        axe2.plot(self.data['Index'], valueY2, color='#181818', zorder=-10)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe2.scatter(self.data['Index'], valueY2, c=colors, s=30, zorder=10)

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

        if self.ui.checkOptimized.isChecked() and 'DecErrorOptimized' in self.data:
            valueY1 = self.data['DecErrorOptimized']
            valueY2 = self.data['RaErrorOptimized']
        else:
            valueY1 = self.data['DecError']
            valueY2 = self.data['RaError']

        if self.ui.checkWinsorize.isChecked():
            limit = float(self.ui.winsorizeLimit.text()) / 100.0
            valueY1 = self.winsorize(valueY1, limits=limit)
            valueY2 = self.winsorize(valueY2, limits=limit)

        axe1.set_title('Model error over Azimuth', color='white', fontweight='bold')
        axe1.set_ylabel('RA error (arcsec)', color='#C0C0C0')
        axe1.yaxis.set_label_position('right')
        axe1.set_xlim(0, 360)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe1.scatter(self.data['Azimuth'], valueY2, marker='o', c=colors, s=30, zorder=10)

        axe2.set_ylabel('DEC error (arcsec)', color='#C0C0C0')
        axe2.set_xlabel('Azimuth', color='white', fontweight='bold')
        axe2.yaxis.set_label_position('right')
        axe2.set_xlim(0, 360)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe2.scatter(self.data['Azimuth'], valueY1, marker='D', c=colors, s=30, zorder=10)

        axe3.set_title('Model error over Altitude', color='white', fontweight='bold')
        axe3.set_ylabel('RA error (arcsec)', color='#C0C0C0')
        axe3.yaxis.set_label_position('right')
        axe3.set_xlim(0, 90)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe3.scatter(self.data['Altitude'], valueY2, marker='o', c=colors, s=30, zorder=10)
        axe4.set_xlabel('Altitude', color='white', fontweight='bold')
        axe4.set_ylabel('DEC error (arcsec)', color='#C0C0C0')
        axe4.yaxis.set_label_position('right')
        axe4.set_xlim(0, 90)
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['Azimuth']])
        axe4.scatter(self.data['Altitude'], valueY1, marker='D', c=colors, s=30, zorder=10)

        self.analyseMatplotlib.draw()
