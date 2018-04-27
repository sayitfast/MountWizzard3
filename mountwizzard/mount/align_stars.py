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
# Python  v3.6.4
#
# Michael Würtenberger
# (c) 2016, 2017, 2018
#
# Licence APL2.0
#
###########################################################
import logging


class AlignStars:
    logger = logging.getLogger(__name__)

    # alignment stars of 10micron with (ra(deg), dec(deg))
    stars = dict()
    stars['Albireo'] = ['19 30 43.28052', '+27 57 34.8483', -7.17, -6.15]
    stars['Aldebaran'] = ['04 35 55.23907', '+16 30 33.4885', 63.45, -188.94]
    stars['Alderamin'] = ['21 18 34.77233', '+62 35 08.0681', 150.55, 49.09]
    stars['Algenib'] = ['00 13 14.15123', '+15 11 00.9368', 1.98, -9.28]
    stars['Alkaid'] = ['13 47 32.43776', '+49 18 47.7602', -121.17, -14.91]
    stars['Alpha Cam'] = ['04 54 03.01040', '+66 20 33.6365', -0.13, 6.89]
    stars['Alpha Fornacis'] = ['03 12 04.52736', '-28 59 15.4336', 370.87, 611.33]
    stars['Alpha Lyrics'] = ['18 36 56.33635', '+38 47 01.2802', 200.94, 286.23]
    stars['Alphard'] = ['09 27 35.24270', '-08 39 30.9583', -15.23, 34.37]
    stars['Alpheratz'] = ['00 08 23.25988', '+29 05 25.5520', 137.46, -163.44]
    stars['Altair'] = ['19 50 46.99855', '+08 52 05.9563', 536.23, 385.29]
    stars['Alula Borealis'] = ['11 18 28.73664', '+33 05 39.5107', -26.84, 28.69]
    stars['Antares'] = ['16 29 24.45970', '-26 25 55.2094', -12.11, -23.30]
    stars['Arcturus'] = ['14 15 39.67207', '+19 10 56.6730', -1093.39, -2000.06]
    stars['Beta Aqr'] = ['21 31 33.53171', '-05 34 16.2320', 18.77, -8.21]
    stars['Betelgeuse'] = ['05 55 10.30536', '+07 24 25.4304', 27.54, 11.30]
    stars['Capella'] = ['05 16 41.35871', '+45 59 52.7693', 75.25, -426.89]
    stars['Caph'] = ['00 09 10.68518', '+59 08 59.2120', 523.50, -179.77]
    stars['Castor'] = ['07 34 35.87319', '+31 53 17.8160', -191.45, -145.19]
    stars['Cor Caroli'] = ['12 56 01.66622', '+38 19 06.1541', -235.08, 53.54]
    stars['Deneb'] = ['20 41 25.91514', '+45 16 49.2197', 2.01, 1.85]
    stars['Denebola'] = ['11 49 03.57834', '+14 34 19.4090', -497.68, -114.67]
    stars['Diphda'] = ['00 43 35.37090', '-17 59 11.7827', 232.55, 31.99]
    stars['Dubhe'] = ['11 03 43.67152', '+61 45 03.7249', -134.11, -34.70]
    stars['Eltanin'] = ['17 56 36.36988', '+51 29 20.0242', -8.48, -22.79]
    stars['Enif'] = ['21 44 11.15614', '+09 52 30.0311', 26.92, 0.44]
    stars['Gamma Cas'] = ['00 56 42.5317', '+60 43 00.265', 25.65, -3.82]
    stars['Gienah Ghurab'] = ['12 15 48.37081', '-17 32 30.9496', -158.61, 21.86]
    stars['Hamal'] = ['02 07 10.40570', '+23 27 44.7032', 188.55, -148.08]
    stars['Kochab'] = ['14 50 42.32580', '+74 09 19.8142', -32.61, 11.42]
    stars['Lambda Aqr'] = ['22 52 36.87441', '-07 34 46.5542', 17.02, 33.03]
    stars['Menkar'] = ['03 02 16.77307', '+04 05 23.0596', -10.41, -76.85]
    stars['Menkent'] = ['14 06 40.94752', '-36 22 11.8371', -520.53, -518.06]
    stars['Mirach'] = ['01 09 43.92388', '+35 37 14.0075', 175.90, -112.20]
    stars['Mirfak'] = ['03 24 19.37009', '+49 51 40.2455', 23.75, -26.23]
    stars['Muscida'] = ['08 30 15.87064', '+60 43 05.4115', -133.76, -107.45]
    stars['Omega Cap'] = ['20 51 49.29084', '-26 55 08.8574', -8.36, -0.36]
    stars['Pi Herculis'] = ['17 15 02.83436', '+36 48 32.9843', -27.29, 2.82]
    stars['Polaris'] = ['02 31 49.09456', '+89 15 50.7923', 44.48, -11.85]
    stars['Pollux'] = ['07 45 18.94987', '+28 01 34.3160', -626.55, -45.80]
    stars['Procyon'] = ['07 39 18.11950', '+05 13 29.9552', -714.59, -1036.80]
    stars['Ras Alhague'] = ['17 34 56.06945', '+12 33 36.1346', 108.07, -221.57]
    stars['Regulus'] = ['10 08 22.31099', '+11 58 01.9516', -248.73, 5.59]
    stars['Rho Puppis'] = ['08 07 32.64882', '-24 18 15.5679', -83.35, 46.23]
    stars['Rigel'] = ['05 14 32.27210', '-08 12 05.8981', 1.31, 0.50]
    stars['Scheat'] = ['23 03 46.45746', '+28 04 58.0336', 187.65, 136.93]
    stars['Sirius'] = ['06 45 08.91728', '-16 42 58.0171', -546.01, -1223.07]
    stars['Spica'] = ['13 25 11.57937', '-11 09 40.7501', -42.35, -30.67]
    stars['Unukalhai'] = ['15 44 16.07431', '+06 25 32.2633', 133.84, 44.81]
    stars['Vindemiatrix'] = ['13 02 10.59785', '+10 57 32.9415', -273.80, 19.96]
    stars['Zaurak'] = ['03 58 01.76695', '-13 30 30.6698', 61.57, -113.11]
    stars['Zeta Herculis'] = ['16 41 17.16104', '+31 36 09.7873', -461.52, 342.28]
    stars['Zeta Persei'] = ['03 54 07.92248', '+31 53 01.0812', 5.77, -9.92]

    def __init__(self, app):
        self.app = app

    def degStringToDecimal(self, value, splitter=':'):
        returnValue = 0
        sign = 1
        if '-' in value:
            value = value.replace('-', '')
            sign = -1
        elif '+' in value:
            value = value.replace('+', '')
        else:
            # just for formal understanding
            pass
        try:
            if len(value.split(splitter)) == 3:
                hour, minute, second = value.split(splitter)
                returnValue = (float(hour) + float(minute) / 60 + float(second) / 3600) * sign
            elif len(value.split(splitter)) == 2:
                hour, minute = value.split(splitter)
                returnValue = (float(hour) + float(minute) / 60) * sign
        except Exception as e:
            self.logger.error('Error in conversion of:{0} with splitter:{1}, e:{2}'.format(value, splitter, e))
            returnValue = 0
        finally:
            pass
        return returnValue

if __name__ == "__main__":


    stars = AlignStars(1)
    jd_2000 = 2451544.5
    jd_now = 2458235.84003
    jd_delta = jd_now - jd_2000
    year_delta = jd_delta / 365.25
    print(year_delta, jd_delta)

    for name in stars.stars:
        ra = stars.degStringToDecimal(stars.stars[name][0], ' ') * 360 / 24 + year_delta * stars.stars[name][2] / 3600000
        dec = stars.degStringToDecimal(stars.stars[name][1], ' ') + year_delta * stars.stars[name][3] / 3600000
        print(name, 'RA: ', ra, ' DEC: ', dec)

