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


    def capturingImage(self, modelData, simulation):
        if self.app.workerModeling.cancel:
            self.logger.info('Modeling cancelled while capturing image')
            return False, 'Modeling cancelled by user', modelData
        suc, mes, guid = self.app.workerModeling.SGPro.SgCaptureImage(binningMode=modelData['Binning'],
                                                                exposureLength=modelData['Exposure'],
                                                                iso=str(modelData['Iso']),
                                                                gain=modelData['GainValue'],
                                                                speed=modelData['Speed'],
                                                                frameType='Light',
                                                                filename=modelData['File'],
                                                                path=modelData['BaseDirImages'],
                                                                useSubframe=modelData['CanSubframe'],
                                                                posX=modelData['OffX'],
                                                                posY=modelData['OffY'],
                                                                width=modelData['SizeX'],
                                                                height=modelData['SizeY'])
        modelData['ImagePath'] = ''
        self.logger.info('Capture Image from SGPro {0}, {1}, {2}'.format(suc, mes, guid))
        if suc:
            # waiting for the start of integration
            PyQt5.QtWidgets.QApplication.processEvents()
            time.sleep(0.5)
            # storing the mount and environment data
            modelData['LocalSiderealTime'] = self.app.mount.data['LocalSiderealTime'][0:9]
            modelData['LocalSiderealTimeFloat'] = self.app.workerModeling.transform.degStringToDecimal(modelData['LocalSiderealTime'])
            modelData['RaJ2000'] = self.app.mount.data['RaJ2000']
            modelData['DecJ2000'] = self.app.mount.data['DecJ2000']
            modelData['RaJNow'] = self.app.mount.data['RaJNow']
            modelData['DecJNow'] = self.app.mount.data['DecJNow']
            modelData['Pierside'] = self.app.mount.data['Pierside']
            modelData['RefractionTemperature'] = self.app.mount.data['RefractionTemperature']
            modelData['RefractionPressure'] = self.app.mount.data['RefractionPressure']
            # waiting for the end of integration
            while True:
                PyQt5.QtWidgets.QApplication.processEvents()
                time.sleep(0.1)
                suc, mes = self.app.workerModeling.SGPro.SgGetDeviceStatus('Camera')
                print(mes)
                if suc:
                    if mes != 'INTEGRATING':
                        break
            self.app.workerModeling.modelBoost.workerSlewpoint.signalSlewing.emit()
            # waiting for downloading and storing the image as fits file
            while True:
                PyQt5.QtWidgets.QApplication.processEvents()
                suc, modelData['ImagePath'] = self.app.workerModeling.SGPro.SgGetImagePath(guid)
                if suc:
                    break
                else:
                    time.sleep(0.5)
            # I got a fits file, than i have to add some data
            LocalSiderealTimeFitsHeader = modelData['LocalSiderealTime'][0:10]
            RaJ2000FitsHeader = self.app.workerModeling.transform.decimalToDegree(modelData['RaJ2000'], False, False, ' ')
            DecJ2000FitsHeader = self.app.workerModeling.transform.decimalToDegree(modelData['DecJ2000'], True, False, ' ')
            RaJNowFitsHeader = self.app.workerModeling.transform.decimalToDegree(modelData['RaJNow'], False, True, ' ')
            DecJNowFitsHeader = self.app.workerModeling.transform.decimalToDegree(modelData['DecJNow'], True, True, ' ')
            if modelData['Pierside'] == '1':
                pierside_fits_header = 'E'
            else:
                pierside_fits_header = 'W'
            # if i do simulation i copy a real image instead of using the simulated image of the camera
            if simulation:
                if getattr(sys, 'frozen', False):
                    # we are running in a bundle
                    bundle_dir = sys._MEIPASS
                else:
                    # we are running in a normal Python environment
                    bundle_dir = os.path.dirname(sys.modules['__main__'].__file__)
                shutil.copyfile(bundle_dir + self.app.workerModeling.REF_PICTURE, modelData['ImagePath'])
            else:
                self.logger.info('suc: {0}, modelData{1}'.format(suc, modelData))
                fitsFileHandle = pyfits.open(modelData['ImagePath'], mode='update')
                fitsHeader = fitsFileHandle[0].header
                if 'FOCALLEN' in fitsHeader and 'XPIXSZ' in fitsHeader:
                    modelData['ScaleHint'] = float(fitsHeader['XPIXSZ']) * 206.6 / float(fitsHeader['FOCALLEN'])
                fitsHeader['DATE-OBS'] = datetime.datetime.now().isoformat()
                # i have to update the header for coordinates, because telescope will slew, when the download takes place and i don't know
                # at which point in time the coordinates are taken from the mount by SGPro. Ideally it is the time, when imaging is starting
                # than it's not necessary
                fitsHeader['OBJCTRA'] = RaJ2000FitsHeader
                fitsHeader['OBJCTDEC'] = DecJ2000FitsHeader
                # the rest of the information is needed for the solver to find the appropriate solution. There are different fields possible
                fitsHeader['CDELT1'] = str(modelData['ScaleHint'])
                fitsHeader['CDELT2'] = str(modelData['ScaleHint'])
                fitsHeader['PIXSCALE'] = str(modelData['ScaleHint'])
                fitsHeader['SCALE'] = str(modelData['ScaleHint'])
                # additional Information from MountWizzard should be stored in fits file
                fitsHeader['MW_MRA'] = RaJNowFitsHeader
                fitsHeader['MW_MDEC'] = DecJNowFitsHeader
                fitsHeader['MW_ST'] = LocalSiderealTimeFitsHeader
                fitsHeader['MW_MSIDE'] = pierside_fits_header
                fitsHeader['MW_EXP'] = modelData['Exposure']
                fitsHeader['MW_AZ'] = modelData['Azimuth']
                fitsHeader['MW_ALT'] = modelData['Altitude']
                fitsFileHandle.flush()
                fitsFileHandle.close()
                self.logger.info('Fits header rewritten')
            # show the picture automatically in image window - if opened
            self.app.imageQueue.put(modelData['ImagePath'])
            return True, 'OK', modelData



