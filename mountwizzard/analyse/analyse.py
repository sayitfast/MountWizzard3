############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016
#
# Licence APL2.0
#
############################################################
# standar solutions
import logging
import os
import numpy
# matplotlib
import matplotlib                                                                                                           # plotting library
matplotlib.use('Qt5Agg')                                                                                                    # we are using QT5 style
import matplotlib.pyplot as plt                                                                                             # use the plot function


class Analyse:
    logger = logging.getLogger('Analyse')                                                                                   # logging enabling

    def __init__(self):
        self.filepath = '\\analysedata'                                                                                     # define file path for storing the analyse files

    def saveData(self, data, name):                                                                                         # saving data from list to file
        if not os.path.isdir(os.getcwd() + self.filepath):                                                                  # if analyse dir doesn't exist, make it
            os.makedirs(os.getcwd() + self.filepath)                                                                        # if path doesn't exist, generate is
        filename = os.getcwd() + self.filepath + '\\' +name                                                                 # built the filename
        try:                                                                                                                # write data to disk
            outfile = open(filename, 'w')                                                                                   # open for write
            for item in data:                                                                                               # run through the data items
                outfile.write('{0}\n'.format(item))                                                                         # write data lines
            outfile.close()                                                                                                 # close the save file
        except Exception as e:                                                                                              # Exception handling
            self.logger.error('saveData -> item in analyse data could not be stored in file {0}, Error : {1}'.format(filename,e))
            return

    def loadData(self, name):                                                                                               # loading data
        filename = os.getcwd() + self.filepath + '\\' + name                                                                # generate filename
        data = []                                                                                                           # clear data list
        try:                                                                                                                # try to read the file
            with open(filename) as infile:                                                                                  # open
                lines = infile.read().splitlines()                                                                          # read over all the lines
            infile.close()                                                                                                  # close
            for i in range(len(lines)):                                                                                     # convert from text to array of floats
                lst1 = lines[i].strip(')').strip('(').split(',')                                                            # shorten the text and split to items
                lst2 = [float(i) for i in lst1]                                                                             # convert to float
                data.append(lst2)                                                                                           # add element to list
        except Exception as e:                                                                                              # exception handling
            self.logger.error('loadData -> item in analyse data could not be loaded from file {0}, Error : {1}'.format(filename, e))
            return []                                                                                                       # loading doesn't work
        return data                                                                                                         # successful loading

    def plotData(self, data, scaleRA, scaleDEC):
        # index in plot             0  1    2   3   4   5       6           7       8       9
        # data format of analyse: (i, az, alt, ra, dec, ra_sol, dec_sol, raError, decError, err)
        if len(data)==0:                                                                                               # in case no data loaded ->
            return                                                                                                          # quit
        dat = numpy.asarray(data)                                                                                      # convert list to array
        datWest = []                                                                                                        # clear the storage, point of west side of pier
        datEast = []                                                                                                        # point on the east side of pier
        datOut = []                                                                                                         # exceeding the min/max value
        for i in range(0,len(dat)):                                                                                         # separate data for coloring
            out = False                                                                                                     # point out of range ?
            if dat[i][7] > scaleRA:
                dat[i][7] = scaleRA
                out = True
            elif dat[i][7] < -scaleRA:
                dat[i][7] = -scaleRA
                out = True
            elif dat[i][8] > scaleDEC:
                dat[i][8] = scaleDEC
                out = True
            elif dat[i][8] < -scaleDEC:
                dat[i][8] = -scaleDEC
                out = True
            if out:                                                                                                         # if out of range, put it to this list
                datOut.append(dat[i])                                                                                       # append
            else:
                if dat[i][1] > 180:                                                                                         # separate east from west and in scale from otu scale
                    datWest.append(dat[i])                                                                                  # appen to west list
                else:
                    datEast.append(dat[i])                                                                                  # append to east list
        dat = numpy.transpose(dat)                                                                                          # transpose array
        datWest = numpy.transpose(datWest)                                                                                  # transpose array
        datEast = numpy.transpose(datEast)                                                                                  # transpose array
        datOut = numpy.transpose(datOut)                                                                                    # transpose array

        plt.rcParams['toolbar'] = 'None'                                                                                    # no toolbar showing in plot
        fig = plt.figure()                                                                                                  # open plot
        fig.suptitle('Modeling Measurements', color='white', fontsize=20)                                                   # set title of figure
        rect = fig.patch                                                                                                    # get rectangle of figure
        rect.set_facecolor((25/256, 25/256, 25/256))                                                                        # set background color of rectangle

        ax1 = fig.add_subplot(231)
        ax1.set_axis_bgcolor((48/256, 48/256, 48/256))
        ax1.tick_params(axis='x', colors='white')
        ax1.tick_params(axis='y', colors='white')
        plt.xlabel('DEC Error (arcsec)', color='white')
        plt.ylabel('Altitude (degree)', color='white')
        plt.title('Altitude over Declination Error', color='white')
        plt.axis([-scaleDEC, scaleDEC, 0, 90])
        plt.grid(True, color='white')
        plt.plot(dat[8], dat[2], color='black')
        plt.plot(datWest[8], datWest[2], 'bo')
        plt.plot(datEast[8], datEast[2], 'go')
        if len(datOut) > 0:
            plt.plot(datOut[8], datOut[2], 'ro')

        ax2 = fig.add_subplot(232)
        #ax2.set_theta_direction(-1)
        #ax2.set_theta_zero_location('N')
        ax2.set_axis_bgcolor((48/256, 48/256, 48/256))
        ax2.tick_params(axis='x', colors='white')
        ax2.tick_params(axis='y', colors='white')
        plt.xlabel('RA Error (arcsec)', color='white')
        plt.ylabel('Altitude (degree)', color='white')
        plt.title('Altitude over RightAcension Error', color='white')
        plt.axis([-scaleRA, scaleRA, 0, 90])
        plt.grid(True, color='white')
        plt.plot(dat[7], dat[2], color='black')
        plt.plot(datWest[7], datWest[2], 'bo')
        plt.plot(datEast[7], datEast[2], 'go')
        if len(datOut) > 0:
            plt.plot(datOut[1], datOut[2], 'ro')

        ax3 = fig.add_subplot(233)
        ax3.set_axis_bgcolor((48/256, 48/256, 48/256))
        ax3.tick_params(axis='x', colors='white')
        ax3.tick_params(axis='y', colors='white')
        plt.xlabel('Azimut (degree)', color='white')
        plt.ylabel('Error (arcsec)', color='white')
        plt.title('Declination Error over Azimuth', color='white')
        plt.axis([0, 360, -scaleDEC, scaleDEC])
        plt.grid(True, color='white')
        plt.plot(dat[1], dat[8], color='black')
        plt.plot(datWest[1], datWest[8], 'bo')
        plt.plot(datEast[1], datEast[8], 'go')
        if len(datOut) > 0:
            plt.plot(datOut[1], datOut[8], 'ro')

        ax4 = fig.add_subplot(234)
        ax4.set_axis_bgcolor((48/256, 48/256, 48/256))
        ax4.tick_params(axis='x', colors='white')
        ax4.tick_params(axis='y', colors='white')
        plt.xlabel('RA Error (arcsec)', color='white')
        plt.ylabel('DEC Error (arcsec)', color='white')
        plt.title('DEC Error over RA Error', color='white')
        plt.axis([-scaleRA, scaleRA, -scaleDEC, scaleDEC])
        plt.grid(True, color='white')
        plt.plot(dat[7], dat[8], color='black')
        plt.plot(datWest[7], datWest[8], 'bo')
        plt.plot(datEast[7], datEast[8], 'go')
        if len(datOut) > 0:
            plt.plot(datOut[7], datOut[8], 'ro')

        ax5 = fig.add_subplot(235)
        ax5.set_axis_bgcolor((48/256, 48/256, 48/256))
        ax5.tick_params(axis='x', colors='white')
        ax5.tick_params(axis='y', colors='white')
        plt.xlabel('Number of Model Point', color='white')
        plt.ylabel('RA Error (arcsec)', color='white')
        plt.title('RA Error over Modeling', color='white')
        plt.axis([0, len(data)-1, -scaleRA, scaleRA])
        plt.grid(True, color='white')
        plt.plot(dat[0], dat[7], color='black')
        plt.plot(datWest[0], datWest[7], 'bo')
        plt.plot(datEast[0], datEast[7], 'go')
        if len(datOut) > 0:
            plt.plot(datOut[0], datOut[7], 'ro')

        ax6 = fig.add_subplot(236)
        ax6.set_axis_bgcolor((48/256, 48/256, 48/256))
        ax6.tick_params(axis='x', colors='white')
        ax6.tick_params(axis='y', colors='white')
        plt.xlabel('Number of Model Point', color='white')
        plt.ylabel('DEC Error (arcsec)', color='white')
        plt.title('DEC Error over Modeling', color='white')
        plt.axis([0, len(data)-1, -scaleDEC, scaleDEC])
        plt.grid(True, color='white')
        plt.plot(dat[0], dat[8], color='black')
        plt.plot(datWest[0], datWest[8], 'bo')
        plt.plot(datEast[0], datEast[8], 'go')
        if len(datOut) > 0:
            plt.plot(datOut[0], datOut[8], 'ro')

        mng = plt.get_current_fig_manager()
        mng.window.showMaximized()
        plt.show()

if __name__ == "__main__":

    a = Analyse()
    #data = a.loadData('2016-10-27-18-31-58_analyse_run.txt')
    #a.plotData(data, 20, 20)

