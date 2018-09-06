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
# Python  v3.6.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
############################################################
# standard libraries
import unittest
# external packages
import skyfield.api
# local imports
from mount_new.command import Command
from mount_new.mountData import Data
from test import configTest


class TestCommand(unittest.TestCase):
    CONNECTED = configTest.CONNECTED
    SLEW = configTest.SLEW

    def setUp(self):
        pathToTimescaleData = '~/PycharmProjects/MountWizzard3/config'
        self.data = Data(pathToTimescaleData)

    #
    #
    # testing the real mount communication and values
    #
    #

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_workaroundAlign(self):
        comm = Command(host=('192.168.2.15', 3492))
        ok = comm.workaroundAlign()
        self.assertEqual(True, ok)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_pollSlow(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        ok = comm.pollSlow()
        self.assertEqual(True, ok)
        self.assertEqual(21514, comm.data.fw.number)
        self.assertEqual('2.15.14', comm.data.fw.numberString)
        self.assertEqual('10micron GM1000HPS', comm.data.fw.productName)
        self.assertEqual('Q-TYPE2012', comm.data.fw.hwVersion)
        self.assertEqual('Mar 19 2018', comm.data.fw.fwdate)
        self.assertEqual('15:56:53', comm.data.fw.fwtime)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_pollMed(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        ok = comm.pollMed()
        self.assertEqual(True, ok)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_pollFast(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        ok = comm.pollFast()
        self.assertEqual(True, ok)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_pollModelNames(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        ok = comm.pollModelNames()
        self.assertEqual(True, ok)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_pollModelStars(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        ok = comm.pollModelStars()
        self.assertEqual(True, ok)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_pollModelStars_with_getain(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        comm.data.fw.numberString = '2.15.01'
        ok = comm.pollModelStars()
        self.assertEqual(True, ok)

    #
    #
    # testing slew command function wise
    #
    #

    @unittest.skipIf(not SLEW, 'mount should movable for this test')
    def test_slewAltAz_pos(self):
        alt = skyfield.api.Angle(degrees=31.251234)
        az = skyfield.api.Angle(degrees=55.77777)

        comm = Command(host=('192.168.2.15', 3492))
        suc = comm.slewAltAz(alt, az)
        self.assertEqual(True, suc)

    @unittest.skipIf(not SLEW, 'mount should movable for this test')
    def test_slewAltAz_neg(self):
        alt = skyfield.api.Angle(degrees=-31.251234)
        az = skyfield.api.Angle(degrees=55.77777)

        comm = Command(host=('192.168.2.15', 3492))
        suc = comm.slewAltAz(alt, az)
        self.assertEqual(True, suc)

    @unittest.skipIf(not SLEW, 'mount should movable for this test')
    def test_slewRaDec_pos(self):
        ra = skyfield.api.Angle(degrees=31.251234)
        dec = skyfield.api.Angle(degrees=55.77777)

        comm = Command(host=('192.168.2.15', 3492))
        suc = comm.slewRaDec(ra, dec)
        self.assertEqual(True, suc)

    @unittest.skipIf(not SLEW, 'mount should movable for this test')
    def test_slewRaDec_neg(self):
        ra = skyfield.api.Angle(degrees=31.251234)
        dec = skyfield.api.Angle(degrees=-55.77777)

        comm = Command(host=('192.168.2.15', 3492))
        suc = comm.slewRaDec(ra, dec)
        self.assertEqual(True, suc)

    #
    #
    # testing the connection against host presence
    #
    #

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_startTracking(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.startTracking()
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_stopTracking(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.stopTracking()
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setSlewRate1(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setSlewRate(1)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setSlewRate2(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setSlewRate(2)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setSlewRate10(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setSlewRate(10)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setSlewRate15(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setSlewRate(15)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setSlewRate20(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setSlewRate(20)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionTemp_m50(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefractionTemp(-50)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionTemp_m25(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefractionTemp(-25)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionTemp_0(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefractionTemp(-0)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionTemp_50(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefractionTemp(50)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionTemp_75(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefractionTemp(75)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionTemp_100(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefractionTemp(100)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionPress_800(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefractionPress(800)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionPress_900(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefractionPress(900)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionPress_1000(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefractionPress(1000)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionPress_500(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefractionPress(500)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionPress_200(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefractionPress(200)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionPress_1400(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefractionPress(1400)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionOn(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefraction(True)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setRefractionOff(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setRefraction(False)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setUnattendedFlipOn(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setUnattendedFlip(True)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setUnattendedFlipOff(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setUnattendedFlip(False)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setDualAxisTrackingOn(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setDualAxisTracking(True)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setDualAxisTrackingOff(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setDualAxisTracking(False)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setMeridianLimitSlew_m10(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setMeridianLimitSlew(-10)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setMeridianLimitSlew_10(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setMeridianLimitSlew(10)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setMeridianLimitSlew_30(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setMeridianLimitSlew(30)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setMeridianLimitSlew_50(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setMeridianLimitSlew(50)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setMeridianLimitTrack_10(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setMeridianLimitTrack(10)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setMeridianLimitTrack_30(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setMeridianLimitTrack(30)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setMeridianLimitCombinedOK(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setMeridianLimitSlew(10)
        self.assertEqual(True, suc)
        suc = comm.setMeridianLimitTrack(15)
        self.assertEqual(True, suc)
        suc = comm.setMeridianLimitTrack(5)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setHorizonLimitLow_m10(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setHorizonLimitLow(-10)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setHorizonLimitLow11(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setHorizonLimitLow(11)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setHorizonLimitLow34(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setHorizonLimitLow(34)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setHorizonLimitLow50(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setHorizonLimitLow(50)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setHorizonLimitHigh_m30(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setHorizonLimitHigh(-30)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setHorizonLimitHigh_m15(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setHorizonLimitHigh(-15)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setHorizonLimitHigh_m5(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setHorizonLimitHigh(-5)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setHorizonLimitHigh_45(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setHorizonLimitHigh(45)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setHorizonLimitHigh_90(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setHorizonLimitHigh(90)
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_setHorizonLimitHigh_91(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.setHorizonLimitHigh(91)
        self.assertEqual(False, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_storeName(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.storeName('Test_Store')
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_loadName(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.storeName('Test_Load')
        self.assertEqual(True, suc)
        suc = comm.loadName('Test_Load')
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_deleteName(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.storeName('Test_Delete')
        self.assertEqual(True, suc)
        suc = comm.deleteName('Test_Delete')
        self.assertEqual(True, suc)

    @unittest.skipIf(not CONNECTED, 'mount should be connected for this test')
    def test_deletePoint(self):
        comm = Command(host=('192.168.2.15', 3492),
                       data=self.data,
                       )
        suc = comm.storeName('Test')
        self.assertEqual(True, suc)
        suc = comm.deletePoint(0)
        self.assertEqual(False, suc)
        suc = comm.deletePoint(99)
        self.assertEqual(False, suc)
        suc = comm.deletePoint(102)
        self.assertEqual(False, suc)
        suc = comm.deletePoint(1)
        self.assertEqual(True, suc)
        suc = comm.loadName('Test')
        self.assertEqual(True, suc)


if __name__ == '__main__':
    unittest.main()
