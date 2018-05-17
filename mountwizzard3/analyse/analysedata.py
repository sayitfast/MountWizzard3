############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
############################################################
import json
import math
import os
from logging import getLogger


class Analyse:
    logger = getLogger(__name__)

    UPDATE = {'index': 'Index',
              'azimuth': 'Azimuth',
              'altitude': 'Altitude',
              'modelError': 'ModelError',
              'raError': 'RaError',
              'decError': 'DecError',
              'ra_Jnow': 'RaJNow',
              'dec_Jnow': 'DecJNow',
              'ra_sol_Jnow': 'RaJNowSolved',
              'dec_sol_Jnow': 'DecJNowSolved',
              'pierside': 'Pierside',
              'sidereal_time_float': 'LocalSiderealTimeFloat'}

    def __init__(self, app):
        self.filepath = '/analysedata'
        self.app = app

    def saveData(self, dataProcess, name):
        filenameData = os.getcwd() + self.filepath + '/' + name + '.dat'
        try:
            outfile = open(filenameData, 'w')
            json.dump(dataProcess, outfile)
            outfile.close()
        except Exception as e:
            self.logger.error('analyse data file {0}, Error : {1}'.format(filenameData, e))
            return

    def processTheSkyXLine(self, line):
        ra_sol = self.app.mount.degStringToDecimal(line[0:13], ' ')
        dec_sol = self.app.mount.degStringToDecimal(line[15:28], ' ')
        ra = self.app.mount.degStringToDecimal(line[30:43], ' ')
        dec = self.app.mount.degStringToDecimal(line[45:58], ' ')
        lst = self.app.mount.degStringToDecimal(line[61:70], ' ')
        return ra, dec, ra_sol, dec_sol, lst

    def loadTheSkyXData(self, filename):
        resultData = {}
        try:
            with open(filename) as infile:
                lines = infile.read().splitlines()
            infile.close()
            # site_latitude = self.app.mount.degStringToDecimal(lines[4][0:9], ' ')
            for i in range(5, len(lines)):
                ra, dec, ra_sol, dec_sol, lst = self.processTheSkyXLine(lines[i])
                if 'RaJ2000' in resultData:
                    resultData['RaJ2000'].append(ra)
                else:
                    resultData['RaJ2000'] = [ra]
                if 'DecJ2000' in resultData:
                    resultData['DecJ2000'].append(dec)
                else:
                    resultData['DecJ2000'] = [dec]
                ra_Jnow, dec_Jnow = self.app.mount.transformERFA(ra, dec, 3)
                if 'RaJNow' in resultData:
                    resultData['RaJNow'].append(ra_Jnow)
                else:
                    resultData['RaJNow'] = [ra_Jnow]
                if 'DecJNow' in resultData:
                    resultData['decJNow'].append(dec_Jnow)
                else:
                    resultData['DecJNow'] = [dec_Jnow]
                if 'LocalSiderealTimeFloat' in resultData:
                    resultData['LocalSiderealTimeFloat'].append(lst)
                else:
                    resultData['LocalSiderealTimeFloat'] = [lst]
                if 'LocalSiderealTime' in resultData:
                    resultData['LocalSiderealTime'].append(self.app.mount.decimalToDegree(lst, False, True))
                else:
                    resultData['LocalSiderealTime'] = [self.app.mount.decimalToDegree(lst, False, True)]
                if 'RaJ2000Solved' in resultData:
                    resultData['RaJ2000Solved'].append(ra_sol)
                else:
                    resultData['RaJ2000Solved'] = [ra_sol]
                if 'DecJ2000Solved' in resultData:
                    resultData['DecJ2000Solved'].append(dec_sol)
                else:
                    resultData['DecJ2000Solved'] = [dec_sol]
                ra_sol_Jnow, dec_sol_Jnow = self.app.mount.transformERFA(ra_sol, dec_sol, 3)
                if 'RaJNowSolved' in resultData:
                    resultData['RaJNowSolved'].append(ra_sol_Jnow)
                else:
                    resultData['RaJNowSolved'] = [ra_sol_Jnow]
                if 'DecJNowSolved' in resultData:
                    resultData['DecJNowSolved'].append(dec_sol_Jnow)
                else:
                    resultData['DecJNowSolved'] = [dec_sol_Jnow]
                ha = ra - lst
                az, alt = self.app.mount.transformERFA(ha, dec, 3)
                if 'Azimuth' in resultData:
                    resultData['Azimuth'].append(az)
                else:
                    resultData['Azimuth'] = [az]
                if 'Altitude' in resultData:
                    resultData['Altitude'].append(alt)
                else:
                    resultData['Altitude'] = [alt]
                if az <= 180:
                    pierside = 'E'
                else:
                    pierside = 'W'
                if 'Pierside' in resultData:
                    resultData['Pierside'].append(pierside)
                else:
                    resultData['Pierside'] = [pierside]
                if 'Index' in resultData:
                    resultData['Index'].append(i - 5)
                else:
                    resultData['index'] = [i - 5]
                if 'RaError' in resultData:
                    resultData['RaError'].append((ra - ra_sol) * 3600)
                else:
                    resultData['RaError'] = [(ra - ra_sol) * 3600]
                if 'DecError' in resultData:
                    resultData['DecError'].append((dec - dec_sol) * 3600)
                else:
                    resultData['DecError'] = [(dec - dec_sol) * 3600]
                if 'ModelError' in resultData:
                    resultData['ModelError'].append(math.sqrt((ra - ra_sol) * 3600 * (ra - ra_sol) * 3600 + (dec - dec_sol) * 3600 * (dec - dec_sol) * 3600))
                else:
                    resultData['ModelError'] = [math.sqrt((ra - ra_sol) * 3600 * (ra - ra_sol) * 3600 + (dec - dec_sol) * 3600 * (dec - dec_sol) * 3600)]
        except Exception as e:
            self.logger.error('error processing file {0}, Error : {1}'.format(filename, e))
            return {}
        return resultData

    def loadMountWizzardData(self, filename):
        try:
            infile = open(filename, 'r')
            dataJson = json.load(infile)
            infile.close()
        except Exception as e:
            self.logger.error('analyse data file {0}, Error : {1}'.format(filename, e))
            return {}
        # check if old file format
        if isinstance(dataJson, list):
            resultData = dict()
            for timestepdict in dataJson:
                for (keyData, valueData) in timestepdict.items():
                    if keyData in self.UPDATE:
                        keyData = self.UPDATE[keyData]
                    if keyData in resultData:
                        resultData[keyData].append(valueData)
                    else:
                        resultData[keyData] = [valueData]
        else:
            resultData = dataJson
        return resultData

    def loadDataRaw(self, filename):
        filenameData = os.getcwd() + self.filepath + '/' + filename + '.dat'
        if os.path.isfile(filenameData):
            infile = open(filenameData, 'r')
            dataJson = json.load(infile)
            infile.close()
            return dataJson
        else:
            return None

    def loadData(self, filename):
        filenameData = os.getcwd() + self.filepath + '/' + filename + '.dat'
        if os.path.isfile(filenameData):
            infile = open(filenameData, 'r')
            check = infile.read(8)
            infile.close()
            if check == '!TheSkyX':
                data = self.loadTheSkyXData(filenameData)
            else:
                data = self.loadMountWizzardData(filenameData)
            return data
        else:
            return {}


if __name__ == "__main__":
    logger = getLogger(__name__)
    from mount.mount_dispatcher import Mount
    filename = '10micron_model.dat'
    m = Mount
    a = Analyse(m)
    data = a.loadData(filename)
    # print(data)
