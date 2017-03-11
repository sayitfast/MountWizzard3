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
            message = 'TheSkyX TCP server is available'
        except Exception as e:
            self.logger.error('checkConnection-> error: {0}'.format(e))
            connected = False
            message = 'TheSkyX TCP server is missing'
        finally:
            tsxSocket.close()
            return connected, message

    def SgEnumerateDevice(self, device):
        return '', False, 'Not implemented'
        # reference {"Device": "Camera"}, devices are "Camera", "FilterWheel", "Focuser", "Telescope" and "PlateSolver"}
        # data = {'Device': device}
        # try:
        #     req = request.Request(self.ipTheSkyX + self.enumerateDevicePath, data=bytes(json.dumps(data).encode('utf-8')), method='POST')
        #     req.add_header('Content-Type', 'application/json')
        #     with request.urlopen(req) as f:
        #        captureResponse = json.loads(f.read().decode('utf-8'))
        #     # {"Devices":["String"],"Success":false,"Message":"String"}
        #     return captureResponse['Devices'], captureResponse['Success'], 'Request OK'
        # except Exception as e:
        #     self.logger.error('SgEnumerateDevi-> error: {0}'.format(e))
        #     return '', False, 'Request failed'

    def SgCaptureImage(self, binningMode=1, exposureLength=1, gain=None, iso=None, speed=None,
                       frameType=None, filename=None, path=None, useSubframe=False, posX=0, posY=0, width=1, height=1):
        try:
            command = '/* Java Script */'
            command += 'ccdsoftCamera.Asynchronous=1;'
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
            # {"Success":false,"Message":"String","Receipt":"00000000000000000000000000000000"}
            return success, response, '00000000000000000000000000000000'
        except Exception as e:
            self.logger.error('TXCaptureImage -> error: {0}'.format(e))
            return False, 'Request failed', ''

    def SgSolveImage(self, path, raHint=None, decHint=None, scaleHint=None, blindSolve=False, useFitsHeaders=False):
        try:
            command = '/* Java Script */'
            command += 'ImageLink.pathToFITS="'+path+'";'
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

    def SgGetSolvedImageData(self, _guid):
        try:
            command = '/* Java Script */'
            command += 'var Out = "";'
            command += 'Out=String(\'{"succeeded":"\'+ImageLinkResults.succeeded+\'","imageCenterRAJ2000":"\'+ImageLinkResults.imageCenterRAJ2000+\'","imageCenterDecJ2000":"\'+ImageLinkResults.imageCenterDecJ2000+\'","imageScale":"\'+ImageLinkResults.imageScale+\'","imagePositionAngle":"\'+ImageLinkResults.imagePositionAngle+\'"}\');'
            success, response = self.sendCommand(command)
            # {"Success":false,"Message":"String","Ra":0,"Dec":0,"Scale":0,"Angle":0,"TimeToSolve":0}
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

    def SgGetImagePath(self, _guid):
        try:
            command = '/* Java Script */ var Out = ""; Out=ccdsoftCamera.LastImageFileName';
            success, response = self.sendCommand(command)
            return success, response
        except Exception as e:
            self.logger.error('TXGetImagePath -> error: {0}'.format(e))
            return False, 'Request failed'

    def SgGetDeviceStatus(self, device):
        # reference {"Device": "Camera"}, devices are "Camera", "FilterWheel", "Focuser", "Telescope" and "PlateSolver"}
        try:
            command = '/* Java Script */ var Out = ""; Out=ccdsoftCamera.ExposureStatus';
            success, response = self.sendCommand(command)
            # states are  "IDLE", "CAPTURING", "BUSY", "MOVING", "DISCONNECTED", "PARKED"

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

    def SgGetCameraProps(self):
        try:
            command = '/* Java Script */ var Out = ""; Out=String(\'{"WidthInPixels":"\'+ccdsoftCamera.WidthInPixels+\'","HeightInPixels":"\'+ccdsoftCamera.HeightInPixels+\'"}\');'
            success, response = self.sendCommand(command)
            # {"Success":false,"Message":"String","NumPixelsX":0,"NumPixelsY":0,"SupportsSubframe":false}
            captureResponse = json.loads(response)
            return success, '', int(captureResponse['WidthInPixels']), int(captureResponse['HeightInPixels']), True, 'High'
        except Exception as e:
            self.logger.error('TXGetCameraProp-> error: {0}'.format(e))
            return False, 'Request failed', '', '', ''
