
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
import skyfield.starlib


class AlignStar:

    # alignment star from hipparcos catatlogue, selection is equivalent to skyfield

    star = dict()
    star["Achernar"] = skyfield.starlib.Star(ra_hours=1.6285684909910512, dec_degrees=-57.23675748604603, ra_mas_per_year=88.02, dec_mas_per_year=-40.08, parallax_mas=22.68, radial_km_per_s=0.0)
    star["Acrux"] = skyfield.starlib.Star(ra_hours=12.443304389488853, dec_degrees=-63.0990916619562, ra_mas_per_year=-35.37, dec_mas_per_year=-14.73, parallax_mas=10.17, radial_km_per_s=0.0)
    star["Adhara"] = skyfield.starlib.Star(ra_hours=6.977096787783971, dec_degrees=-28.972083744027586, ra_mas_per_year=2.63, dec_mas_per_year=2.29, parallax_mas=7.57, radial_km_per_s=0.0)
    star["Agena"] = skyfield.starlib.Star(ra_hours=14.063723467348478, dec_degrees=-60.373039309617674, ra_mas_per_year=-33.96, dec_mas_per_year=-25.06, parallax_mas=6.21, radial_km_per_s=0.0)
    star["Albireo"] = skyfield.starlib.Star(ra_hours=19.512022385341623, dec_degrees=27.959681115970845, ra_mas_per_year=-7.09, dec_mas_per_year=-5.63, parallax_mas=8.46, radial_km_per_s=0.0)
    star["Alcor"] = skyfield.starlib.Star(ra_hours=13.420427210362131, dec_degrees=54.98795766532296, ra_mas_per_year=120.35, dec_mas_per_year=-16.94, parallax_mas=40.19, radial_km_per_s=0.0)
    star["Aldebaran"] = skyfield.starlib.Star(ra_hours=4.598677406767971, dec_degrees=16.509301389939786, ra_mas_per_year=62.78, dec_mas_per_year=-189.36, parallax_mas=50.09, radial_km_per_s=0.0)
    star["Alderamin"] = skyfield.starlib.Star(ra_hours=21.309658745909516, dec_degrees=62.58557261068296, ra_mas_per_year=149.91, dec_mas_per_year=48.27, parallax_mas=66.84, radial_km_per_s=0.0)
    star["Algenib"] = skyfield.starlib.Star(ra_hours=3.4053806529520334, dec_degrees=49.86117959121446, ra_mas_per_year=24.11, dec_mas_per_year=-26.01, parallax_mas=5.51, radial_km_per_s=0.0)
    star["Algieba"] = skyfield.starlib.Star(ra_hours=10.332876236967754, dec_degrees=19.841488734870072, ra_mas_per_year=310.77, dec_mas_per_year=-152.88, parallax_mas=25.96, radial_km_per_s=0.0)
    star["Algol"] = skyfield.starlib.Star(ra_hours=3.1361476567909103, dec_degrees=40.955647699999744, ra_mas_per_year=2.39, dec_mas_per_year=-1.44, parallax_mas=35.14, radial_km_per_s=0.0)
    star["Alhena"] = skyfield.starlib.Star(ra_hours=6.628528082759717, dec_degrees=16.39925216722216, ra_mas_per_year=-2.04, dec_mas_per_year=-66.92, parallax_mas=31.12, radial_km_per_s=0.0)
    star["Alioth"] = skyfield.starlib.Star(ra_hours=12.900485951888628, dec_degrees=55.959821158352696, ra_mas_per_year=111.74, dec_mas_per_year=-8.99, parallax_mas=40.3, radial_km_per_s=0.0)
    star["Alkaid"] = skyfield.starlib.Star(ra_hours=13.792343787984251, dec_degrees=49.31326505967427, ra_mas_per_year=-121.23, dec_mas_per_year=-15.56, parallax_mas=32.39, radial_km_per_s=0.0)
    star["Almach"] = skyfield.starlib.Star(ra_hours=2.0649869643468484, dec_degrees=42.329724726162844, ra_mas_per_year=43.08, dec_mas_per_year=-50.85, parallax_mas=9.19, radial_km_per_s=0.0)
    star["Alnair"] = skyfield.starlib.Star(ra_hours=22.13721818655977, dec_degrees=-46.96097543257332, ra_mas_per_year=127.6, dec_mas_per_year=-147.91, parallax_mas=32.16, radial_km_per_s=0.0)
    star["Alnilam"] = skyfield.starlib.Star(ra_hours=5.6035592894883175, dec_degrees=-1.2019198263888866, ra_mas_per_year=1.49, dec_mas_per_year=-1.06, parallax_mas=2.43, radial_km_per_s=0.0)
    star["Alnitak"] = skyfield.starlib.Star(ra_hours=5.679313094899547, dec_degrees=-1.9425722363888611, ra_mas_per_year=3.99, dec_mas_per_year=2.54, parallax_mas=3.99, radial_km_per_s=0.0)
    star["Alphard"] = skyfield.starlib.Star(ra_hours=9.459789798348773, dec_degrees=-8.658602534026127, ra_mas_per_year=-14.49, dec_mas_per_year=33.25, parallax_mas=18.4, radial_km_per_s=0.0)
    star["Alphecca"] = skyfield.starlib.Star(ra_hours=15.578130032315757, dec_degrees=26.714693020735133, ra_mas_per_year=120.38, dec_mas_per_year=-89.44, parallax_mas=43.65, radial_km_per_s=0.0)
    star["Alpheratz"] = skyfield.starlib.Star(ra_hours=0.13979404756006997, dec_degrees=29.090431990444202, ra_mas_per_year=135.68, dec_mas_per_year=-162.95, parallax_mas=33.6, radial_km_per_s=0.0)
    star["Altair"] = skyfield.starlib.Star(ra_hours=19.84638861051789, dec_degrees=8.868321984070757, ra_mas_per_year=536.82, dec_mas_per_year=385.54, parallax_mas=194.44, radial_km_per_s=0.0)
    star["Aludra"] = skyfield.starlib.Star(ra_hours=7.401584037342451, dec_degrees=-29.303103602499593, ra_mas_per_year=-3.76, dec_mas_per_year=6.66, parallax_mas=1.02, radial_km_per_s=0.0)
    star["Ankaa"] = skyfield.starlib.Star(ra_hours=0.43806971414947443, dec_degrees=-42.305981509124614, ra_mas_per_year=232.76, dec_mas_per_year=-353.64, parallax_mas=42.14, radial_km_per_s=0.0)
    star["Antares"] = skyfield.starlib.Star(ra_hours=16.490128030847767, dec_degrees=-26.432002493191803, ra_mas_per_year=-10.16, dec_mas_per_year=-23.21, parallax_mas=5.4, radial_km_per_s=0.0)
    star["Arcturus"] = skyfield.starlib.Star(ra_hours=14.261020006808682, dec_degrees=19.182410295790085, ra_mas_per_year=-1093.45, dec_mas_per_year=-1999.4, parallax_mas=88.85, radial_km_per_s=0.0)
    star["Arided"] = skyfield.starlib.Star(ra_hours=20.6905318725771, dec_degrees=45.28033799736099, ra_mas_per_year=1.56, dec_mas_per_year=1.55, parallax_mas=1.01, radial_km_per_s=0.0)
    star["Aridif"] = skyfield.starlib.Star(ra_hours=20.6905318725771, dec_degrees=45.28033799736099, ra_mas_per_year=1.56, dec_mas_per_year=1.55, parallax_mas=1.01, radial_km_per_s=0.0)
    star["Aspidiske"] = skyfield.starlib.Star(ra_hours=9.284835187284724, dec_degrees=-59.27522928538525, ra_mas_per_year=-19.03, dec_mas_per_year=13.11, parallax_mas=4.71, radial_km_per_s=0.0)
    star["Atria"] = skyfield.starlib.Star(ra_hours=16.811081909109944, dec_degrees=-69.02771504384603, ra_mas_per_year=17.85, dec_mas_per_year=-32.92, parallax_mas=7.85, radial_km_per_s=0.0)
    star["Avior"] = skyfield.starlib.Star(ra_hours=8.375232106994085, dec_degrees=-59.50948306772156, ra_mas_per_year=-25.34, dec_mas_per_year=22.72, parallax_mas=5.16, radial_km_per_s=0.0)
    star["Becrux"] = skyfield.starlib.Star(ra_hours=12.795350870157481, dec_degrees=-59.688763619517, ra_mas_per_year=-48.24, dec_mas_per_year=-12.82, parallax_mas=9.25, radial_km_per_s=0.0)
    star["Bellatrix"] = skyfield.starlib.Star(ra_hours=5.418850850757774, dec_degrees=6.3497022322217855, ra_mas_per_year=-8.75, dec_mas_per_year=-13.28, parallax_mas=13.42, radial_km_per_s=0.0)
    star["Benetnash"] = skyfield.starlib.Star(ra_hours=13.792343787984251, dec_degrees=49.31326505967427, ra_mas_per_year=-121.23, dec_mas_per_year=-15.56, parallax_mas=32.39, radial_km_per_s=0.0)
    star["Betelgeuse"] = skyfield.starlib.Star(ra_hours=5.919529239737559, dec_degrees=7.407062735828328, ra_mas_per_year=27.33, dec_mas_per_year=10.86, parallax_mas=7.63, radial_km_per_s=0.0)
    star["Birdun"] = skyfield.starlib.Star(ra_hours=13.664794000596656, dec_degrees=-53.46639377679071, ra_mas_per_year=-14.6, dec_mas_per_year=-12.79, parallax_mas=8.68, radial_km_per_s=0.0)
    star["Canopus"] = skyfield.starlib.Star(ra_hours=6.3991971866540736, dec_degrees=-52.69566045872297, ra_mas_per_year=19.99, dec_mas_per_year=23.67, parallax_mas=10.43, radial_km_per_s=0.0)
    star["Capella"] = skyfield.starlib.Star(ra_hours=5.278155293267133, dec_degrees=45.99799110650121, ra_mas_per_year=75.52, dec_mas_per_year=-427.13, parallax_mas=77.29, radial_km_per_s=0.0)
    star["Caph"] = skyfield.starlib.Star(ra_hours=0.15296807541656848, dec_degrees=59.14977959552322, ra_mas_per_year=523.39, dec_mas_per_year=-180.42, parallax_mas=59.89, radial_km_per_s=0.0)
    star["Castor"] = skyfield.starlib.Star(ra_hours=7.576628556311226, dec_degrees=31.888276288912298, ra_mas_per_year=-206.33, dec_mas_per_year=-148.18, parallax_mas=63.27, radial_km_per_s=0.0)
    star["Deneb"] = skyfield.starlib.Star(ra_hours=20.6905318725771, dec_degrees=45.28033799736099, ra_mas_per_year=1.56, dec_mas_per_year=1.55, parallax_mas=1.01, radial_km_per_s=0.0)
    star["Deneb Kaitos"] = skyfield.starlib.Star(ra_hours=0.7264919601096897, dec_degrees=-17.98660459562076, ra_mas_per_year=232.79, dec_mas_per_year=32.71, parallax_mas=34.04, radial_km_per_s=0.0)
    star["Denebola"] = skyfield.starlib.Star(ra_hours=11.817660437393638, dec_degrees=14.57206031805155, ra_mas_per_year=-499.02, dec_mas_per_year=-113.78, parallax_mas=90.16, radial_km_per_s=0.0)
    star["Diphda"] = skyfield.starlib.Star(ra_hours=0.7264919601096897, dec_degrees=-17.98660459562076, ra_mas_per_year=232.79, dec_mas_per_year=32.71, parallax_mas=34.04, radial_km_per_s=0.0)
    star["Dschubba"] = skyfield.starlib.Star(ra_hours=16.005557294713373, dec_degrees=-22.621709927498383, ra_mas_per_year=-8.67, dec_mas_per_year=-36.9, parallax_mas=8.12, radial_km_per_s=0.0)
    star["Dubhe"] = skyfield.starlib.Star(ra_hours=11.062130192490221, dec_degrees=61.75103320112995, ra_mas_per_year=-136.46, dec_mas_per_year=-35.25, parallax_mas=26.38, radial_km_per_s=0.0)
    star["Durre Menthor"] = skyfield.starlib.Star(ra_hours=1.734467475849155, dec_degrees=-15.937480061772153, ra_mas_per_year=-1721.82, dec_mas_per_year=854.07, parallax_mas=274.17, radial_km_per_s=0.0)
    star["Elnath"] = skyfield.starlib.Star(ra_hours=5.438198166101953, dec_degrees=28.607450008595883, ra_mas_per_year=23.28, dec_mas_per_year=-174.22, parallax_mas=24.89, radial_km_per_s=0.0)
    star["Enif"] = skyfield.starlib.Star(ra_hours=21.736432809504855, dec_degrees=9.875011264158582, ra_mas_per_year=30.02, dec_mas_per_year=1.38, parallax_mas=4.85, radial_km_per_s=0.0)
    star["Etamin"] = skyfield.starlib.Star(ra_hours=17.943436075499083, dec_degrees=51.48889498568973, ra_mas_per_year=-8.52, dec_mas_per_year=-23.05, parallax_mas=22.1, radial_km_per_s=0.0)
    star["Fomalhaut"] = skyfield.starlib.Star(ra_hours=22.96084624820144, dec_degrees=-29.62223615265622, ra_mas_per_year=329.22, dec_mas_per_year=-164.22, parallax_mas=130.08, radial_km_per_s=0.0)
    star["Foramen"] = skyfield.starlib.Star(ra_hours=19.0049327596155, dec_degrees=-55.015580999305364, ra_mas_per_year=1.69, dec_mas_per_year=18.35, parallax_mas=4.79, radial_km_per_s=0.0)
    star["Gacrux"] = skyfield.starlib.Star(ra_hours=12.519433139224041, dec_degrees=-57.11321168868774, ra_mas_per_year=27.94, dec_mas_per_year=-264.33, parallax_mas=37.09, radial_km_per_s=0.0)
    star["Gemma"] = skyfield.starlib.Star(ra_hours=15.578130032315757, dec_degrees=26.714693020735133, ra_mas_per_year=120.38, dec_mas_per_year=-89.44, parallax_mas=43.65, radial_km_per_s=0.0)
    star["Gienah"] = skyfield.starlib.Star(ra_hours=20.770189648487424, dec_degrees=33.97025609948278, ra_mas_per_year=356.16, dec_mas_per_year=330.28, parallax_mas=45.26, radial_km_per_s=0.0)
    star["Girtab"] = skyfield.starlib.Star(ra_hours=17.621980723925383, dec_degrees=-42.99782385902602, ra_mas_per_year=6.06, dec_mas_per_year=-0.95, parallax_mas=11.99, radial_km_per_s=0.0)
    star["Gruid"] = skyfield.starlib.Star(ra_hours=22.71112518766103, dec_degrees=-46.88457690079192, ra_mas_per_year=135.68, dec_mas_per_year=-4.51, parallax_mas=19.17, radial_km_per_s=0.0)
    star["Hadar"] = skyfield.starlib.Star(ra_hours=14.063723467348478, dec_degrees=-60.373039309617674, ra_mas_per_year=-33.96, dec_mas_per_year=-25.06, parallax_mas=6.21, radial_km_per_s=0.0)
    star["Hamal"] = skyfield.starlib.Star(ra_hours=2.119557528835421, dec_degrees=23.46242312710268, ra_mas_per_year=190.73, dec_mas_per_year=-145.77, parallax_mas=49.48, radial_km_per_s=0.0)
    star["Herschel's Garnet Star"] = skyfield.starlib.Star(ra_hours=21.72512801211178, dec_degrees=58.78004607999765, ra_mas_per_year=5.24, dec_mas_per_year=-2.88, parallax_mas=0.62, radial_km_per_s=0.0)
    star["Izar"] = skyfield.starlib.Star(ra_hours=14.749782695446205, dec_degrees=27.074222441043503, ra_mas_per_year=-50.65, dec_mas_per_year=20.0, parallax_mas=15.55, radial_km_per_s=0.0)
    star["Kaus Australis"] = skyfield.starlib.Star(ra_hours=18.402866200757806, dec_degrees=-34.38461611036131, ra_mas_per_year=-39.61, dec_mas_per_year=-124.05, parallax_mas=22.55, radial_km_per_s=0.0)
    star["Kochab"] = skyfield.starlib.Star(ra_hours=14.845090670444478, dec_degrees=74.15550490772729, ra_mas_per_year=-32.29, dec_mas_per_year=11.91, parallax_mas=25.79, radial_km_per_s=0.0)
    star["Koo She"] = skyfield.starlib.Star(ra_hours=8.745062881287438, dec_degrees=-54.70882108799522, ra_mas_per_year=28.78, dec_mas_per_year=-104.14, parallax_mas=40.9, radial_km_per_s=0.0)
    star["Marchab"] = skyfield.starlib.Star(ra_hours=23.079348272961244, dec_degrees=15.205264415503251, ra_mas_per_year=61.1, dec_mas_per_year=-42.56, parallax_mas=23.36, radial_km_per_s=0.0)
    star["Marfikent"] = skyfield.starlib.Star(ra_hours=14.591784390419466, dec_degrees=-42.157824467164026, ra_mas_per_year=-35.31, dec_mas_per_year=-32.44, parallax_mas=10.57, radial_km_per_s=0.0)
    star["Markab"] = skyfield.starlib.Star(ra_hours=9.36856064476279, dec_degrees=-55.010667990547084, ra_mas_per_year=-10.72, dec_mas_per_year=11.24, parallax_mas=6.05, radial_km_per_s=0.0)
    star["Megrez"] = skyfield.starlib.Star(ra_hours=12.257100034120432, dec_degrees=57.03261690178644, ra_mas_per_year=103.56, dec_mas_per_year=7.81, parallax_mas=40.05, radial_km_per_s=0.0)
    star["Men"] = skyfield.starlib.Star(ra_hours=14.698821005377841, dec_degrees=-47.388200138030484, ra_mas_per_year=-21.15, dec_mas_per_year=-24.22, parallax_mas=5.95, radial_km_per_s=0.0)
    star["Menkalinan"] = skyfield.starlib.Star(ra_hours=5.992145259211346, dec_degrees=44.94743278094737, ra_mas_per_year=-56.41, dec_mas_per_year=-0.88, parallax_mas=39.72, radial_km_per_s=0.0)
    star["Menkent"] = skyfield.starlib.Star(ra_hours=14.111374571622669, dec_degrees=-36.36995445156714, ra_mas_per_year=-519.29, dec_mas_per_year=-517.87, parallax_mas=53.52, radial_km_per_s=0.0)
    star["Merak"] = skyfield.starlib.Star(ra_hours=11.030687999605183, dec_degrees=56.382426786427374, ra_mas_per_year=81.66, dec_mas_per_year=33.74, parallax_mas=41.07, radial_km_per_s=0.0)
    star["Miaplacidus"] = skyfield.starlib.Star(ra_hours=9.219993190723619, dec_degrees=-69.71720773472705, ra_mas_per_year=-157.66, dec_mas_per_year=108.91, parallax_mas=29.34, radial_km_per_s=0.0)
    star["Mimosa"] = skyfield.starlib.Star(ra_hours=12.795350870157481, dec_degrees=-59.688763619517, ra_mas_per_year=-48.24, dec_mas_per_year=-12.82, parallax_mas=9.25, radial_km_per_s=0.0)
    star["Mintaka"] = skyfield.starlib.Star(ra_hours=5.533444645272205, dec_degrees=-0.2990920388888882, ra_mas_per_year=1.67, dec_mas_per_year=0.56, parallax_mas=3.56, radial_km_per_s=0.0)
    star["Mira"] = skyfield.starlib.Star(ra_hours=2.3224424114388684, dec_degrees=-2.9776426194441377, ra_mas_per_year=10.33, dec_mas_per_year=-239.48, parallax_mas=7.79, radial_km_per_s=0.0)
    star["Mirach"] = skyfield.starlib.Star(ra_hours=1.162200995068799, dec_degrees=35.620557697611176, ra_mas_per_year=175.59, dec_mas_per_year=-112.23, parallax_mas=16.36, radial_km_per_s=0.0)
    star["Mirfak"] = skyfield.starlib.Star(ra_hours=3.4053806529520334, dec_degrees=49.86117959121446, ra_mas_per_year=24.11, dec_mas_per_year=-26.01, parallax_mas=5.51, radial_km_per_s=0.0)
    star["Mirzam"] = skyfield.starlib.Star(ra_hours=6.3783292456834735, dec_degrees=-17.955917722360915, ra_mas_per_year=-3.45, dec_mas_per_year=-0.47, parallax_mas=6.53, radial_km_per_s=0.0)
    star["Mizar"] = skyfield.starlib.Star(ra_hours=13.398761920264775, dec_degrees=54.92536175239315, ra_mas_per_year=121.23, dec_mas_per_year=-22.01, parallax_mas=41.73, radial_km_per_s=0.0)
    star["Muhlifein"] = skyfield.starlib.Star(ra_hours=12.691955167774646, dec_degrees=-48.95988844458953, ra_mas_per_year=-187.28, dec_mas_per_year=-1.2, parallax_mas=25.01, radial_km_per_s=0.0)
    star["Murzim"] = skyfield.starlib.Star(ra_hours=6.3783292456834735, dec_degrees=-17.955917722360915, ra_mas_per_year=-3.45, dec_mas_per_year=-0.47, parallax_mas=6.53, radial_km_per_s=0.0)
    star["Naos"] = skyfield.starlib.Star(ra_hours=8.059735187852958, dec_degrees=-40.00314769954223, ra_mas_per_year=-30.82, dec_mas_per_year=16.77, parallax_mas=2.33, radial_km_per_s=0.0)
    star["Nunki"] = skyfield.starlib.Star(ra_hours=18.921090477553655, dec_degrees=-26.296722248745102, ra_mas_per_year=13.87, dec_mas_per_year=-52.65, parallax_mas=14.54, radial_km_per_s=0.0)
    star["Peacock"] = skyfield.starlib.Star(ra_hours=20.42746050896483, dec_degrees=-56.73509010235645, ra_mas_per_year=7.71, dec_mas_per_year=-86.15, parallax_mas=17.8, radial_km_per_s=0.0)
    star["Phad"] = skyfield.starlib.Star(ra_hours=11.897179848125406, dec_degrees=53.69476008418518, ra_mas_per_year=107.76, dec_mas_per_year=11.16, parallax_mas=38.99, radial_km_per_s=0.0)
    star["Phecda"] = skyfield.starlib.Star(ra_hours=11.897179848125406, dec_degrees=53.69476008418518, ra_mas_per_year=107.76, dec_mas_per_year=11.16, parallax_mas=38.99, radial_km_per_s=0.0)
    star["Polaris"] = skyfield.starlib.Star(ra_hours=2.5303010234979415, dec_degrees=89.26410950742917, ra_mas_per_year=44.22, dec_mas_per_year=-11.74, parallax_mas=7.56, radial_km_per_s=0.0)
    star["Pollux"] = skyfield.starlib.Star(ra_hours=7.755263988502078, dec_degrees=28.026198615229106, ra_mas_per_year=-625.69, dec_mas_per_year=-45.95, parallax_mas=96.74, radial_km_per_s=0.0)
    star["Procyon"] = skyfield.starlib.Star(ra_hours=7.655032867306519, dec_degrees=5.224993063414227, ra_mas_per_year=-716.57, dec_mas_per_year=-1034.58, parallax_mas=285.93, radial_km_per_s=0.0)
    star["Ras Alhague"] = skyfield.starlib.Star(ra_hours=17.582241821699995, dec_degrees=12.560034773888612, ra_mas_per_year=110.08, dec_mas_per_year=-222.61, parallax_mas=69.84, radial_km_per_s=0.0)
    star["Rasalhague"] = skyfield.starlib.Star(ra_hours=17.582241821699995, dec_degrees=12.560034773888612, ra_mas_per_year=110.08, dec_mas_per_year=-222.61, parallax_mas=69.84, radial_km_per_s=0.0)
    star["Regor"] = skyfield.starlib.Star(ra_hours=8.158875066792271, dec_degrees=-47.336587707498026, ra_mas_per_year=-5.93, dec_mas_per_year=9.9, parallax_mas=3.88, radial_km_per_s=0.0)
    star["Regulus"] = skyfield.starlib.Star(ra_hours=10.139530740152827, dec_degrees=11.967207063348102, ra_mas_per_year=-249.4, dec_mas_per_year=4.91, parallax_mas=42.09, radial_km_per_s=0.0)
    star["Rigel"] = skyfield.starlib.Star(ra_hours=5.242297874807085, dec_degrees=-8.201640551111085, ra_mas_per_year=1.87, dec_mas_per_year=-0.56, parallax_mas=4.22, radial_km_per_s=0.0)
    star["Rigel Kent"] = skyfield.starlib.Star(ra_hours=14.66013772257702, dec_degrees=-60.83397468139249, ra_mas_per_year=-3678.19, dec_mas_per_year=481.84, parallax_mas=742.12, radial_km_per_s=0.0)
    star["Rigil Kentaurus"] = skyfield.starlib.Star(ra_hours=14.66013772257702, dec_degrees=-60.83397468139249, ra_mas_per_year=-3678.19, dec_mas_per_year=481.84, parallax_mas=742.12, radial_km_per_s=0.0)
    star["Sabik"] = skyfield.starlib.Star(ra_hours=17.172968701426836, dec_degrees=-15.724910226225411, ra_mas_per_year=41.16, dec_mas_per_year=97.65, parallax_mas=38.77, radial_km_per_s=0.0)
    star["Sadira"] = skyfield.starlib.Star(ra_hours=3.54884560600934, dec_degrees=-9.458262154728086, ra_mas_per_year=-976.44, dec_mas_per_year=17.97, parallax_mas=310.75, radial_km_per_s=0.0)
    star["Sadr"] = skyfield.starlib.Star(ra_hours=20.37047274661545, dec_degrees=40.25667923958307, ra_mas_per_year=2.43, dec_mas_per_year=-0.93, parallax_mas=2.14, radial_km_per_s=0.0)
    star["Saiph"] = skyfield.starlib.Star(ra_hours=5.795941348777099, dec_degrees=-9.669604776666644, ra_mas_per_year=1.55, dec_mas_per_year=-1.2, parallax_mas=4.52, radial_km_per_s=0.0)
    star["Sargas"] = skyfield.starlib.Star(ra_hours=17.621980723925383, dec_degrees=-42.99782385902602, ra_mas_per_year=6.06, dec_mas_per_year=-0.95, parallax_mas=11.99, radial_km_per_s=0.0)
    star["Scheat"] = skyfield.starlib.Star(ra_hours=23.062904867258066, dec_degrees=28.082789087780267, ra_mas_per_year=187.76, dec_mas_per_year=137.61, parallax_mas=16.37, radial_km_per_s=0.0)
    star["Schedar"] = skyfield.starlib.Star(ra_hours=0.6751223652032042, dec_degrees=56.53733108882995, ra_mas_per_year=50.36, dec_mas_per_year=-32.17, parallax_mas=14.27, radial_km_per_s=0.0)
    star["Scutulum"] = skyfield.starlib.Star(ra_hours=9.284835187284724, dec_degrees=-59.27522928538525, ra_mas_per_year=-19.03, dec_mas_per_year=13.11, parallax_mas=4.71, radial_km_per_s=0.0)
    star["Shaula"] = skyfield.starlib.Star(ra_hours=17.56014444045273, dec_degrees=-37.103821145135804, ra_mas_per_year=-8.9, dec_mas_per_year=-29.95, parallax_mas=4.64, radial_km_per_s=0.0)
    star["Sirius"] = skyfield.starlib.Star(ra_hours=6.752477025765419, dec_degrees=-16.716115819270435, ra_mas_per_year=-546.01, dec_mas_per_year=-1223.08, parallax_mas=379.21, radial_km_per_s=0.0)
    star["Sirrah"] = skyfield.starlib.Star(ra_hours=0.13979404756006997, dec_degrees=29.090431990444202, ra_mas_per_year=135.68, dec_mas_per_year=-162.95, parallax_mas=33.6, radial_km_per_s=0.0)
    star["South Star"] = skyfield.starlib.Star(ra_hours=21.146346010469216, dec_degrees=-88.95649899670357, ra_mas_per_year=25.96, dec_mas_per_year=5.02, parallax_mas=12.07, radial_km_per_s=0.0)
    star["Spica"] = skyfield.starlib.Star(ra_hours=13.419883133995869, dec_degrees=-11.161322031509407, ra_mas_per_year=-42.5, dec_mas_per_year=-31.73, parallax_mas=12.44, radial_km_per_s=0.0)
    star["Suhail"] = skyfield.starlib.Star(ra_hours=9.13326623836911, dec_degrees=-43.432589351640374, ra_mas_per_year=-23.21, dec_mas_per_year=14.28, parallax_mas=5.69, radial_km_per_s=0.0)
    star["Thuban"] = skyfield.starlib.Star(ra_hours=14.073152714322651, dec_degrees=64.37585051090666, ra_mas_per_year=-56.52, dec_mas_per_year=17.19, parallax_mas=10.56, radial_km_per_s=0.0)
    star["Toliman"] = skyfield.starlib.Star(ra_hours=14.66013772257702, dec_degrees=-60.83397468139249, ra_mas_per_year=-3678.19, dec_mas_per_year=481.84, parallax_mas=742.12, radial_km_per_s=0.0)
    star["Tseen She"] = skyfield.starlib.Star(ra_hours=19.0049327596155, dec_degrees=-55.015580999305364, ra_mas_per_year=1.69, dec_mas_per_year=18.35, parallax_mas=4.79, radial_km_per_s=0.0)
    star["Tsih"] = skyfield.starlib.Star(ra_hours=0.9451477026042057, dec_degrees=60.7167403752173, ra_mas_per_year=25.65, dec_mas_per_year=-3.82, parallax_mas=5.32, radial_km_per_s=0.0)
    star["Turais"] = skyfield.starlib.Star(ra_hours=9.284835187284724, dec_degrees=-59.27522928538525, ra_mas_per_year=-19.03, dec_mas_per_year=13.11, parallax_mas=4.71, radial_km_per_s=0.0)
    star["Vega"] = skyfield.starlib.Star(ra_hours=18.615649007099478, dec_degrees=38.78369179582599, ra_mas_per_year=201.02, dec_mas_per_year=287.46, parallax_mas=128.93, radial_km_per_s=0.0)
    star["Wei"] = skyfield.starlib.Star(ra_hours=16.836059159468615, dec_degrees=-34.293231713088886, ra_mas_per_year=-611.83, dec_mas_per_year=-255.87, parallax_mas=49.85, radial_km_per_s=0.0)
    star["Wezen"] = skyfield.starlib.Star(ra_hours=7.139856737879104, dec_degrees=-26.39319966624981, ra_mas_per_year=-2.75, dec_mas_per_year=3.33, parallax_mas=1.82, radial_km_per_s=0.0)

    def __init__(self):
        pass

    def __getitem__(self, item):
        if item in self.star:
            return self.star[item]

    def __missing__(self, key):
        return None

    def __iter__(self):
        return iter(self.star)

    def keys(self):
        return self.star.keys()

    def items(self):
        return self.star.items()

    def values(self):
        return self.star.values()


if __name__ == "__main__":

    star = AlignStar()
    for name, value in star.items():
        print(name, value.ra.hours, value.dec.degrees)

