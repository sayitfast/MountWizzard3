import logging
import json
import socket
import timeit
from support.mwcamera import MWCamera
# windows automation
from pywinauto import Application, timings, findwindows, application


class TheSkyX(MWCamera):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(TheSkyX, self).__init__(app)
        self.host = '127.0.0.1'
        self.port = 3040
        self.responseSuccess = '|No error. Error = 0.'
        self.appExe = 'TheSkyX.exe'

    def checkAppInstall(self):
        self.appAvailable, self.appName, self.appInstallPath = self.app.checkRegistrationKeys('TheSkyX')
        self.appName = 'TheSkyX - Test Entry'
        if self.appAvailable:
            self.app.messageQueue.put('Found: {0}'.format(self.appName))
            self.logger.debug('checkApplicatio-> Name: {0}, Path: {1}'.format(self.appName, self.appInstallPath))
        else:
            self.app.ui.rb_cameraTSX.setVisible(False)
            self.app.ui.rb_cameraTSX.setCheckable(False)
            self.logger.error('checkApplicatio-> Application TheSkyX not found on computer')

    def checkAppStatus(self):
        try:
            tsxSocket = socket.socket()
            tsxSocket.connect((self.host, self.port))
            command = '/* Java Script */'
            command += 'var Out = "";'
            command += 'ccdsoftCamera.Asynchronous=0;'
            command += 'Out=ccdsoftCamera.ExposureStatus;'
            success, response = self.sendCommand(command)
            if response == 'Not Connected':
                self.appCameraConnected = False
            else:
                self.appCameraConnected = True
            self.appRunning = True
        except Exception as e:
            self.appRunning = False
            self.appConnected = False
            self.appCameraConnected = False
            self.logger.error('checkAppStatus -> error: {0}'.format(e))
        finally:
            pass

    def startApplication(self):
        self.appRunning = True
        try:
            a = findwindows.find_windows(title_re='^(.*?)(\\bTheSkyX\\b)(.*)$')
            if len(a) == 0:
                self.appRunning = False
            else:
                self.appRunning = True

        except Exception as e:
            self.logger.error('startApplicatio-> error{0}'.format(e))
        finally:
            pass
        if not self.appRunning:
            try:
                app = Application(backend='win32')
                app.start(self.appInstallPath + '\\' + self.appExe)
                self.appRunning = True
                self.logger.error('startApplicatio-> started TheSkyX')
            except application.AppStartError:
                self.logger.error('startApplicatio-> error starting application')
                self.app.messageQueue.put('Failed to start TheSkyX!')
                self.appRunning = False
            finally:
                pass

    def connectApplication(self):
        if self.appRunning:
            self.appConnected = True

    def disconnectApplication(self):
        if self.appRunning:
            self.appConnected = False

    def connectCamera(self):
        try:
            tsxSocket = socket.socket()
            tsxSocket.connect((self.host, self.port))
            command = '/* Java Script */ '
            command += 'ccdsoftCamera.Connect();'
            self.appCameraConnected, response = self.sendCommand(command)
        except Exception as e:
            self.logger.error('connectCamera  -> error: {0}'.format(e))
            self.appCameraConnected = False
        finally:
            # noinspection PyUnboundLocalVariable
            tsxSocket.close()

    def disconnectCamera(self):
        try:
            tsxSocket = socket.socket()
            tsxSocket.connect((self.host, self.port))
            command = '/* Java Script */ '
            command += 'ccdsoftCamera.Disconnect();'
            self.sendCommand(command)
            self.appCameraConnected = False
        except Exception as e:
            self.logger.error('disconnectCamer-> error: {0}'.format(e))
        finally:
            # noinspection PyUnboundLocalVariable
            tsxSocket.close()

    def sendCommand(self, command):
        try:
            tsxSocket = socket.socket()
            tsxSocket.connect((self.host, self.port))
            tsxSocket.send(command.encode())
            response = str(tsxSocket.recv(1024).decode())

            if response.endswith(self.responseSuccess):
                response = response.replace(self.responseSuccess, '')
                return True, response
            else:
                return False, response
        except Exception as e:
            self.logger.error('sendCommand    -> error: {0}'.format(e))
            return False, format(e)
        finally:
            # noinspection PyUnboundLocalVariable
            tsxSocket.close()

    def solveImage(self, modelData):
        if modelData['blind']:
            self.logger.warning('Blind mode is not supported. TheSkyX allows to switch to All Sky Image Link by scripting. Please, enable All Sky Image Link manually in TheSkyX')

        try:
            command = '/* Java Script */'
            command += 'ccdsoftCamera.Asynchronous=0;'
            command += 'ImageLink.pathToFITS="' + str(modelData['imagepath']).replace('\\', '/') + '";'
            if modelData['scaleHint']:
                command += 'ImageLink.unknownScale=0;'
                command += 'ImageLink.scale=' + str(modelData['scaleHint']) + ';'
            else:
                command += 'ImageLink.unknownScale=1;'
                command += 'ImageLink.scale=2;'
            command += 'ImageLink.execute();'
            command += 'Out=String(\'{"succeeded":"\'+ImageLinkResults.succeeded+\'","imageCenterRAJ2000":"\'+ImageLinkResults.imageCenterRAJ2000+\'","imageCenterDecJ2000":"\'+ImageLinkResults.imageCenterDecJ2000+\'","imageScale":"\'+ImageLinkResults.imageScale+\'","imagePositionAngle":"\'+ImageLinkResults.imagePositionAngle+\'"}\');'

            startTime = timeit.default_timer()
            success, response = self.sendCommand(command)
            solveTime = timeit.default_timer() - startTime

            if success:
                captureResponse = json.loads(response)

                if captureResponse['succeeded'] == '1':
                    modelData['dec_sol'] = float(captureResponse['imageCenterDecJ2000'])
                    modelData['ra_sol'] = float(captureResponse['imageCenterRAJ2000'])
                    modelData['scale'] = float(captureResponse['imageScale'])
                    modelData['angle'] = float(captureResponse['imagePositionAngle'])
                    modelData['timeTS'] = solveTime
                    return True, 'Solved', modelData
                else:
                    return False, 'Unsolved', modelData
            else:
                return False, 'Request failed', modelData
        except Exception as e:
            self.logger.error('TXGetSolvedImag-> error: {0}'.format(e))
            return False, 'Request failed', modelData

    def getImage(self, modelData):
        # TODO: how is TSX dealing with ISO settings for DSLR?

        try:
            command = '/* Java Script */'
            command += 'ccdsoftCamera.Asynchronous=0;'
            if modelData['canSubframe']:
                command += 'ccdsoftCamera.Subframe=1;'
                command += 'ccdsoftCamera.SubframeLeft=' + str(modelData['offX']) + ';'
                command += 'ccdsoftCamera.SubframeTop=' + str(modelData['offY']) + ';'
                command += 'ccdsoftCamera.SubframeRight=' + str(modelData['offX'] + modelData['sizeX']) + ';'
                command += 'ccdsoftCamera.SubframeBottom=' + str(modelData['offY'] + modelData['sizeY']) + ';'
            else:
                command += 'ccdsoftCamera.Subframe=0;'

            if modelData['speed'] == 'HiSpeed':
                command += 'ccdsoftCamera.setPropStr("m_csExCameraMode", "Fast Image Download");'
            else:
                command += 'ccdsoftCamera.setPropStr("m_csExCameraMode", "High Image Quality");'

            command += 'ccdsoftCamera.BinX='+str(modelData['binning'])+';'
            command += 'ccdsoftCamera.BinY='+str(modelData['binning'])+';'
            command += 'ccdsoftCamera.ExposureTime='+str(modelData['exposure'])+';'
            command += 'ccdsoftCamera.AutoSavePath="'+str(modelData['base_dir_images'])+'";'
            command += 'ccdsoftCamera.AutoSaveOn=1;'
            command += 'ccdsoftCamera.Frame="cdLight";'
            command += 'ccdsoftCamera.TakeImage();'
            command += 'var Out = "";'
            command += 'Out=ccdsoftCamera.LastImageFileName;'
            success, response = self.sendCommand(command)

            modelData['imagepath'] = response

            return success, response, modelData
        except Exception as e:
            self.logger.error('TXCaptureImage -> error: {0}'.format(e))
            return False, 'Request failed', ''

    def getCameraStatus(self):
        try:
            command = '/* Java Script */'
            command += 'var Out = "";'
            command += 'ccdsoftCamera.Asynchronous=0;'
            command += 'Out=ccdsoftCamera.ExposureStatus;'
            success, response = self.sendCommand(command)
            if response == 'Not Connected':
                response = 'DISCONNECTED'
            elif response == 'Ready':
                response = 'IDLE'
            elif 'Exposing' in response:
                response = 'CAPTURING'
            self.cameraStatus = response
        except Exception as e:
            self.logger.error('TXGetDeviceStat-> error: {0}'.format(e))
        finally:
            pass

    def getCameraProps(self):
        # TODO: Get the chance to implement subframe on / off if a camera doesn't support this
        # TODO: Gain setting in CMOS Cameras necessary ?
        try:
            command = '/* Java Script */'
            command += 'var Out = "";'
            command += 'ccdsoftCamera.Asynchronous=0;'
            command += 'Out=String(\'{"WidthInPixels":"\'+ccdsoftCamera.WidthInPixels+\'","HeightInPixels":"\'+ccdsoftCamera.HeightInPixels+\'"}\');'
            success, response = self.sendCommand(command)
            captureResponse = json.loads(response)
            return success, '', int(captureResponse['WidthInPixels']), int(captureResponse['HeightInPixels']), True, 'Not Set'
        except Exception as e:
            self.logger.error('TXGetCameraProp-> error: {0}'.format(e))
            return False, 'Request failed', '', '', '', ''
