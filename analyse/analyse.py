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
import json
import math
import os
from logging import getLogger

# import for the PyQt5 Framework
import PyQt5.QtWidgets
import numpy
# matplotlib
from matplotlib import use

from baseclasses.widget import MwWidget
from gui import analyse_dialog_ui

use('Qt5Agg')
from matplotlib import pyplot as plt
from matplotlib import figure as figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class ShowAnalyseData(FigureCanvas):

    def __init__(self, parent=None):
        self.fig = figure.Figure(dpi=75, facecolor=(25/256, 25/256, 25/256))
        # self.axes = self.fig.add_axes([0.1, 0.1, 0.8, 0.8])
        self.axes = self.fig.add_subplot(111)
        self.axes.grid(True, color='white')
        self.axes.set_facecolor((32/256, 32/256, 32/256))
        self.axes.tick_params(axis='x', colors='white')
        self.axes.tick_params(axis='y', colors='white')
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.updateGeometry(self)


# noinspection PyTypeChecker
def calculateTimeConstant(x_time, y_value):
    timeconstant = 0
    # print(x_time)
    # print(y_value)
    x = 0
    y = 0
    return timeconstant, x, y


# noinspection PyUnresolvedReferences
class ShowAnalysePopup(MwWidget):
    logger = getLogger(__name__)

    def __init__(self, app):
        super(ShowAnalysePopup, self).__init__()
        self.app = app
        self.showStatus = False
        self.scaleRA = 10
        self.scaleDEC = 10
        self.scaleError = 10
        self.data = {}
        self.analyse = Analyse(self.app)
        self.ui = analyse_dialog_ui.Ui_AnalyseDialog()
        self.ui.setupUi(self)
        self.initUI()
        self.ui.windowTitle.setPalette(self.palette)
        self.ui.btn_selectClose.clicked.connect(self.hideAnalyseWindow)
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
        helper = PyQt5.QtWidgets.QVBoxLayout(self.ui.plot)
        self.plotWidget = ShowAnalyseData(self.ui.plot)
        helper.addWidget(self.plotWidget)
        self.initConfig()
        self.show()
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
            self.logger.error('initConfig -> item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['AnalysePopupWindowPositionX'] = self.pos().x()
        self.app.config['AnalysePopupWindowPositionY'] = self.pos().y()
        self.app.config['AnalysePopupWindowShowStatus'] = self.showStatus
        self.app.config['ScalePlotRA'] = self.ui.scalePlotRA.value()
        self.app.config['ScalePlotDEC'] = self.ui.scalePlotDEC.value()
        self.app.config['ScalePlotError'] = self.ui.scalePlotError.value()

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
        if filename == '' or not self.app.mount.transformConnected:
            return False
        self.scaleRA = self.ui.scalePlotRA.value()
        self.scaleDEC = self.ui.scalePlotDEC.value()
        self.scaleError = self.ui.scalePlotError.value()
        self.data = self.analyse.loadData(filename)
        return True

    def setFigure(self, projection=None):
        self.plotWidget.fig.clf()
        self.plotWidget.axes = self.plotWidget.fig.add_subplot(1, 1, 1, projection=projection)
        self.plotWidget.axes.grid(True, color='gray')
        self.plotWidget.axes.set_facecolor((32/256, 32/256, 32/256))
        self.plotWidget.axes.tick_params(axis='x', colors='white')
        self.plotWidget.axes.tick_params(axis='y', colors='white')

    def hideAnalyseWindow(self):
        self.showStatus = False
        self.setVisible(False)

    def showDecError(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotWidget.axes.set_xlabel('Number of Model Point', color='white')                                             # x axis
        self.plotWidget.axes.set_ylabel('DEC Error (arcsec)', color='white')                                                # y axis
        self.plotWidget.axes.set_title('DEC Error over Modeling\n ', color='white')                                         # title
        self.plotWidget.axes.set_xlim(0, len(self.data['index']))
        self.plotWidget.axes.set_ylim(-self.scaleDEC, self.scaleDEC)                                                        # defining the scaling of the plot
        self.plotWidget.axes.plot(self.data['index'], self.data['decError'], color='black')                                 # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.axes.scatter(self.data['index'], self.data['decError'], c=colors, s=50)
        self.plotWidget.draw()                                                                                              # put the plot in the widget

    def showDecErrorDeviation(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        # timeconstant, x, y = calculateTimeConstant(self.data['sidereal_time'], self.data['decError'])
        self.setFigure()
        self.plotWidget.axes.set_xlabel('Number of Model Point', color='white')                                             # x axis
        self.plotWidget.axes.set_ylabel('DEC Error(arcsec)', color='white')                                                 # y axis
        self.plotWidget.axes.set_title('DEC Error referenced to 0 over Modeling\n ', color='white')                         # title
        self.plotWidget.axes.set_xlim(0, len(self.data['index']))
        self.plotWidget.axes.set_ylim(-self.scaleDEC, self.scaleDEC)                                                        # defining the scaling of the plot
        decErrorDeviation = numpy.asarray(self.data['decError'])
        self.plotWidget.axes.plot(self.data['index'], decErrorDeviation - decErrorDeviation[0], color='black')              # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.axes.scatter(self.data['index'], decErrorDeviation - decErrorDeviation[0], c=colors, s=50)
        self.plotWidget.draw()                                                                                              # put the plot in the widget

    def showRaError(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotWidget.axes.set_xlabel('Number of Model Point', color='white')
        self.plotWidget.axes.set_ylabel('RA Error (arcsec)', color='white')
        self.plotWidget.axes.set_title('RA Error over Modeling\n ', color='white')
        self.plotWidget.axes.set_xlim(0, len(self.data['index']))
        self.plotWidget.axes.set_ylim(-self.scaleRA, self.scaleRA)
        self.plotWidget.axes.plot(self.data['index'], self.data['raError'], color='black')                                   # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.axes.scatter(self.data['index'], self.data['raError'], c=colors, s=50)
        self.plotWidget.draw()

    def showRaErrorDeviation(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotWidget.axes.set_xlabel('Number of Model Point', color='white')
        self.plotWidget.axes.set_ylabel('RA Error', color='white')
        self.plotWidget.axes.set_title('RA Error referenced to 0 over Modeling\n ', color='white')
        self.plotWidget.axes.axis([0, len(self.data['index']), -self.scaleRA, self.scaleRA])
        raErrorDeviation = numpy.asarray(self.data['raError'])
        self.plotWidget.axes.plot(self.data['index'], raErrorDeviation - raErrorDeviation[0], color='black')                 # Basic Data
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.axes.scatter(self.data['index'], raErrorDeviation - raErrorDeviation[0], c=colors, s=50)
        self.plotWidget.draw()

    def showDecErrorAltitude(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotWidget.axes.set_xlabel('Altitude', color='white')
        self.plotWidget.axes.set_ylabel('DEC Error (arcsec)', color='white')
        self.plotWidget.axes.set_title('DEC Error over Altitude\n ', color='white')
        self.plotWidget.axes.set_xlim(0, 90)
        self.plotWidget.axes.set_ylim(-self.scaleDEC, self.scaleDEC)
        self.plotWidget.axes.plot(self.data['altitude'], self.data['decError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.axes.scatter(self.data['altitude'], self.data['decError'], c=colors, s=50)
        self.plotWidget.draw()

    def showRaErrorAltitude(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotWidget.axes.set_xlabel('Altitude', color='white')
        self.plotWidget.axes.set_ylabel('RA Error (arcsec)', color='white')
        self.plotWidget.axes.set_title('RA Error over Altitude\n ', color='white')
        self.plotWidget.axes.set_xlim(0, 90)
        self.plotWidget.axes.set_ylim(-self.scaleRA, self.scaleRA)
        self.plotWidget.axes.plot(self.data['altitude'], self.data['raError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.axes.scatter(self.data['altitude'], self.data['raError'], c=colors, s=50)
        self.plotWidget.draw()

    def showDecErrorAzimuth(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotWidget.axes.set_xlabel('Altitude', color='white')
        self.plotWidget.axes.set_ylabel('DEC Error (arcsec)', color='white')
        self.plotWidget.axes.set_title('DEC Error over Azimuth\n ', color='white')
        self.plotWidget.axes.set_xlim(0, 360)
        self.plotWidget.axes.set_ylim(-self.scaleDEC, self.scaleDEC)
        self.plotWidget.axes.plot(self.data['azimuth'], self.data['decError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.axes.scatter(self.data['azimuth'], self.data['decError'], c=colors, s=50)
        self.plotWidget.draw()

    def showRaErrorAzimuth(self):
        if len(self.data) > 0:
            self.data = self.analyse.prepareData(self.data, self.scaleRA, self.scaleDEC)
        else:
            return
        self.setFigure()
        self.plotWidget.axes.set_xlabel('Altitude', color='white')
        self.plotWidget.axes.set_ylabel('RA Error (arcsec)', color='white')
        self.plotWidget.axes.set_title('RA Error over Azimuth\n ', color='white')
        self.plotWidget.axes.set_xlim(0, 360)
        self.plotWidget.axes.set_ylim(-self.scaleRA, self.scaleRA)
        self.plotWidget.axes.plot(self.data['azimuth'], self.data['raError'], color='black')
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.axes.scatter(self.data['azimuth'], self.data['raError'], c=colors, s=50)
        self.plotWidget.draw()

    def showModelPointPolar(self):
        self.setFigure('polar')
        self.plotWidget.axes.set_theta_zero_location('N')
        self.plotWidget.axes.set_theta_direction(-1)
        self.plotWidget.axes.set_yticks(range(0, 90, 10))
        yLabel = ['', '80', '', '60', '', '40', '', '20', '', '0']
        self.plotWidget.axes.set_yticklabels(yLabel, color='white')
        self.plotWidget.axes.set_title('Model Points\n ', color='white')
        azimuth = numpy.asarray(self.data['azimuth'])
        altitude = numpy.asarray(self.data['altitude'])
        colors = numpy.asarray(['blue' if x > 180 else 'green' for x in self.data['azimuth']])
        self.plotWidget.axes.plot(azimuth / 180.0 * 3.141593, 90 - altitude, color='black')
        self.plotWidget.axes.scatter(azimuth / 180.0 * 3.141593, 90 - altitude, c=colors, s=50)
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
        self.plotWidget.axes.set_title('Model Points Error\n ', color='white')
        azimuth = numpy.asarray(self.data['azimuth'])
        altitude = numpy.asarray(self.data['altitude'])
        self.plotWidget.axes.plot(azimuth / 180.0 * 3.141593, 90 - altitude, color='black')
        cm = plt.cm.get_cmap('RdYlGn_r')
        colors = numpy.asarray(self.data['modelError'])
        scaleError = int(max(colors) / 4 + 1) * 4
        area = colors * 100 / self.scaleError + 20
        theta = azimuth / 180.0 * 3.141593
        r = 90 - altitude
        scatter = self.plotWidget.axes.scatter(theta, r, c=colors, vmin=0, vmax=scaleError, s=area, cmap=cm)
        scatter.set_alpha(0.75)
        colorbar = self.plotWidget.fig.colorbar(scatter)
        colorbar.set_label('Error [arcsec]', color='white')
        plt.setp(plt.getp(colorbar.ax.axes, 'yticklabels'), color='white')
        self.plotWidget.axes.set_rmax(90)
        self.plotWidget.axes.set_rmin(0)
        self.plotWidget.draw()


class Analyse:
    logger = getLogger(__name__)

    def __init__(self, app):
        self.filepath = '/analysedata'
        self.app = app

    def saveData(self, dataProcess, name):                                                                                  # saving data from list to file
        if name in ['base.dat', 'refine.dat', 'actual.dat', 'simple.dat', 'dso1.dat', 'dso2.dat']:
            number = self.app.mount.numberModelStars()
            if number == -1:                                                                                                # if not real mount, than don't save model data
                return
        filenameData = os.getcwd() + self.filepath + '/' + name                                                             # built the filename
        try:                                                                                                                # write data to disk
            outfile = open(filenameData, 'w')                                                                               # open for write
            json.dump(dataProcess, outfile)
            outfile.close()                                                                                                 # close the save file
        except Exception as e:                                                                                              # Exception handling
            self.logger.error('saveData       -> analyse data file {0}, Error : {1}'.format(filenameData, e))
            return

    def processTheSkyXLine(self, line):
        ra_sol = self.app.mount.degStringToDecimal(line[0:13], ' ')
        dec_sol = self.app.mount.degStringToDecimal(line[15:28], ' ')
        ra = self.app.mount.degStringToDecimal(line[30:43], ' ')
        dec = self.app.mount.degStringToDecimal(line[45:58], ' ')
        lst = self.app.mount.degStringToDecimal(line[61:70], ' ')
        return ra, dec, ra_sol, dec_sol, lst

    def loadTheSkyXData(self, filename):
        resultData = {}
        try:
            with open(filename) as infile:
                lines = infile.read().splitlines()
            infile.close()
            site_latitude = self.app.mount.degStringToDecimal(lines[4][0:9], ' ')
            for i in range(5, len(lines)):
                ra, dec, ra_sol, dec_sol, lst = self.processTheSkyXLine(lines[i])
                if 'ra_J2000' in resultData:
                    resultData['ra_J2000'].append(ra)
                else:
                    resultData['ra_J2000'] = [ra]
                if 'dec_J2000' in resultData:
                    resultData['dec_J2000'].append(dec)
                else:
                    resultData['dec_J2000'] = [dec]
                ra_Jnow, dec_Jnow = self.app.mount.transformNovas(ra, dec, 3)
                if 'ra_Jnow' in resultData:
                    resultData['ra_Jnow'].append(ra_Jnow)
                else:
                    resultData['ra_Jnow'] = [ra_Jnow]
                if 'dec_Jnow' in resultData:
                    resultData['dec_Jnow'].append(dec_Jnow)
                else:
                    resultData['dec_Jnow'] = [dec_Jnow]
                if 'sidereal_time_float' in resultData:
                    resultData['sidereal_time_float'].append(lst)
                else:
                    resultData['sidereal_time_float'] = [lst]
                if 'sidereal_time' in resultData:
                    resultData['sidereal_time'].append(self.app.mount.decimalToDegree(lst, False, True))
                else:
                    resultData['sidereal_time'] = [self.app.mount.decimalToDegree(lst, False, True)]
                if 'ra_sol' in resultData:
                    resultData['ra_sol'].append(ra_sol)
                else:
                    resultData['ra_sol'] = [ra_sol]
                if 'dec_sol' in resultData:
                    resultData['dec_sol'].append(dec_sol)
                else:
                    resultData['dec_sol'] = [dec_sol]
                ra_sol_Jnow, dec_sol_Jnow = self.app.mount.transformNovas(ra_sol, dec_sol, 3)
                if 'ra_sol_Jnow' in resultData:
                    resultData['ra_sol_Jnow'].append(ra_sol_Jnow)
                else:
                    resultData['ra_sol_Jnow'] = [ra_sol_Jnow]
                if 'dec_sol_Jnow' in resultData:
                    resultData['dec_sol_Jnow'].append(dec_sol_Jnow)
                else:
                    resultData['dec_sol_Jnow'] = [dec_sol_Jnow]
                ha = ra - lst
                az, alt = self.app.mount.transformNovas(ha, dec, 4)
                if 'azimuth' in resultData:
                    resultData['azimuth'].append(az)
                else:
                    resultData['azimuth'] = [az]
                if 'altitude' in resultData:
                    resultData['altitude'].append(alt)
                else:
                    resultData['altitude'] = [alt]
                if az <= 180:
                    pierside = 'E'
                else:
                    pierside = 'W'
                if 'pierside' in resultData:
                    resultData['pierside'].append(pierside)
                else:
                    resultData['pierside'] = [pierside]
                if 'index' in resultData:
                    resultData['index'].append(i - 5)
                else:
                    resultData['index'] = [i - 5]
                if 'raError' in resultData:
                    resultData['raError'].append((ra - ra_sol) * 3600)
                else:
                    resultData['raError'] = [(ra - ra_sol) * 3600]
                if 'decError' in resultData:
                    resultData['decError'].append((dec - dec_sol) * 3600)
                else:
                    resultData['decError'] = [(dec - dec_sol) * 3600]
                if 'modelError' in resultData:
                    resultData['modelError'].append(math.sqrt((ra - ra_sol) * 3600 * (ra - ra_sol) * 3600 + (dec - dec_sol) * 3600 * (dec - dec_sol) * 3600))
                else:
                    resultData['modelError'] = [math.sqrt((ra - ra_sol) * 3600 * (ra - ra_sol) * 3600 + (dec - dec_sol) * 3600 * (dec - dec_sol) * 3600)]
        except Exception as e:
            self.logger.error('loadTheSkyXData-> error processing file {0}, Error : {1}'.format(filename, e))
            return {}
        return resultData

    def loadMountWizzardData(self, filename):
        try:                                                                                                                # try to read the file
            infile = open(filename, 'r')
            dataJson = json.load(infile)
            infile.close()                                                                                                  # close
        except Exception as e:                                                                                              # exception handling
            self.logger.error('loadMountWizzar->  analyse data file {0}, Error : {1}'.format(filename, e))
            return {}                                                                                                       # loading doesn't work
        resultData = dict()
        for timestepdict in dataJson:
            for (keyData, valueData) in timestepdict.items():
                if keyData in resultData:
                    resultData[keyData].append(valueData)
                else:
                    resultData[keyData] = [valueData]
        return resultData                                                                                                   # successful loading

    def loadDataRaw(self, filename):                                                                                        # saving data from list to file
        filenameData = os.getcwd() + self.filepath + '/' + filename                                                         # generate filename
        if os.path.isfile(filenameData):
            infile = open(filenameData, 'r')
            dataJson = json.load(infile)
            infile.close()
            return dataJson
        else:
            return None

    def loadData(self, filename):                                                                                           # loading data
        filenameData = os.getcwd() + self.filepath + '/' + filename                                                         # generate filename
        if os.path.isfile(filenameData):
            infile = open(filenameData, 'r')
            check = infile.read(8)
            infile.close()
            if check == '!TheSkyX':
                data = self.loadTheSkyXData(filenameData)
            else:
                data = self.loadMountWizzardData(filenameData)
            return data

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
    logger = getLogger(__name__)
    from mount.mount_thread import Mount
    filename = '10micron_model.dat'
    m = Mount
    a = Analyse(m)
    data = a.loadData(filename)
    # print(data)
