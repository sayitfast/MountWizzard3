import logging
from urllib import request
import json
import socket


class TheSkyX:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 3040
        self.responseSuccess = '|No error. Error = 0.'

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
            tsxSocket.close()

    def checkConnection(self):
        try:
            tsxSocket = socket.socket()
            tsxSocket.connect((self.host, self.port))
            connected = True
        except Exception as e:
            self.logger.error('checkConnection-> error: {0}'.format(e))
            connected = False
        finally:
            tsxSocket.close()
            if connected:
                if self.SgGetDeviceStatus('Camera'):
                    if self.SgGetDeviceStatus('PlateSolver'):
                        return True, 'Camera and Solver OK'
                    else:
                        return False, 'PlateSolver not available !'
                else:
                    return False, 'Camera not available !'
            return False, 'SGPro server not running'

    @staticmethod
    def SgEnumerateDevice(self, device):
        return '', False, 'Not implemented'

    def SgCaptureImage(self, binningMode=1, exposureLength=1, gain=None, iso=None, speed=None, frameType=None,
                       filename=None, path=None, useSubframe=False, posX=0, posY=0, width=1, height=1):
        if frameType == 'Light':
            frameType = 'cdLight'
        try:
            command = '/* Java Script */'
            command += 'ccdsoftCamera.Asynchronous=0;'
            if useSubframe:
                command += 'ccdsoftCamera.Subframe=1;'
                command += 'ccdsoftCamera.SubframeLeft=' + str(posX) + ';'
                command += 'ccdsoftCamera.SubframeTop=' + str(posY) + ';'
                command += 'ccdsoftCamera.SubframeRight=' + str(posX + height) + ';'
                command += 'ccdsoftCamera.SubframeBottom=' + str(posY + width) + ';'
            else:
                command += 'ccdsoftCamera.Subframe=0;'
            command += 'ccdsoftCamera.BinX='+str(binningMode)+';'
            command += 'ccdsoftCamera.BinY='+str(binningMode)+';'
            command += 'ccdsoftCamera.ExposureTime='+str(exposureLength)+';'
            command += 'ccdsoftCamera.AutoSavePath="'+path+'";'
            command += 'ccdsoftCamera.AutoSaveOn=1;'
            command += 'ccdsoftCamera.Frame="'+frameType+'";'
            command += 'ccdsoftCamera.TakeImage();'
            success, response = self.sendCommand(command)
            return success, response, '00000000000000000000000000000000'
        except Exception as e:
            self.logger.error('TXCaptureImage -> error: {0}'.format(e))
            return False, 'Request failed', ''

    def SgSolveImage(self, path, raHint=None, decHint=None, scaleHint=None, blindSolve=False, useFitsHeaders=False):
        try:
            command = '/* Java Script */'
            command += 'ccdsoftCamera.Asynchronous=1;'
            command += 'ImageLink.pathToFITS="' + path.replace('\\', '/') + '";'
            if scaleHint == None:
                command += 'ImageLink.unknownScale=1;'
                command += 'ImageLink.scale=2;'
            else:
                command += 'ImageLink.unknownScale=0;'
                command += 'ImageLink.scale=' + str(scaleHint) + ';'
            command += 'ImageLink.execute();'
            command += 'var Out = "";'
            command += 'Out=ImageLinkResults.succeeded'
            success, response = self.sendCommand(command)
            return success, response, '00000000000000000000000000000000'
        except Exception as e:
            self.logger.error('TheSkyX SgSolveImage -> error: {0}'.format(e))
            return False, 'Request failed'

    def SgGetSolvedImageData(self, guid):
        try:
            command = '/* Java Script */'
            command += 'ccdsoftCamera.Asynchronous=0;'
            command += 'var Out = "";'
            command += 'Out=String(\'{"succeeded":"\'+ImageLinkResults.succeeded+\'","imageCenterRAJ2000":"\'+ImageLinkResults.imageCenterRAJ2000+\'","imageCenterDecJ2000":"\'+ImageLinkResults.imageCenterDecJ2000+\'","imageScale":"\'+ImageLinkResults.imageScale+\'","imagePositionAngle":"\'+ImageLinkResults.imagePositionAngle+\'"}\');'
            success, response = self.sendCommand(command)
            if success:
                captureResponse = json.loads(response)
                if captureResponse['succeeded'] == '1':
                    success = True
                else:
                    success = False
                return success, 'succeeded', captureResponse['imageCenterRAJ2000'], captureResponse['imageCenterDecJ2000'], captureResponse['imageScale'], captureResponse['imagePositionAngle'], '1'
            else:
                return False, 'Request failed', '', '', '', '', ''
        except Exception as e:
            self.logger.error('TXGetSolvedImag-> error: {0}'.format(e))
            return False, 'Request failed', '', '', '', '', ''

    def SgGetImagePath(self, guid):
        try:
            command = '/* Java Script */'
            command += 'var Out = "";'
            command += 'Out=ccdsoftCamera.LastImageFileName;'
            success, response = self.sendCommand(command)
            return success, response
        except Exception as e:
            self.logger.error('TXGetImagePath -> error: {0}'.format(e))
            return False, 'Request failed'

    def SgGetDeviceStatus(self, device):
        if device == 'Camera':
            # TODO: actually a not connected camera is to seen
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
                return success, response
            except Exception as e:
                self.logger.error('TXGetDeviceStat-> error: {0}'.format(e))
                return False, 'Request failed'
        elif device == 'PlateSolver':
            # TODO: we need at least the check if a plate solver is available
            return True, 'No check currently'
        else:
            return False, 'Device has no status'

    def SgGetCameraProps(self):
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

if __name__ == "__main__":

    cam = TheSkyX()
    suc, mes, x, y, can, gain = cam.SgGetCameraProps()
    print(suc, mes, x, y, can, gain)
    suc, mes, guid = cam.SgCaptureImage(binningMode=1, exposureLength=1, gain=gain, iso=None, speed=None, frameType='cdLight', filename=None, path='c:/temp', useSubframe=False, posX=0, posY=0, width=1, height=1)
    while True:
        suc, path = cam.SgGetImagePath(guid)
        if suc:
            break
    print(suc, path)
    suc, mes, guid = cam.SgSolveImage(path=path, raHint=None, decHint=None, scaleHint=3.7, blindSolve=False, useFitsHeaders=False)
    print(suc, mes, guid)
    suc, mes, ra, dec, scale, angle, time = cam.SgGetSolvedImageData(guid)
    print(suc, mes, ra, dec, scale, angle, time)
