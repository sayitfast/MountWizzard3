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
import os
import json
import numpy
import copy
# import for the PyQt5 Framework
import PyQt5.QtWidgets
from support.mw_widget import MwWidget
from support.analyse_dialog_ui import Ui_AnalyseDialog
# matplotlib
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class ShowAnalyseData(FigureCanvas):

    def __init__(self, parent=None):
        self.plt = plt
        self.fig = self.plt.figure(dpi=75)
        rect = self.fig.patch
        rect.set_facecolor((25/256, 25/256, 25/256))
        self.axes = self.fig.add_subplot(111)
        self.axes.grid(True, color='white')
        self.axes.set_facecolor((32/256, 32/256, 32/256))
        self.axes.tick_params(axis='x', colors='white')
        self.axes.tick_params(axis='y', colors='white')
        self.plt.rcParams['toolbar'] = 'None'
        self.plt.rcParams['axes.titlesize'] = 'large'
        self.plt.rcParams['axes.labelsize'] = 'medium'
        self.plt.tight_layout(rect=[0.05, 0.025, 0.95, 0.925])
        self.compute_initial_figure()
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        self.axes.plot(1, 1)


# noinspection PyTypeChecker
class ShowAnalysePopup(MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, uiMain):
        super(ShowAnalysePopup, self).__init__()

        self.uiMain = uiMain
        self.showStatus = False
        self.scaleRA = 10
        self.scaleDEC = 10
        self.scaleError = 10
        self.data = {}
        self.analyse = Analyse()
        self.ui = Ui_AnalyseDialog()
        self.ui.setupUi(self)
        self.initUI()
        self.ui.windowTitle.setPalette(self.palette)
        self.ui.btn_selectClose.clicked.connect(self.hideAnalyseWindow)
        self.ui.scalePlotDEC.valueChanged.connect(self.getData)
        self.ui.scalePlotRA.valueChanged.connect(self.getData)
        self.ui.scalePlotError.valueChanged.connect(self.getData)
        self.ui.btn_selectDecError.clicked.connect(self.showDecError)
        self.ui.btn_selectRaError.clicked.connect(self.showRaError)
        self.ui.btn_selectDecErrorAltitude.clicked.connect(self.showDecErrorAltitude)
        self.ui.btn_selectRaErrorAltitude.clicked.connect(self.showRaErrorAltitude)
        self.ui.btn_selectDecErrorAzimuth.clicked.connect(self.showDecErrorAzimuth)
        self.ui.btn_selectRaErrorAzimuth.clicked.connect(self.showRaErrorAzimuth)
        self.ui.btn_selectModelPointPolar.clicked.connect(self.showModelPointPolar)
        self.ui.btn_selectModelPointErrorPolar.clicked.connect(self.showModelPointErrorPolar)
        helper = PyQt5.QtWidgets.QVBoxLayout(self.ui.plot)
        self.plotWidget = ShowAnalyseData(self.ui.plot)
        helper.addWidget(self.plotWidget)
        self.show()
        self.setVisible(False)

    def getData(self):
        filenameData = self.uiMain.le_analyseFileName.text()
        self.scaleRA = self.ui.scalePlotRA.value()
        self.scaleDEC = self.ui.scalePlotDEC.value()
        self.scaleError = self.ui.scalePlotError.value()
        self.data = self.analyse.loadData(filenameData)
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)

    def setFigure(self, projection=None):
        self.plotWidget.plt.clf()
        self.plotWidget.axes = self.plotWidget.fig.add_subplot(111, projection=projection)
        self.plotWidget.axes.grid(True, color='gray')
        self.plotWidget.axes.set_facecolor((32/256, 32/256, 32/256))
        self.plotWidget.axes.tick_params(axis='x', colors='white')
        self.plotWidget.axes.tick_params(axis='y', colors='white')
        if projection:
            self.plotWidget.plt.tight_layout(rect=[0.05, 0.025, 0.95, 0.925])
        else:
            self.plotWidget.plt.tight_layout(rect=[0.05, 0.025, 0.95, 0.925])

    def hideAnalyseWindow(self):
        self.showStatus = False
        self.setVisible(False)

    def showDecError(self):
        if len(self.data) == 0:
            return
        self.setFigure()
        self.plotWidget.plt.xlabel('Number of Model Point', color='white')                                                  # x axis
        self.plotWidget.plt.ylabel('DEC Error (arcsec)', color='white')                                                     # y axis
        self.plotWidget.plt.title('DEC Error over Modeling\n ', color='white')                                              # title
        self.plotWidget.plt.axis([0, len(self.data['index']), -self.scaleDEC, self.scaleDEC])                               # defining the scaling of the plot
        self.plotWidget.plt.plot(self.data['index'], self.data['decError'], color='black')                                  # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.plt.scatter(self.data['index'], self.data['decError'], c=colors, s=50)
        self.plotWidget.draw()                                                                                              # put the plot in the widget

    def showRaError(self):
        self.setFigure()
        self.plotWidget.plt.xlabel('Number of Model Point', color='white')
        self.plotWidget.plt.ylabel('RA Error (arcsec)', color='white')
        self.plotWidget.plt.title('RA Error over Modeling\n ', color='white')
        self.plotWidget.plt.axis([0, len(self.data['index']), -self.scaleRA, self.scaleRA])
        self.plotWidget.plt.plot(self.data['index'], self.data['raError'], color='black')                                   # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.plt.scatter(self.data['index'], self.data['raError'], c=colors, s=50)
        self.plotWidget.draw()

    def showDecErrorAltitude(self):
        self.setFigure()
        self.plotWidget.plt.xlabel('Altitude', color='white')
        self.plotWidget.plt.ylabel('DEC Error (arcsec)', color='white')
        self.plotWidget.plt.title('DEC Error over Altitude\n ', color='white')
        self.plotWidget.plt.axis([0, 90, -self.scaleDEC, self.scaleDEC])
        self.plotWidget.plt.plot(self.data['altitude'], self.data['decError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.plt.scatter(self.data['altitude'], self.data['decError'], c=colors, s=50)
        self.plotWidget.draw()

    def showRaErrorAltitude(self):
        self.setFigure()
        self.plotWidget.plt.xlabel('Altitude', color='white')
        self.plotWidget.plt.ylabel('RA Error (arcsec)', color='white')
        self.plotWidget.plt.title('RA Error over Altitude\n ', color='white')
        self.plotWidget.plt.axis([0, 90, -self.scaleRA, self.scaleRA])
        self.plotWidget.plt.plot(self.data['altitude'], self.data['raError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.plt.scatter(self.data['altitude'], self.data['raError'], c=colors, s=50)
        self.plotWidget.draw()

    def showDecErrorAzimuth(self):
        self.setFigure()
        self.plotWidget.plt.xlabel('Altitude', color='white')
        self.plotWidget.plt.ylabel('DEC Error (arcsec)', color='white')
        self.plotWidget.plt.title('DEC Error over Azimuth\n ', color='white')
        self.plotWidget.plt.axis([0, 360, -self.scaleDEC, self.scaleDEC])
        self.plotWidget.plt.plot(self.data['azimuth'], self.data['decError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.plt.scatter(self.data['azimuth'], self.data['decError'], c=colors, s=50)
        self.plotWidget.draw()

    def showRaErrorAzimuth(self):
        self.setFigure()
        self.plotWidget.plt.xlabel('Altitude', color='white')
        self.plotWidget.plt.ylabel('RA Error (arcsec)', color='white')
        self.plotWidget.plt.title('RA Error over Azimuth\n ', color='white')
        self.plotWidget.plt.axis([0, 360, -self.scaleRA, self.scaleRA])
        self.plotWidget.plt.plot(self.data['azimuth'], self.data['raError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.plt.scatter(self.data['azimuth'], self.data['raError'], c=colors, s=50)
        self.plotWidget.draw()

    def showModelPointPolar(self):
        self.setFigure('polar')
        self.plotWidget.axes.set_theta_zero_location('N')
        self.plotWidget.axes.set_theta_direction(-1)
        self.plotWidget.axes.set_yticks(range(0, 90, 10))
        yLabel = ['', '80', '', '60', '', '40', '', '20', '', '0']
        self.plotWidget.axes.set_yticklabels(yLabel, color='white')
        self.plotWidget.plt.title('Model Points\n ', color='white')
        azimuth = numpy.asarray(self.data['azimuth'])
        altitude = numpy.asarray(self.data['altitude'])
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.plt.plot(azimuth / 180.0 * 3.141593, 90 - altitude, color='black')
        self.plotWidget.plt.scatter(azimuth / 180.0 * 3.141593, 90 - altitude, c=colors, s=50)
        self.plotWidget.axes.set_rmax(90)
        self.plotWidget.axes.set_rmin(0)
        self.plotWidget.draw()

    def showModelPointErrorPolar(self):
        self.setFigure('polar')
        self.plotWidget.axes.set_theta_zero_location('N')
        self.plotWidget.axes.set_theta_direction(-1)
        self.plotWidget.axes.set_yticks(range(0, 90, 10))
        yLabel = ['', '80', '', '60', '', '40', '', '20', '', '0']
        self.plotWidget.axes.set_yticklabels(yLabel, color='white')
        self.plotWidget.plt.title('Model Points Error\n ', color='white')
        azimuth = numpy.asarray(self.data['azimuth'])
        altitude = numpy.asarray(self.data['altitude'])
        self.plotWidget.plt.plot(azimuth / 180.0 * 3.141593, 90 - altitude, color='black')
        cm = plt.cm.get_cmap('RdYlGn_r')
        colors = numpy.asarray(self.data['modelError'])
        area = colors * 100 / self.scaleError + 20
        theta = azimuth / 180.0 * 3.141593
        r = 90 - altitude
        scatter = self.plotWidget.plt.scatter(theta, r, c=colors, vmin=1, vmax=self.scaleError, s=area, cmap=cm)
        scatter.set_alpha(0.75)
        colorbar = self.plotWidget.plt.colorbar(scatter)
        colorbar.set_label('Error [arcsec]', color='white')
        plt.setp(plt.getp(colorbar.ax.axes, 'yticklabels'), color='white')
        self.plotWidget.axes.set_rmax(90)
        self.plotWidget.axes.set_rmin(0)
        self.plotWidget.draw()


class Analyse:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.filepath = '/analysedata'

    def saveData(self, dataProcess, name):                                                                                  # saving data from list to file
        filenameData = os.getcwd() + self.filepath + '/' + name                                                             # built the filename
        try:                                                                                                                # write data to disk
            outfile = open(filenameData, 'w')                                                                               # open for write
            json.dump(dataProcess, outfile)
            outfile.close()                                                                                                 # close the save file
        except Exception as e:                                                                                              # Exception handling
            self.logger.error('saveData       -> analyse data file {0}, Error : {1}'.format(filenameData, e))
            return

    def loadData(self, name):                                                                                               # loading data
        filenameData = os.getcwd() + self.filepath + '/' + name                                                             # generate filename
        try:                                                                                                                # try to read the file
            infileData = open(filenameData, 'r')
            dataJson = json.load(infileData)
            infileData.close()                                                                                                  # close
        except Exception as e:                                                                                              # exception handling
            self.logger.error('loadData       ->  analyse data file {0}, Error : {1}'.format(filenameData, e))
            return {}                                                                                                       # loading doesn't work
        resultData = dict()
        for timestepdict in dataJson:
            for (keyData, valueData) in timestepdict.items():
                if keyData in resultData:
                    resultData[keyData].append(valueData)
                else:
                    resultData[keyData] = [valueData]
        return resultData                                                                                                   # successful loading

    @staticmethod
    def prepareData(dataProcess, scaleRA, scaleDEC):
        if len(dataProcess) == 0:                                                                                           # in case no data loaded ->
            return dataProcess                                                                                              # quit
        dataProcess['raError'] = [scaleRA if x > scaleRA else x for x in dataProcess['raError']]
        dataProcess['raError'] = [-scaleRA if x < -scaleRA else x for x in dataProcess['raError']]
        dataProcess['decError'] = [scaleDEC if x > scaleDEC else x for x in dataProcess['decError']]
        dataProcess['decError'] = [-scaleDEC if x < -scaleDEC else x for x in dataProcess['decError']]
        return dataProcess

if __name__ == "__main__":
    filename = 'C:/Users/mw/Projects/mountwizzard/mountwizzard/analysedata/2017-01-22-19-46-07_test.dat'
    infile = open(filename, 'r')
    data = json.load(infile)
    infile.close()  # close
    result = dict()
    for timedict in data:
        for (key, value) in timedict.items():
            if key in result:
                pass
                result[key].append(value)
            else:
                result[key] = [value]
    print(result['ra'])
    b = [5 if x > 5 else x for x in result['ra']]
    print(b)
