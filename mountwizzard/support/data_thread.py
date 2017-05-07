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

# import basic stuff
import os
import sys
import logging
from PyQt5 import QtCore
import time
import urllib.request as urllib2
import urllib.parse as urlparse
# windows automation
from pywinauto import Application, timings, findwindows
from pywinauto.controls.win32_controls import ButtonWrapper, EditWrapper


class Data(QtCore.QThread):
    logger = logging.getLogger(__name__)                                                                                    # get logger for  problems

    UTC_1 = 'http://maia.usno.navy.mil/ser7/finals.data'
    UTC_2 = 'http://maia.usno.navy.mil/ser7/tai-utc.dat'
    COMETS = 'http://www.minorplanetcenter.net/iau/MPCORB/CometEls.txt'
    ASTEROIDS = 'http://www.ap-i.net/pub/skychart/mpc/mpc5000.dat'
    SPACESTATIONS = 'http://www.celestrak.com/NORAD/elements/stations.txt'
    SATBRIGHTEST = 'http://www.celestrak.com/NORAD/elements/visual.txt'
    TARGET_DIR = os.getcwd() + '\\config\\'
    COMETS_FILE = 'comets.mpc'
    ASTEROIDS_FILE = 'asteroids.mpc'
    SPACESTATIONS_FILE = 'spacestations.tle'
    SATBRIGHTEST_FILE = 'satbrightest.tle'
    UTC_1_FILE = 'finals.data'
    UTC_2_FILE = 'tai-utc.dat'
    BLUE = 'background-color: rgb(42, 130, 218)'
    RED = 'background-color: red;'
    DEFAULT = 'background-color: rgb(32,32,32); color: rgb(192,192,192)'

    def __init__(self, app):
        super().__init__()
        self.app = app

    def run(self):                                                                                                          # runnable for doing the work
        while True:                                                                                                         # main loop for stick thread
            if not self.app.commandDataQueue.empty():
                command = self.app.commandDataQueue.get()
                if command == 'SPACESTATIONS':
                    self.app.ui.btn_downloadSpacestations.setStyleSheet(self.BLUE)
                    self.downloadFile(self.SPACESTATIONS, self.TARGET_DIR + self.SPACESTATIONS_FILE)
                    self.app.ui.btn_downloadSpacestations.setStyleSheet(self.DEFAULT)
                elif command == 'SATBRIGHTEST':
                    self.app.ui.btn_downloadSatbrighest.setStyleSheet(self.BLUE)
                    self.downloadFile(self.SATBRIGHTEST, self.TARGET_DIR + self.SATBRIGHTEST_FILE)
                    self.app.ui.btn_downloadSatbrighest.setStyleSheet(self.DEFAULT)
                elif command == 'ASTEROIDS':
                    self.app.ui.btn_downloadAsteroids.setStyleSheet(self.BLUE)
                    self.downloadFile(self.ASTEROIDS, self.TARGET_DIR + self.ASTEROIDS_FILE)
                    self.app.ui.btn_downloadAsteroids.setStyleSheet(self.DEFAULT)
                elif command == 'COMETS':
                    self.app.ui.btn_downloadComets.setStyleSheet(self.BLUE)
                    self.downloadFile(self.COMETS, self.TARGET_DIR + self.COMETS_FILE)
                    self.app.ui.btn_downloadComets.setStyleSheet(self.DEFAULT)
                elif command == 'EARTHROTATION':
                    self.app.ui.btn_downloadEarthrotation.setStyleSheet(self.BLUE)
                    self.downloadFile(self.UTC_1, self.TARGET_DIR + self.UTC_1_FILE)
                    self.downloadFile(self.UTC_2, self.TARGET_DIR + self.UTC_2_FILE)
                    self.app.ui.btn_downloadEarthrotation.setStyleSheet(self.DEFAULT)
                elif command == 'ALL':
                    self.app.ui.btn_downloadAll.setStyleSheet(self.BLUE)
                    self.app.ui.btn_downloadEarthrotation.setStyleSheet(self.BLUE)
                    self.app.ui.btn_downloadSpacestations.setStyleSheet(self.BLUE)
                    self.app.ui.btn_downloadSatbrighest.setStyleSheet(self.BLUE)
                    self.app.ui.btn_downloadAsteroids.setStyleSheet(self.BLUE)
                    self.app.ui.btn_downloadComets.setStyleSheet(self.BLUE)
                    self.downloadFile(self.UTC_1, self.TARGET_DIR + self.UTC_1_FILE)
                    self.downloadFile(self.UTC_2, self.TARGET_DIR + self.UTC_2_FILE)
                    self.app.ui.btn_downloadEarthrotation.setStyleSheet(self.DEFAULT)
                    self.downloadFile(self.SPACESTATIONS, self.TARGET_DIR + self.SPACESTATIONS_FILE)
                    self.app.ui.btn_downloadSpacestations.setStyleSheet(self.DEFAULT)
                    self.downloadFile(self.SATBRIGHTEST, self.TARGET_DIR + self.SATBRIGHTEST_FILE)
                    self.app.ui.btn_downloadSatbrighest.setStyleSheet(self.DEFAULT)
                    self.downloadFile(self.ASTEROIDS, self.TARGET_DIR + self.ASTEROIDS_FILE)
                    self.app.ui.btn_downloadAsteroids.setStyleSheet(self.DEFAULT)
                    self.downloadFile(self.COMETS, self.TARGET_DIR + self.COMETS_FILE)
                    self.app.ui.btn_downloadComets.setStyleSheet(self.DEFAULT)
                    self.app.ui.btn_downloadAll.setStyleSheet(self.DEFAULT)
                elif command == 'UPLOADMOUNT':
                    self.app.ui.btn_uploadMount.setStyleSheet(self.BLUE)
                    self.uploadMount()
                    self.app.ui.btn_uploadMount.setStyleSheet(self.DEFAULT)
                else:
                    pass
            time.sleep(0.1)                                                                                                   # wait for the next cycle
        self.terminate()                                                                                                    # closing the thread at the end

    def __del__(self):                                                                                                      # remove thread
        self.wait()

    def getStatusFast(self):
        pass

    def getStatusMedium(self):
        self.logger.error('getStatusMedium-> error accessing weather ascom data: {}')

    def getStatusSlow(self):
        pass

    def getStatusOnce(self):
        pass

    def downloadFile(self, url, filename):
        try:
            u = urllib2.urlopen(url)
            scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
            with open(filename, 'wb') as f:
                meta = u.info()
                meta_func = meta.getheaders if hasattr(meta, 'getheaders') else meta.get_all
                meta_length = meta_func("Content-Length")
                file_size = None
                if meta_length:
                    file_size = int(meta_length[0])
                self.app.messageQueue.put('{0}'.format(url))
                file_size_dl = 0
                block_sz = 8192
                while True:
                    buffer = u.read(block_sz)
                    if not buffer:
                        break
                    file_size_dl += len(buffer)
                    f.write(buffer)
            self.app.messageQueue.put('Downloaded {0} Bytes'.format(file_size))
        except Exception as e:
            self.logger.error('downloadFile   -> Download of {0} failed, error{1}'.format(url, e))
            self.app.messageQueue.put('Download Error {0}'.format(e))
        return

    def uploadMount(self):
        if not os.path.isfile(self.app.ui.le_updaterFileName.text()):
            self.logger.error('uploadMount    -> no updater configured')
            self.app.messageQueue.put('No Path to Updater configured, please check!')
        app = Application(backend='win32')                                                                                  # backend win32 ist faster than uai
        app.start(self.app.ui.le_updaterFileName.text())                                                                    # start 10 micro updater
        timings.Timings.Slow()
        try:
            dialog = timings.WaitUntilPasses(2, 0.5, lambda: findwindows.find_windows(title='GmQCIv2', class_name='#32770')[0])
            winOK = app.window_(handle=dialog)
            winOK['OK'].click()
        except TimeoutError as e:
            self.logger.error('uploadMount    -> error{0}'.format(e))
            self.app.messageQueue.put('Error in starting 10micron updater, please check!')
        except Exception as e:
            pass
        finally:
            pass
        try:
            win = app['10 micron control box update']                                                                       # link handle
            win['next'].click()                                                                                             # accept next
            win['next'].click()                                                                                             # go upload select page
            ButtonWrapper(win['Control box firmware']).uncheck()                                                            # no firmware updates
        except Exception as e:
            self.logger.error('uploadMount    -> error{0}'.format(e))
            self.app.messageQueue.put('Error in starting 10micron updater, please check!')
            return
        ButtonWrapper(win['Orbital parameters of comets']).uncheck()
        ButtonWrapper(win['Orbital parameters of asteroids']).uncheck()
        ButtonWrapper(win['Orbital parameters of satellites']).uncheck()
        ButtonWrapper(win['UTC / Earth rotation data']).uncheck()
        try:
            uploadNecessary = False
            if self.app.ui.checkComets.isChecked():
                ButtonWrapper(win['Orbital parameters of comets']).check()
                win['Edit...4'].click()
                popup = app['Comet orbits']
                popup['MPC file'].click()
                filedialog = app['Öffnen']      # TODO: english version ?
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.COMETS_FILE)                               # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                popup['Close'].click()
                uploadNecessary = True
            else:
                ButtonWrapper(win['Orbital parameters of comets']).uncheck()
            if self.app.ui.checkAsteroids.isChecked():
                ButtonWrapper(win['Orbital parameters of asteroids']).check()
                win['Edit...3'].click()
                popup = app['Asteroid orbits']
                popup['MPC file'].click()
                filedialog = app['Öffnen']      # TODO: english version ?
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.ASTEROIDS_FILE)                            # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                popup['Close'].click()
                uploadNecessary = True
            else:
                ButtonWrapper(win['Orbital parameters of asteroids']).uncheck()
            if self.app.ui.checkSatellites.isChecked():
                ButtonWrapper(win['Orbital parameters of satellites']).check()
                win['Edit...2'].click()
                popup = app['Satellites orbits']
                popup['Load from file'].click()
                filedialog = app['Öffnen']      # TODO: english version ?
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.SATBRIGHTEST_FILE)                         # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                popup['Close'].click()
                uploadNecessary = True
            else:
                ButtonWrapper(win['Orbital parameters of satellites']).uncheck()
            if self.app.ui.checkSpacestations.isChecked():
                ButtonWrapper(win['Orbital parameters of satellites']).check()
                win['Edit...2'].click()
                popup = app['Satellites orbits']
                popup['Load from file'].click()
                filedialog = app['Öffnen']      # TODO: english version ?
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.SPACESTATIONS_FILE)                        # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                popup['Close'].click()
                uploadNecessary = True
            else:
                ButtonWrapper(win['Orbital parameters of satellites']).uncheck()
            if self.app.ui.checkEarthrotation.isChecked():
                ButtonWrapper(win['UTC / Earth rotation data']).check()
                win['Edit...1'].click()
                popup = app['UTC / Earth rotation data']
                popup['Import files...'].click()
                filedialog = app['Open finals data']      # TODO: english version ?
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.UTC_1_FILE)                               # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                filedialog = app['Open tai-utc.dat']      # TODO: english version ?
                EditWrapper(filedialog['Edit13']).SetText(self.TARGET_DIR + self.UTC_2_FILE)                               # filename box
                filedialog['Button16'].click()                                                                              # accept filename selection and proceed
                fileOK = app['UTC data']
                fileOK['OK'].click()
                uploadNecessary = True
            else:
                ButtonWrapper(win['UTC / Earth rotation data']).uncheck()
        except Exception as e:
            self.logger.error('uploadMount    -> error{0}'.format(e))
            self.app.messageQueue.put('Error in choosing upload files, please check 10micron updater!')
            return
        if uploadNecessary:
            try:
                win['next'].click()
                win['next'].click()
                win['Update Now'].click()
            except Exception as e:
                self.logger.error('uploadMount    -> error{0}'.format(e))
                self.app.messageQueue.put('Error in uploading files, please check 10micron updater!')
                return
            try:
                dialog = timings.WaitUntilPasses(60, 0.5, lambda: findwindows.find_windows(title='Update completed', class_name='#32770')[0])
                winOK = app.window_(handle=dialog)
                winOK['OK'].click()
            except Exception as e:
                self.logger.error('uploadMount    -> error{0}'.format(e))
                self.app.messageQueue.put('Error in closing 10micron updater, please check!')
                return
        else:
            try:
                win['Cancel'].click()
                winOK = app['Exit updater']
                winOK['Yes'].click()
            except Exception as e:
                self.logger.error('uploadMount    -> error{0}'.format(e))
                self.app.messageQueue.put('Error in closing Updater, please check!')
                return

if __name__ == "__main__":


    def find_executable(executable, path=None):
        """Find if 'executable' can be run. Looks for it in 'path'
        (string that lists directories separated by 'os.pathsep';
        defaults to os.environ['PATH']). Checks for all executable
        extensions. Returns full path or None if no command is found.
        """
        if path is None:
            path = os.environ['PATH']
        paths = path.split(os.pathsep)
        extlist = ['']
        pathext = os.environ['PATHEXT'].lower().split(os.pathsep)
        (base, ext) = os.path.splitext(executable)
        if ext.lower() not in pathext:
            extlist = pathext
        for ext in extlist:
            execname = executable + ext
            if os.path.isfile(execname):
                return execname
            else:
                for p in paths:
                    f = os.path.join(p, execname)
                    if os.path.isfile(f):
                        return f
        else:
            return None

    print(find_executable('GmQCIv2.exe', 'c:\\'))

    '''
    updater_file = 'C:/Program Files (x86)/10micron/Updater/GmQCIv2.exe'
    app = Application(backend='uia')
    app.start(updater_file)
    win = app['10 micron control box update']
    win['next'].click()
    win['next'].click()
    # print(win.print_control_identifiers())
    ButtonWrapper(win['Control box firmware']).uncheck()
    ButtonWrapper(win['Orbital parameters of comets']).check()
    ButtonWrapper(win['Orbital parameters of asteroids']).uncheck()
    ButtonWrapper(win['Orbital parameters of satellites']).uncheck()
    ButtonWrapper(win['UTC / Earth rotation data']).uncheck()
    win['Edit...4'].click()  # comets
    popup = app['Comet orbits']
    popup['MPC file'].click()

    filedialog = app['Öffnen']
    # print(filedialog.print_control_identifiers())
    file = 'c:\\Users\\mw\\Projects\\mountwizzard\\mountwizzard\\config\\comets.mpc'
    EditWrapper(filedialog['Edit13']).SetText(file)         # filename box
    filedialog['Button16'].click()                          # open dialog

    popup['Close'].click()
    win['next'].click()
    win['next'].click()

    win['Update Now'].click()

    # winOK = app.WindowsSpecification.Wait(title='Update completed', timeout=20, retry_interval=0.5)
    dialog = timings.WaitUntilPasses(20, 0.5, lambda: findwindows.find_windows(title='Update completed', class_name='#32770')[0])
    winOK = app.window_(handle=dialog)
    print(winOK)
    print(winOK['OK'])
    winOK['OK'].click()
    '''


