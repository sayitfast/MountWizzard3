import logging
from urllib import request
import json
import socket
import timeit


class TheSkyX:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 3040
        self.responseSuccess = '|No error. Error = 0.'
        self.connected = False
        self.cameraStatus = ''

    def connect(self):
        pass

    def disconnect(self):
        pass

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
            command = '/* Java Script */ '
            command += 'ccdsoftCamera.Connect();'
            self.connected, response = self.sendCommand(command)
        except Exception as e:
            self.logger.error('checkConnection-> error: {0}'.format(e))
            self.connected = False
        finally:
            tsxSocket.close()
            if self.connected:
                return True, 'Camera and Solver OK';
            else:
                return self.connected, 'Unable to connect camera';

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
        # TODO: how is TSX dealing with download speeds for CCD, who support this feature ?

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

if __name__ == "__main__":

    cam = TheSkyX()
    suc, mes, x, y, can, gain = cam.SgGetCameraProps()
    # print(suc, mes, x, y, can, gain)
    suc, mes, guid = cam.SgCaptureImage(binningMode=1, exposureLength=1, gain=gain, iso=None, speed=None, frameType='cdLight', filename=None, path='c:/temp', useSubframe=False, posX=0, posY=0, width=1, height=1)
    while True:
        suc, path = cam.SgGetImagePath(guid)
        if suc:
            break
    # print(suc, path)
    suc, mes, guid = cam.SgSolveImage(path=path, raHint=None, decHint=None, scaleHint=3.7, blindSolve=False, useFitsHeaders=False)
    # print(suc, mes, guid)
    suc, mes, ra, dec, scale, angle, time = cam.SgGetSolvedImageData(guid)
    # print(suc, mes, ra, dec, scale, angle, time)
