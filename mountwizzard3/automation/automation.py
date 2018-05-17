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
import os
import logging
import time
import PyQt5
import requests
import queue
import comtypes.client
from pywinauto import Application, timings, findwindows, application
from pywinauto.controls.win32_controls import ButtonWrapper, EditWrapper


class Automation(PyQt5.QtCore.QObject):
    logger = logging.getLogger(__name__)

    CYCLE = 500
    signalDestruct = PyQt5.QtCore.pyqtSignal()

    UTC_1 = 'http://maia.usno.navy.mil/ser7/finals.data'
    UTC_2 = 'http://maia.usno.navy.mil/ser7/tai-utc.dat'
    COMETS = 'http://www.minorplanetcenter.net/iau/MPCORB/CometEls.txt'
    COMETS_START = 102
    COMETS_END = 161
    ASTEROIDS_START = 165
    ASTEROIDS_END = 196
    ASTEROIDS_MPC5000 = 'http://www.ap-i.net/pub/skychart/mpc/mpc5000.dat'
    # ASTEROIDS = 'http://www.minorplanetcenter.net/iau/MPCORB/MPCORB.DAT'
    ASTEROIDS_NEA = 'http://www.minorplanetcenter.net/iau/MPCORB/NEA.txt'
    ASTEROIDS_PHA = 'http://www.minorplanetcenter.net/iau/MPCORB/PHA.txt'
    ASTEROIDS_TNO = 'http://www.minorplanetcenter.net/iau/MPCORB/Distant.txt'
    ASTEROIDS_UNUSAL = 'http://www.minorplanetcenter.net/iau/MPCORB/Unusual.txt'
    SPACESTATIONS = 'http://www.celestrak.com/NORAD/elements/stations.txt'
    SATBRIGHTEST = 'http://www.celestrak.com/NORAD/elements/visual.txt'
    COMETS_FILE = 'comets.mpc'
    ASTEROIDS_FILE = 'asteroids.mpc'
    SPACESTATIONS_FILE = 'spacestations.tle'
    SATBRIGHTEST_FILE = 'satbrightest.tle'
    UTC_1_FILE = 'finals.data'
    UTC_2_FILE = 'tai-utc.dat'
    OPENDIALOG = 'Dialog'

    def __init__(self, app, thread):
        super().__init__()
        self.isRunning = False
        self.mutexIsRunning = PyQt5.QtCore.QMutex()

        self.app = app
        self.thread = thread
        self.commandDispatcherQueue = queue.Queue()
        self.cycleTimer = None

        self.appAvailable = False
        self.appName = ''
        self.appInstallPath = ''
        self.appExe = 'GmQCIv2.exe'
        # defining the command dispatcher
        self.commandDispatch = {
            'COMETS':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_downloadComets,
                            'Method': self.downloadFile,
                            'Parameter': ['self.COMETS',
                                          'self.TARGET_DIR + self.COMETS_FILE'],
                            'Checkbox': self.app.ui.checkComets
                        }
                    ]
                },
            'UPLOADMOUNT':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_uploadMount,
                            'Method': self.uploadMount
                        }
                    ]
                },
            'SPACESTATIONS':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_downloadSpacestations,
                            'Method': self.downloadFile,
                            'Parameter': ['self.SPACESTATIONS',
                                          'self.TARGET_DIR + self.SPACESTATIONS_FILE'],
                            'Checkbox': self.app.ui.checkTLE
                        }
                    ]
                },
            'SATBRIGHTEST':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_downloadSatbrighest,
                            'Method': self.downloadFile,
                            'Parameter': ['self.SATBRIGHTEST',
                                          'self.TARGET_DIR + self.SATBRIGHTEST_FILE'],
                            'Checkbox': self.app.ui.checkTLE
                        }
                    ]
                },
            'ASTEROIDS_MPC5000':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_downloadAsteroidsMPC5000,
                            'Method': self.downloadFile,
                            'Parameter': ['self.ASTEROIDS_MPC5000',
                                          'self.TARGET_DIR + self.ASTEROIDS_FILE'],
                            'Checkbox': self.app.ui.checkAsteroids
                        }
                    ]
                },
            'ASTEROIDS_NEA':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_downloadAsteroidsNEA,
                            'Method': self.downloadFile,
                            'Parameter': ['self.ASTEROIDS_NEA',
                                          'self.TARGET_DIR + self.ASTEROIDS_FILE'],
                            'Checkbox': self.app.ui.checkAsteroids
                        }
                    ]
                },
            'ASTEROIDS_PHA':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_downloadAsteroidsPHA,
                            'Method': self.downloadFile,
                            'Parameter': ['self.ASTEROIDS_PHA',
                                          'self.TARGET_DIR + self.ASTEROIDS_FILE'],
                            'Checkbox': self.app.ui.checkAsteroids
                        }
                    ]
                },
            'ASTEROIDS_TNO':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_downloadAsteroidsTNO,
                            'Method': self.downloadFile,
                            'Parameter': ['self.ASTEROIDS_TNO',
                                          'self.TARGET_DIR + self.ASTEROIDS_FILE'],
                            'Checkbox': self.app.ui.checkAsteroids
                        }]
                },
            'EARTHROTATION':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_downloadEarthrotation,
                            'Method': self.downloadFile,
                            'Parameter': ['self.UTC_1',
                                          'self.TARGET_DIR + self.UTC_1_FILE']
                        },
                        {
                            'Button': self.app.ui.btn_downloadEarthrotation,
                            'Method': self.downloadFile,
                            'Parameter': ['self.UTC_2',
                                          'self.TARGET_DIR + self.UTC_2_FILE'],
                            'Checkbox': self.app.ui.checkEarthrotation
                        }
                    ]
                },
            'ALL':
                {
                    'Worker': [
                        {
                            'Button': self.app.ui.btn_downloadEarthrotation,
                            'Method': self.downloadFile,
                            'Parameter': ['self.UTC_1',
                                          'self.TARGET_DIR + self.UTC_1_FILE']
                        },
                        {
                            'Button': self.app.ui.btn_downloadEarthrotation,
                            'Method': self.downloadFile,
                            'Parameter': ['self.UTC_2',
                                          'self.TARGET_DIR + self.UTC_2_FILE'],
                            'Checkbox': self.app.ui.checkEarthrotation
                        },
                        {
                            'Button': self.app.ui.btn_downloadSpacestations,
                            'Method': self.downloadFile,
                            'Parameter': ['self.SPACESTATIONS',
                                          'self.TARGET_DIR + self.SPACESTATIONS_FILE'],
                            'Checkbox': self.app.ui.checkTLE
                        },
                        {
                            'Button': self.app.ui.btn_downloadSatbrighest,
                            'Method': self.downloadFile,
                            'Parameter': ['self.SATBRIGHTEST',
                                          'self.TARGET_DIR + self.SATBRIGHTEST_FILE'],
                            'Checkbox': self.app.ui.checkTLE
                        },
                        {
                            'Button': self.app.ui.btn_downloadComets,
                            'Method': self.downloadFile,
                            'Parameter': ['self.COMETS',
                                          'self.TARGET_DIR + self.COMETS_FILE'],
                            'Checkbox': self.app.ui.checkComets
                        },
                        {
                            'Button': self.app.ui.btn_downloadAsteroidsMPC5000,
                            'Method': self.downloadFile,
                            'Parameter': ['self.ASTEROIDS_MPC5000',
                                          'self.TARGET_DIR + self.ASTEROIDS_FILE'],
                            'Checkbox': self.app.ui.checkAsteroids
                        }
                    ]
                }
            }

        self.checkApplication()
        self.TARGET_DIR = self.appInstallPath
        if self.TARGET_DIR == '':
            self.TARGET_DIR = os.getcwd()+'/config/'
        # signal slot
        self.app.ui.btn_downloadEarthrotation.clicked.connect(lambda: self.commandDispatcherQueue.put('EARTHROTATION'))
        self.app.ui.btn_downloadSpacestations.clicked.connect(lambda: self.commandDispatcherQueue.put('SPACESTATIONS'))
        self.app.ui.btn_downloadSatbrighest.clicked.connect(lambda: self.commandDispatcherQueue.put('SATBRIGHTEST'))
        self.app.ui.btn_downloadAsteroidsMPC5000.clicked.connect(lambda: self.commandDispatcherQueue.put('ASTEROIDS_MPC5000'))
        self.app.ui.btn_downloadAsteroidsNEA.clicked.connect(lambda: self.commandDispatcherQueue.put('ASTEROIDS_NEA'))
        self.app.ui.btn_downloadAsteroidsPHA.clicked.connect(lambda: self.commandDispatcherQueue.put('ASTEROIDS_PHA'))
        self.app.ui.btn_downloadAsteroidsTNO.clicked.connect(lambda: self.commandDispatcherQueue.put('ASTEROIDS_TNO'))
        self.app.ui.btn_downloadComets.clicked.connect(lambda: self.commandDispatcherQueue.put('COMETS'))
        self.app.ui.btn_downloadAll.clicked.connect(lambda: self.commandDispatcherQueue.put('ALL'))
        self.app.ui.btn_uploadMount.clicked.connect(lambda: self.commandDispatcherQueue.put('UPLOADMOUNT'))

    def initConfig(self):
        try:
            if 'FilterExpressionMPC' in self.app.config:
                self.app.ui.le_filterExpressionMPC.setText(self.app.config['FilterExpressionMPC'])
            if 'CheckFilterMPC' in self.app.config:
                self.app.ui.checkFilterMPC.setChecked(self.app.config['CheckFilterMPC'])
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['CheckFilterMPC'] = self.app.ui.checkFilterMPC.isChecked()
        self.app.config['FilterExpressionMPC'] = self.app.ui.le_filterExpressionMPC.text()

    def checkApplication(self):
        self.appAvailable, self.appName, self.appInstallPath = self.app.checkRegistrationKeys('10micron QCI')
        if self.appAvailable:
            self.app.messageQueue.put('Found: {0}\n'.format(self.appName))
            self.logger.info('Name: {0}, Path: {1}'.format(self.appName, self.appInstallPath))
        else:
            self.logger.info('Application 10micron Updater  not found on computer')

    def run(self):
        self.logger.info('automation started')
        # a running thread is shown with variable isRunning = True. This thread should hav it's own event loop.
        self.mutexIsRunning.lock()
        if not self.isRunning:
            self.isRunning = True
        self.mutexIsRunning.unlock()
        self.signalDestruct.connect(self.destruct, type=PyQt5.QtCore.Qt.BlockingQueuedConnection)
        self.cycleTimer = PyQt5.QtCore.QTimer(self)
        self.cycleTimer.setSingleShot(False)
        self.cycleTimer.timeout.connect(self.doCommand)
        self.cycleTimer.start(self.CYCLE)

    def stop(self):
        self.mutexIsRunning.lock()
        if self.isRunning:
            self.isRunning = False
            self.signalDestruct.emit()
            self.thread.quit()
            self.thread.wait()
        self.mutexIsRunning.unlock()
        self.logger.info('automation stopped')

    @PyQt5.QtCore.pyqtSlot()
    def destruct(self):
        self.cycleTimer.stop()
        self.signalDestruct.disconnect(self.destruct)

    def doCommand(self):
        if not self.commandDispatcherQueue.empty():
            command = self.commandDispatcherQueue.get()
            self.commandDispatcher(command)

    def commandDispatcher(self, command):
        # if we have a command in dispatcher
        if command in self.commandDispatch:
            # running through all necessary commands
            for work in self.commandDispatch[command]['Worker']:
                # if we want to color a button, which one
                if 'Button' in work:
                    work['Button'].setProperty('running', True)
                    work['Button'].style().unpolish(work['Button'])
                    work['Button'].style().polish(work['Button'])
                if 'Parameter' in work:
                    parameter = []
                    for p in work['Parameter']:
                        parameter.append(eval(p))
                    work['Method'](*parameter)
                else:
                    work['Method']()
                if 'Checkbox' in work:
                    work['Checkbox'].setChecked(True)
                if 'Button' in work:
                    work['Button'].setProperty('running', False)
                    work['Button'].style().unpolish(work['Button'])
                    work['Button'].style().polish(work['Button'])

    def filterFileMPC(self, directory, filename, expression, start, end):
        numberEntry = 0
        with open(directory + filename, 'r') as inFile, open(directory + 'filter.mpc', 'w') as outFile:
            for line in inFile:
                searchExp = expression.split(',')
                for exp in searchExp:
                    if line.find(exp, start, end) != -1:
                        outFile.write(line)
                        numberEntry += 1
        if numberEntry == 0:
            return False
        else:
            self.app.messageQueue.put('Found {0} target(s) in MPC file: {1}\n'.format(numberEntry, filename))
            self.logger.info('Found {0} target(s) in MPC file: {1}!'.format(numberEntry, filename))
            return True

    def downloadFile(self, url, filename):
        try:
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                numberOfChunks = 0
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(128):
                        numberOfChunks += 1
                        f.write(chunk)
            self.app.messageQueue.put('Downloaded {0} Bytes\n'.format(128 * numberOfChunks))
        except Exception as e:
            self.logger.error('Download of {0} failed, error{1}'.format(url, e))
            self.app.messageQueue.put('#BRDownload Error {0}\n'.format(e))
        return

    def uploadMount(self):
        actual_work_dir = ''
        try:
            actual_work_dir = os.getcwd()
            os.chdir(os.path.dirname(self.appInstallPath))
            app = Application(backend='win32')
            app.start(self.appInstallPath + self.appExe)
            # timings.Timings.Slow()
        except application.AppStartError:
            self.logger.error('Failed to start updater, please check!')
            self.app.messageQueue.put('#BRFailed to start updater, please check\n')
            os.chdir(actual_work_dir)
            return
        try:
            dialog = timings.WaitUntilPasses(2, 0.2, lambda: findwindows.find_windows(title='GmQCIv2', class_name='#32770')[0])
            winOK = app.window_(handle=dialog)
            winOK['OK'].click()
        except timings.TimeoutError as e:
            self.logger.warning('No invalid floating point windows occurred - moving forward')
        except Exception as e:
            self.logger.error('error{0}'.format(e))
        finally:
            pass
        try:
            win = app['10 micron control box update']                                                                       # link handle
            win['next'].click()                                                                                             # accept next
            win['next'].click()                                                                                             # go upload select page
            ButtonWrapper(win['Control box firmware']).UncheckByClick()                                                       # no firmware updates
        except Exception as e:
            self.logger.error('error{0}'.format(e))
            self.app.messageQueue.put('#BRError in starting 10micron updater, please check\n')
            os.chdir(actual_work_dir)
            return
        ButtonWrapper(win['Orbital parameters of comets']).UncheckByClick()
        ButtonWrapper(win['Orbital parameters of asteroids']).UncheckByClick()
        ButtonWrapper(win['Orbital parameters of satellites']).UncheckByClick()
        ButtonWrapper(win['UTC / Earth rotation data']).UncheckByClick()
        try:
            uploadNecessary = False
            if self.app.ui.checkComets.isChecked():
                ButtonWrapper(win['Orbital parameters of comets']).CheckByClick()
                win['Edit...4'].click()
                popup = app['Comet orbits']
                popup['MPC file'].click()
                filedialog = app[self.OPENDIALOG]
                if self.app.ui.checkFilterMPC.isChecked():
                    if self.filterFileMPC(self.TARGET_DIR, self.COMETS_FILE, self.app.ui.le_filterExpressionMPC.text(), self.COMETS_START, self.COMETS_END):
                        uploadNecessary = True
                    EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + 'filter.mpc')                               # filename box
                else:
                    uploadNecessary = True
                    EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.COMETS_FILE)                           # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                popup['Close'].click()
            else:
                ButtonWrapper(win['Orbital parameters of comets']).UncheckByClick()
            if self.app.ui.checkAsteroids.isChecked():
                ButtonWrapper(win['Orbital parameters of asteroids']).CheckByClick()
                win['Edit...3'].click()
                popup = app['Asteroid orbits']
                popup['MPC file'].click()
                filedialog = app[self.OPENDIALOG]
                if self.app.ui.checkFilterMPC.isChecked():
                    if self.filterFileMPC(self.TARGET_DIR, self.ASTEROIDS_FILE, self.app.ui.le_filterExpressionMPC.text(), self.ASTEROIDS_START, self.ASTEROIDS_END):
                        uploadNecessary = True
                    EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + 'filter.mpc')
                else:
                    uploadNecessary = True
                    EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.ASTEROIDS_FILE)                        # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                popup['Close'].click()
            else:
                ButtonWrapper(win['Orbital parameters of asteroids']).UncheckByClick()
            if self.app.ui.checkTLE.isChecked():
                ButtonWrapper(win['Orbital parameters of satellites']).CheckByClick()
                win['Edit...2'].click()
                popup = app['Satellites orbits']
                popup['Load from file'].click()
                filedialog = app[self.OPENDIALOG]
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.SATBRIGHTEST_FILE)                         # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                popup['Close'].click()
                uploadNecessary = True
            else:
                ButtonWrapper(win['Orbital parameters of satellites']).UncheckByClick()
            if self.app.ui.checkTLE.isChecked():
                ButtonWrapper(win['Orbital parameters of satellites']).CheckByClick()
                win['Edit...2'].click()
                popup = app['Satellites orbits']
                popup['Load from file'].click()
                filedialog = app[self.OPENDIALOG]
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.SPACESTATIONS_FILE)                        # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                popup['Close'].click()
                uploadNecessary = True
            else:
                ButtonWrapper(win['Orbital parameters of satellites']).UncheckByClick()
            if self.app.ui.checkEarthrotation.isChecked():
                ButtonWrapper(win['UTC / Earth rotation data']).CheckByClick()
                win['Edit...1'].click()
                popup = app['UTC / Earth rotation data']
                popup['Import files...'].click()
                filedialog = app['Open finals data']
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.UTC_1_FILE)                                # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                filedialog = app['Open tai-utc.dat']
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.UTC_2_FILE)                                # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                fileOK = app['UTC data']
                fileOK['OK'].click()
                uploadNecessary = True
            else:
                ButtonWrapper(win['UTC / Earth rotation data']).UncheckByClick()
        except Exception as e:
            self.logger.error('error{0}'.format(e))
            self.app.messageQueue.put('#BRError in choosing upload files, please check 10micron updater\n')
            os.chdir(actual_work_dir)
            return
        if self.app.workerMountDispatcher.mountStatus['Once']:
            self.app.messageQueue.put('Upload only possible with connected mount !')
            uploadNecessary = False
        if uploadNecessary:
            try:
                win['next'].click()
                win['next'].click()
                win['Update Now'].click()
            except Exception as e:
                self.logger.error('error{0}'.format(e))
                self.app.messageQueue.put('#BRError in uploading files, please check 10micron updater\n')
                os.chdir(actual_work_dir)
                return
            try:
                dialog = timings.WaitUntilPasses(60, 0.5, lambda: findwindows.find_windows(title='Update completed', class_name='#32770')[0])
                winOK = app.window_(handle=dialog)
                winOK['OK'].click()
            except Exception as e:
                self.logger.error('error{0}'.format(e))
                self.app.messageQueue.put('#BRError in closing 10micron updater, please check\n')
                os.chdir(actual_work_dir)
                return
        else:
            try:
                win['Cancel'].click()
                winOK = app['Exit updater']
                winOK['Yes'].click()
            except Exception as e:
                self.logger.error('error{0}'.format(e))
                self.app.messageQueue.put('#BRError in closing Updater, please check\n')
                os.chdir(actual_work_dir)
                return


if __name__ == "__main__":
    pass
