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
###########################################################

import skyfield.api

# global loader
skyfieldLoader = skyfield.api.Loader('~/config', verbose=False)

# global time
skyfieldTime = skyfieldLoader.timescale()

# get the data downloaded
skyfieldPlanets = skyfieldLoader('de421.bsp')

# you have to use the variables accordingly with:
#
# import globals
# global skyfieldTime
# global skyfieldPlanets