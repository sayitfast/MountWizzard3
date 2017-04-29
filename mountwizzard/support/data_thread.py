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
import logging
from PyQt5 import QtCore
import time
import urllib.request as urllib2
import urllib.parse as urlparse


class Data(QtCore.QThread):
    logger = logging.getLogger(__name__)                                                                                    # get logger for  problems

    UTC_1 = 'http://maia.usno.navy.mil/ser7/finals.data'
    UTC_2 = 'http://maia.usno.navy.mil/ser7/tai-utc.dat'
    COMETS = 'http://www.minorplanetcenter.net/iau/MPCORB/CometEls.txt'
    ASTEROIDS = 'http://www.ap-i.net/pub/skychart/mpc/mpc5000.dat'
    SPACESTATIONS = 'http://www.celestrak.com/NORAD/elements/stations.txt'
    SATBRIGHTEST = 'http://www.celestrak.com/NORAD/elements/visual.txt'
    TARGET_DIR = os.getcwd() + '\\config\\'

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
                    self.downloadFile(self.SPACESTATIONS, self.TARGET_DIR + 'spacestations.tle')
                    self.app.ui.btn_downloadSpacestations.setStyleSheet(self.DEFAULT)
                elif command == 'SATBRIGHTEST':
                    self.app.ui.btn_downloadSatbrighest.setStyleSheet(self.BLUE)
                    self.downloadFile(self.SATBRIGHTEST, self.TARGET_DIR + 'satbrightest.tle')
                    self.app.ui.btn_downloadSatbrighest.setStyleSheet(self.DEFAULT)
                elif command == 'ASTEROIDS':
                    self.app.ui.btn_downloadAsteroids.setStyleSheet(self.BLUE)
                    self.downloadFile(self.ASTEROIDS, self.TARGET_DIR + 'asteroids.mpc')
                    self.app.ui.btn_downloadAsteroids.setStyleSheet(self.DEFAULT)
                elif command == 'COMETS':
                    self.app.ui.btn_downloadComets.setStyleSheet(self.BLUE)
                    self.downloadFile(self.COMETS, self.TARGET_DIR + 'comets.mpc')
                    self.app.ui.btn_downloadComets.setStyleSheet(self.DEFAULT)
                elif command == 'EARTHROTATION':
                    self.app.ui.btn_downloadEarthrotation.setStyleSheet(self.BLUE)
                    self.downloadFile(self.UTC_1, self.TARGET_DIR + 'finals.data')
                    self.downloadFile(self.UTC_2, self.TARGET_DIR + 'tai-utc.dat')
                    self.app.ui.btn_downloadEarthrotation.setStyleSheet(self.DEFAULT)
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


if __name__ == "__main__":

    from pywinauto import Application, timings, findwindows
    from pywinauto.controls.win32_controls import ButtonWrapper, EditWrapper

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




