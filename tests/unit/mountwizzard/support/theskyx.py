import unittest
import time

from mountwizzard.support.camera_theskyx import TheSkyX

class TheSkyXTestCase(unittest.TestCase):

    def setUp(self):
        self.theskyx = TheSkyX()

    def test_checkConnection(self):
        res, message = self.theskyx.checkConnection()
        self.assertEqual(True, res)

    @unittest.skip("skipping")
    def test_SgEnumerateDevice(self):
        devices, res, message = self.theskyx.SgEnumerateDevice('')
        self.assertEqual(True, res)

    def test_SgCaptureImage(self):
        success, response, receipt = self.theskyx.SgCaptureImage(1, None, 5, None, None, None, 'cdLight', None, 'c:/temp', False, 0, 0, 1, 1)
        self.assertEqual(True, success)
        self.assertEqual('0', response)

    @unittest.skip("skipping")
    def test_SgCaptureImage_withSubFrame(self):
        success, response, receipt = self.theskyx.SgCaptureImage(1, None, 5, None, None, None, 'cdLight',
                                                                 None, 'c:/temp', True, 100, 100, 300, 300)
        self.assertEqual(True, success)
        self.assertEqual('0', response)

    @unittest.skip("skipping")
    def test_SgSolveImage(self):
        success, response, receipt = self.theskyx.SgSolveImage('c:/temp/', None, None, 2.47, False, False)
        self.assertEqual(True, success)
        self.assertEqual('0', response)

    @unittest.skip("skipping")
    def test_SgGetSolvedImageData(self):
        self.theskyx.SgSolveImage('d:/test_mw/test.fit', None, None, 2.47, False, False)
        succeeded, message, imageCenterRAJ2000, imageCenterDecJ2000, imageScale, imagePositionAngle, time = self.theskyx.SgGetSolvedImageData(None)
        self.assertEqual(True, succeeded)

    def test_SgGetImagePath(self):
        self.theskyx.SgCaptureImage(1, None, 5, None, None, None, 'cdLight', 'd:/test_mw/', False, 0, 0, 1, 1)
        time.sleep(5)
        success, response = self.theskyx.SgGetImagePath(None)
        self.assertEqual(True, success)

    def test_SgGetDeviceStatus(self):
        success, response = self.theskyx.SgGetDeviceStatus(None);
        self.assertEqual(True, success)

    def test_SgGetCameraProps(self):
        success, message, numPixelsX, numPixelsY, supportsSubframe = self.theskyx.SgGetCameraProps()
        self.assertEqual(True, success)

if __name__ == '__main__':
    unittest.main()
