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
import numpy
# import for the PyQt5 Framework
from PyQt5.QtWidgets import *
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
        self.axes.set_axis_bgcolor((48/256, 48/256, 48/256))
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


class ShowAnalysePopup(MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, uiMain):
        super(ShowAnalysePopup, self).__init__()

        self.uiMain = uiMain
        self.showStatus = False
        self.analyse = Analyse()
        self.ui = Ui_AnalyseDialog()
        self.ui.setupUi(self)
        self.initUI()
        self.ui.windowTitle.setPalette(self.palette)
        self.ui.btn_selectClose.clicked.connect(self.closeAnalyseWindow)
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
        helper = QVBoxLayout(self.ui.plot)
        self.plotWidget = ShowAnalyseData(self.ui.plot)
        helper.addWidget(self.plotWidget)

    def getData(self, filename):
        self.scaleRA = self.ui.scalePlotRA.value()
        self.scaleDEC = self.ui.scalePlotDEC.value()
        self.scaleError = self.ui.scalePlotError.value()
        self.data = self.analyse.loadData(filename)
        if len(self.data) > 0:
            self.dat, self.datWest, self.datEast, self.datOut, self.isDatWest, self.isDatEast, self.isDatOut = \
                self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)

    def setFigure(self, projection=None):
        self.plotWidget.plt.clf()
        self.plotWidget.axes = self.plotWidget.fig.add_subplot(111, projection=projection)
        self.plotWidget.axes.grid(True, color='white')
        self.plotWidget.axes.set_axis_bgcolor((48/256, 48/256, 48/256))
        self.plotWidget.axes.tick_params(axis='x', colors='white')
        self.plotWidget.axes.tick_params(axis='y', colors='white')
        if projection:
            self.plotWidget.plt.tight_layout(rect=[0.05, 0.025, 0.95, 0.925])
        else:
            self.plotWidget.plt.tight_layout(rect=[0.05, 0.025, 0.95, 0.925])

    def closeAnalyseWindow(self):
        self.showStatus = False
        self.close()

    def showDecError(self):
        self.setFigure()
        self.plotWidget.plt.xlabel('Number of Model Point', color='white')
        self.plotWidget.plt.ylabel('DEC Error (arcsec)', color='white')
        self.plotWidget.plt.title('DEC Error over Modeling\n ', color='white')
        self.plotWidget.plt.axis([0, len(self.data), -self.scaleDEC, self.scaleDEC])
        self.plotWidget.plt.grid(True, color='white')
        self.plotWidget.plt.plot(self.dat[0], self.dat[8], color='black')
        if self.isDatWest:
            self.plotWidget.plt.plot(self.datWest[0], self.datWest[8], 'bo')
        if self.isDatEast:
            self.plotWidget.plt.plot(self.datEast[0], self.datEast[8], 'go')
        if self.isDatOut:
            self.plotWidget.plt.plot(self.datOut[0], self.datOut[8], 'ro')
        self.plotWidget.draw()

    def showRaError(self):
        self.setFigure()
        self.plotWidget.plt.xlabel('Number of Model Point', color='white')
        self.plotWidget.plt.ylabel('RA Error (arcsec)', color='white')
        self.plotWidget.plt.title('RA Error over Modeling\n ', color='white')
        self.plotWidget.plt.axis([0, len(self.data), -self.scaleRA, self.scaleRA])
        self.plotWidget.plt.grid(True, color='white')
        self.plotWidget. plt.plot(self.dat[0], self.dat[7], color='black')
        if self.isDatWest:
            self.plotWidget.plt.plot(self.datWest[0], self.datWest[7], 'bo')
        if self.isDatEast:
            self.plotWidget.plt.plot(self.datEast[0], self.datEast[7], 'go')
        if self.isDatOut:
            self.plotWidget.plt.plot(self.datOut[0], self.datOut[7], 'ro')
        self.plotWidget.draw()

    def showDecErrorAltitude(self):
        self.setFigure()
        self.plotWidget.plt.xlabel('Altitude', color='white')
        self.plotWidget.plt.ylabel('DEC Error (arcsec)', color='white')
        self.plotWidget.plt.title('DEC Error over Altitude\n ', color='white')
        self.plotWidget.plt.axis([0, 90, -self.scaleDEC, self.scaleDEC])
        self.plotWidget.plt.grid(True, color='white')
        self.plotWidget.plt.plot(self.dat[2], self.dat[8], color='black')
        if self.isDatWest:
            self.plotWidget.plt.plot(self.datWest[2], self.datWest[8], 'bo')
        if self.isDatEast:
            self.plotWidget.plt.plot(self.datEast[2], self.datEast[8], 'go')
        if self.isDatOut:
            self.plotWidget.plt.plot(self.datOut[2], self.datOut[8], 'ro')
        self.plotWidget.draw()

    def showRaErrorAltitude(self):
        self.setFigure()
        self.plotWidget.plt.xlabel('Altitude', color='white')
        self.plotWidget.plt.ylabel('RA Error (arcsec)', color='white')
        self.plotWidget.plt.title('RA Error over Altitude\n ', color='white')
        self.plotWidget.plt.axis([0, 90, -self.scaleRA, self.scaleRA])
        self.plotWidget.plt.grid(True, color='white')
        self.plotWidget. plt.plot(self.dat[2], self.dat[7], color='black')
        if self.isDatWest:
            self.plotWidget.plt.plot(self.datWest[2], self.datWest[7], 'bo')
        if self.isDatEast:
            self.plotWidget.plt.plot(self.datEast[2], self.datEast[7], 'go')
        if self.isDatOut:
            self.plotWidget.plt.plot(self.datOut[2], self.datOut[7], 'ro')
        self.plotWidget.draw()

    def showDecErrorAzimuth(self):
        self.setFigure()
        self.plotWidget.plt.xlabel('Altitude', color='white')
        self.plotWidget.plt.ylabel('DEC Error (arcsec)', color='white')
        self.plotWidget.plt.title('DEC Error over Azimuth\n ', color='white')
        self.plotWidget.plt.axis([0, 360, -self.scaleDEC, self.scaleDEC])
        self.plotWidget.plt.grid(True, color='white')
        self.plotWidget.plt.plot(self.dat[1], self.dat[8], color='black')
        if self.isDatWest:
            self.plotWidget.plt.plot(self.datWest[1], self.datWest[8], 'bo')
        if self.isDatEast:
            self.plotWidget.plt.plot(self.datEast[1], self.datEast[8], 'go')
        if self.isDatOut:
            self.plotWidget.plt.plot(self.datOut[1], self.datOut[8], 'ro')
        self.plotWidget.draw()

    def showRaErrorAzimuth(self):
        self.setFigure()
        self.plotWidget.plt.xlabel('Altitude', color='white')
        self.plotWidget.plt.ylabel('RA Error (arcsec)', color='white')
        self.plotWidget.plt.title('RA Error over Azimuth\n ', color='white')
        self.plotWidget.plt.axis([0, 360, -self.scaleRA, self.scaleRA])
        self.plotWidget.plt.grid(True, color='white')
        self.plotWidget. plt.plot(self.dat[1], self.dat[7], color='black')
        if self.isDatWest:
            self.plotWidget.plt.plot(self.datWest[1], self.datWest[7], 'bo')
        if self.isDatEast:
            self.plotWidget.plt.plot(self.datEast[1], self.datEast[7], 'go')
        if self.isDatOut:
            self.plotWidget.plt.plot(self.datOut[1], self.datOut[7], 'ro')
        self.plotWidget.draw()

    def showModelPointPolar(self):
        self.setFigure('polar')
        self.plotWidget.axes.set_theta_zero_location('N')
        self.plotWidget.axes.set_theta_direction(-1)
        self.plotWidget.axes.set_rmax(90)
        self.plotWidget.axes.set_rmin(0)
        self.plotWidget.axes.set_yticks(range(0, 90, 10))
        yLabel = ['90', '', '', '60', '', '', '30', '', '', '']
        self.plotWidget.axes.set_yticklabels(yLabel, color='white')
        self.plotWidget.plt.title('Model Points\n ', color='white')
        self.plotWidget.plt.grid(True, color='white')
        self.plotWidget. plt.plot(self.dat[1] / 180.0 * 3.141593, 90 - self.dat[2], color='black')
        if self.isDatWest:
            self.plotWidget.plt.plot(self.datWest[1] / 180.0 * 3.141593, 90 - self.datWest[2], 'bo')
        if self.isDatEast:
            self.plotWidget.plt.plot(self.datEast[1] / 180.0 * 3.141593, 90 - self.datEast[2], 'go')
        if self.isDatOut:
            self.plotWidget.plt.plot(self.datOut[1] / 180.0 * 3.141593, 90 - self.datOut[2], 'ro')
        self.plotWidget.draw()

    def showModelPointErrorPolar(self):
        self.setFigure('polar')
        self.plotWidget.axes.set_theta_zero_location('N')
        self.plotWidget.axes.set_theta_direction(-1)
        self.plotWidget.axes.set_rmax(90)
        self.plotWidget.axes.set_rmin(0)
        self.plotWidget.axes.set_yticks(range(0, 90, 10))
        yLabel = ['90', '', '', '60', '', '', '30', '', '', '']
        self.plotWidget.axes.set_yticklabels(yLabel, color='white')
        self.plotWidget.plt.title('Model Points Error\n ', color='white')
        self.plotWidget.plt.grid(True, color='white')
        self.plotWidget.plt.plot(self.dat[1] / 180.0 * 3.141593, 90 - self.dat[2], color='black')
        cm = plt.cm.get_cmap('RdYlGn_r')
        colors = self.dat[9]
        area = self.dat[9] * 100 / self.scaleError + 20
        theta = self.dat[1] / 180.0 * 3.141593
        r = 90 - self.dat[2]
        scatter = self.plotWidget.plt.scatter(theta, r, c=colors, vmin=1, vmax=self.scaleError, s=area, cmap=cm)
        scatter.set_alpha(0.75)
        colorbar = self.plotWidget.plt.colorbar(scatter, shrink=0.9)
        colorbar.set_label('Error [arcsec]', color='white')
        plt.setp(plt.getp(colorbar.ax.axes, 'yticklabels'), color='white')
        self.plotWidget.draw()


class Analyse:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.filepath = '/analysedata'

    def saveData(self, data, name):                                                                                         # saving data from list to file
        filename = os.getcwd() + self.filepath + '/' + name                                                                 # built the filename
        try:                                                                                                                # write data to disk
            outfile = open(filename, 'w')                                                                                   # open for write
            for item in data:                                                                                               # run through the data items
                outfile.write('{0}\n'.format(item))                                                                         # write data lines
            outfile.close()                                                                                                 # close the save file
        except Exception as e:                                                                                              # Exception handling
            self.logger.error('saveData -> item in analyse data could not be stored in file {0}, Error : {1}'.format(filename, e))
            return

    def loadData(self, name):                                                                                               # loading data
        filename = os.getcwd() + self.filepath + '/' + name                                                                 # generate filename
        data = []                                                                                                           # clear data list
        try:                                                                                                                # try to read the file
            with open(filename) as infile:                                                                                  # open
                lines = infile.read().splitlines()                                                                          # read over all the lines
            infile.close()                                                                                                  # close
            for i in range(len(lines)):                                                                                     # convert from text to array of floats
                lst1 = lines[i].strip(')').strip('(').split(',')                                                            # shorten the text and split to items
                lst2 = [float(i) for i in lst1]                                                                             # convert to float
                data.append(lst2)                                                                                           # add element to list
        except Exception as e:                                                                                              # exception handling
            self.logger.error('loadData -> item in analyse data could not be loaded from file {0}, Error : {1}'.format(filename, e))
            return []                                                                                                       # loading doesn't work
        return data                                                                                                         # successful loading

    def prepareData(self, data, scaleRA, scaleDEC):
        # index in plot             0  1    2   3   4   5       6           7       8       9
        # data format of analyse: (i, az, alt, ra, dec, ra_sol, dec_sol, raError, decError, err)
        if len(data) == 0:                                                                                                  # in case no data loaded ->
            return                                                                                                          # quit
        dat = numpy.asarray(data)                                                                                           # convert list to array
        datWest = []                                                                                                        # clear the storage, point of west side of pier
        isDatWest = False
        datEast = []                                                                                                        # point on the east side of pier
        isDatEast = False
        datOut = []                                                                                                         # exceeding the min/max value
        isDatOut = False
        for i in range(0, len(dat)):                                                                                        # separate data for coloring
            out = False                                                                                                     # point out of range ?
            if dat[i][7] > scaleRA:
                dat[i][7] = scaleRA
                out = True
            elif dat[i][7] < -scaleRA:
                dat[i][7] = -scaleRA
                out = True
            elif dat[i][8] > scaleDEC:
                dat[i][8] = scaleDEC
                out = True
            elif dat[i][8] < -scaleDEC:
                dat[i][8] = -scaleDEC
                out = True
            if out:                                                                                                         # if out of range, put it to this list
                datOut.append(dat[i])                                                                                       # append
                isDatOut = True
            else:
                if dat[i][1] > 180:                                                                                         # separate east from west and in scale from otu scale
                    datWest.append(dat[i])                                                                                  # append to west list
                    isDatWest = True
                else:
                    datEast.append(dat[i])                                                                                  # append to east list
                    isDatEast = True
        datWest = numpy.transpose(datWest)                                                                                  # transpose array
        datEast = numpy.transpose(datEast)                                                                                  # transpose array
        datOut = numpy.transpose(datOut)
        dat = numpy.transpose(dat)                                                                                          # transpose array
        return dat, datWest, datEast, datOut, isDatWest, isDatEast, isDatOut


if __name__ == "__main__":
    pass