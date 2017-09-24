import logging
import time
from PyQt5 import QtCore
# for data storing
from queue import Queue


class Slewpoint(QtCore.QObject):

    queuePoint = Queue()
    signalSlewing = QtCore.pyqtSignal(name='slew')

    def __init__(self, main):
        QtCore.QThread.__init__(self)
        self.main = main
        self.stopped = 0

        self.signalSlewing.connect(self.slewing)

    @QtCore.pyqtSlot()
    def run(self):
        pass

    @QtCore.pyqtSlot()
    def stop(self):
        self.stopped = 1

    @QtCore.pyqtSlot()
    def slewing(self):
        if not self.queuePoint.empty():
            number = self.queuePoint.get()
            time.sleep(0.1)
            print('Start Slewing to Point {0}'.format(number))
            time.sleep(5)
            print('Settling of point {0}'.format(number))
            time.sleep(0.5)
            print('Tracking of point {0}'.format(number))
            self.main.workerImage.queueImage.put(number)
            self.main.workerImage.signalImaging.emit()


class Image(QtCore.QObject):

    queueImage = Queue()
    signalImaging = QtCore.pyqtSignal(name='image')

    def __init__(self, main):
        QtCore.QThread.__init__(self)
        self.main = main
        self.stopped = 0

        self.signalImaging.connect(self.imaging)

    @QtCore.pyqtSlot()
    def run(self):
        pass

    @QtCore.pyqtSlot()
    def stop(self):
        self.stopped = 1

    @QtCore.pyqtSlot()
    def imaging(self):
        if not self.queueImage.empty():
            number = self.queueImage.get()
            time.sleep(0.5)
            print('Start Integration of point {0}'.format(number))
            time.sleep(5)
            print('Download of point {0}'.format(number))
            # self.main.workerSlewpoint.signalSlewing.emit()
            time.sleep(2)
            print('Store Image of point {0}'.format(number))
            time.sleep(0.2)
            self.main.workerPlatesolve.queuePlatesolve.put(number)
            self.main.workerPlatesolve.signalPlatesolve.emit()


class Platesolve(QtCore.QObject):

    queuePlatesolve = Queue()
    signalPlatesolve = QtCore.pyqtSignal(name='plate')

    def __init__(self, main):
        QtCore.QThread.__init__(self)
        self.main = main
        self.stopped = 0

        self.signalPlatesolve.connect(self.platesolving)

    @QtCore.pyqtSlot()
    def run(self):
        pass

    @QtCore.pyqtSlot()
    def stop(self):
        self.stopped = 1

    @QtCore.pyqtSlot()
    def platesolving(self):
        if not self.queuePlatesolve.empty():
            number = self.queuePlatesolve.get()
            print('Start Platesolve of point {0}'.format(number))
            time.sleep(5)
            print('Got coordinates of point {0}'.format(number))
            time.sleep(0.1)
            self.main.workerSlewpoint.signalSlewing.emit()


class NEWMODEL:
    logger = logging.getLogger(__name__)

    def __init__(self):

        self.workerSlewpoint = Slewpoint(self)
        self.threadSlewpoint = QtCore.QThread()
        self.workerSlewpoint.moveToThread(self.threadSlewpoint)
        self.threadSlewpoint.start()

        self.workerImage = Image(self)
        self.threadImage = QtCore.QThread()
        self.workerImage.moveToThread(self.threadImage)
        self.threadImage.start()

        self.workerPlatesolve = Platesolve(self)
        self.threadPlatesolve = QtCore.QThread()
        self.workerPlatesolve.moveToThread(self.threadPlatesolve)
        self.threadPlatesolve.start()

        # mapping the signals:
        for i in range(1, 10):
            self.workerSlewpoint.queuePoint.put(i)
        self.workerSlewpoint.signalSlewing.emit()          # start process

    def stop(self):
        print('stop threads')
        self.workerSlewpoint.stop()
        self.threadSlewpoint.quit()
        self.threadSlewpoint.wait()

        self.workerPlatesolve.stop()
        self.threadPlatesolve.quit()
        self.threadPlatesolve.wait()
