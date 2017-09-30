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
# standard solutions
import json
import math
import os
from logging import getLogger


class Analyse:
    logger = getLogger(__name__)

    def __init__(self, app):
        self.filepath = '/analysedata'
        self.app = app

    def saveData(self, dataProcess, name):                                                                                  # saving data from list to file
        if name in ['base.dat', 'refine.dat', 'actual.dat', 'simple.dat', 'dso1.dat', 'dso2.dat']:
            number = self.app.mount.numberModelStars()
            if number == -1:                                                                                                # if not real mount, than don't save modeling data
                return
        filenameData = os.getcwd() + self.filepath + '/' + name                                                             # built the filename
        try:                                                                                                                # write data to disk
            outfile = open(filenameData, 'w')                                                                               # open for write
            json.dump(dataProcess, outfile)
            outfile.close()                                                                                                 # close the save file
        except Exception as e:                                                                                              # Exception handling
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
                if 'ra_J2000' in resultData:
                    resultData['ra_J2000'].append(ra)
                else:
                    resultData['ra_J2000'] = [ra]
                if 'dec_J2000' in resultData:
                    resultData['dec_J2000'].append(dec)
                else:
                    resultData['dec_J2000'] = [dec]
                ra_Jnow, dec_Jnow = self.app.mount.transformERFA(ra, dec, 3)
                if 'ra_Jnow' in resultData:
                    resultData['ra_Jnow'].append(ra_Jnow)
                else:
                    resultData['ra_Jnow'] = [ra_Jnow]
                if 'dec_Jnow' in resultData:
                    resultData['dec_Jnow'].append(dec_Jnow)
                else:
                    resultData['dec_Jnow'] = [dec_Jnow]
                if 'sidereal_time_float' in resultData:
                    resultData['sidereal_time_float'].append(lst)
                else:
                    resultData['sidereal_time_float'] = [lst]
                if 'sidereal_time' in resultData:
                    resultData['sidereal_time'].append(self.app.mount.decimalToDegree(lst, False, True))
                else:
                    resultData['sidereal_time'] = [self.app.mount.decimalToDegree(lst, False, True)]
                if 'ra_sol' in resultData:
                    resultData['ra_sol'].append(ra_sol)
                else:
                    resultData['ra_sol'] = [ra_sol]
                if 'dec_sol' in resultData:
                    resultData['dec_sol'].append(dec_sol)
                else:
                    resultData['dec_sol'] = [dec_sol]
                ra_sol_Jnow, dec_sol_Jnow = self.app.mount.transformERFA(ra_sol, dec_sol, 3)
                if 'ra_sol_Jnow' in resultData:
                    resultData['ra_sol_Jnow'].append(ra_sol_Jnow)
                else:
                    resultData['ra_sol_Jnow'] = [ra_sol_Jnow]
                if 'dec_sol_Jnow' in resultData:
                    resultData['dec_sol_Jnow'].append(dec_sol_Jnow)
                else:
                    resultData['dec_sol_Jnow'] = [dec_sol_Jnow]
                ha = ra - lst
                az, alt = self.app.mount.transformERFA(ha, dec, 3)
                if 'azimuth' in resultData:
                    resultData['azimuth'].append(az)
                else:
                    resultData['azimuth'] = [az]
                if 'altitude' in resultData:
                    resultData['altitude'].append(alt)
                else:
                    resultData['altitude'] = [alt]
                if az <= 180:
                    pierside = 'E'
                else:
                    pierside = 'W'
                if 'pierside' in resultData:
                    resultData['pierside'].append(pierside)
                else:
                    resultData['pierside'] = [pierside]
                if 'index' in resultData:
                    resultData['index'].append(i - 5)
                else:
                    resultData['index'] = [i - 5]
                if 'raError' in resultData:
                    resultData['raError'].append((ra - ra_sol) * 3600)
                else:
                    resultData['raError'] = [(ra - ra_sol) * 3600]
                if 'decError' in resultData:
                    resultData['decError'].append((dec - dec_sol) * 3600)
                else:
                    resultData['decError'] = [(dec - dec_sol) * 3600]
                if 'modelError' in resultData:
                    resultData['modelError'].append(math.sqrt((ra - ra_sol) * 3600 * (ra - ra_sol) * 3600 + (dec - dec_sol) * 3600 * (dec - dec_sol) * 3600))
                else:
                    resultData['modelError'] = [math.sqrt((ra - ra_sol) * 3600 * (ra - ra_sol) * 3600 + (dec - dec_sol) * 3600 * (dec - dec_sol) * 3600)]
        except Exception as e:
            self.logger.error('error processing file {0}, Error : {1}'.format(filename, e))
            return {}
        return resultData

    def loadMountWizzardData(self, filename):
        try:                                                                                                                # try to read the file
            infile = open(filename, 'r')
            dataJson = json.load(infile)
            infile.close()                                                                                                  # close
        except Exception as e:                                                                                              # exception handling
            self.logger.error('analyse data file {0}, Error : {1}'.format(filename, e))
            return {}                                                                                                       # loading doesn't work
        resultData = dict()
        for timestepdict in dataJson:
            for (keyData, valueData) in timestepdict.items():
                if keyData in resultData:
                    resultData[keyData].append(valueData)
                else:
                    resultData[keyData] = [valueData]
        return resultData                                                                                                   # successful loading

    def loadDataRaw(self, filename):                                                                                        # saving data from list to file
        filenameData = os.getcwd() + self.filepath + '/' + filename                                                         # generate filename
        if os.path.isfile(filenameData):
            infile = open(filenameData, 'r')
            dataJson = json.load(infile)
            infile.close()
            return dataJson
        else:
            return None

    def loadData(self, filename):                                                                                           # loading data
        filenameData = os.getcwd() + self.filepath + '/' + filename                                                         # generate filename
        if os.path.isfile(filenameData):
            infile = open(filenameData, 'r')
            check = infile.read(8)
            infile.close()
            if check == '!TheSkyX':
                data = self.loadTheSkyXData(filenameData)
            else:
                data = self.loadMountWizzardData(filenameData)
            return data

    @staticmethod
    def prepareData(dataProcess, scaleRA, scaleDEC):
        if len(dataProcess) == 0:                                                                                           # in case no data loaded ->
            return dataProcess                                                                                              # quit
        dataProcess['raError'] = [scaleRA if x > scaleRA else x for x in dataProcess['raError']]
        dataProcess['raError'] = [-scaleRA if x < -scaleRA else x for x in dataProcess['raError']]
        dataProcess['decError'] = [scaleDEC if x > scaleDEC else x for x in dataProcess['decError']]
        dataProcess['decError'] = [-scaleDEC if x < -scaleDEC else x for x in dataProcess['decError']]
        return dataProcess


if __name__ == "__main__":
    logger = getLogger(__name__)
    from mount.mount_thread import Mount
    filename = '10micron_model.dat'
    m = Mount
    a = Analyse(m)
    data = a.loadData(filename)
    # print(data)
