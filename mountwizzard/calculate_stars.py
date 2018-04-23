import astropy.coordinates

# star = astropy.coordinates.SkyCoord(ra=202.469575, dec=47.1952583, unit='deg')
# starTime = astropy.time.Time('2018-04-19 21:00')
# location = astropy.coordinates.EarthLocation(lat='49', lon='11')
# topo = star.transform_to(astropy.coordinates.AltAz(location=location, obstime=starTime))
# print(topo)
star = dict()
star['Albireo'] = None
star['Aldebaran'] = None
star['Alderamin'] = None
star['Algenib'] = None
star['Alkaid'] = None
star['Alpha Cam'] = None
star['Alpha Fornacis'] = None
star['Alpha Lyrics'] = None
star['Alphard'] = None
star['Alpheratz'] = None
star['Altair'] = None
star['Alula Borealis'] = None
star['Antares'] = None
star['Arcturus'] = None
star['Beta Aqr'] = None
star['Betelgeuse'] = None
star['Capella'] = None
star['Caph'] = None
star['Castor'] = None
star['Cor Caroli'] = None
star['Deneb'] = None
star['Denebola'] = None
star['Diphda'] = None
star['Dubhe'] = None
# star['Eltanin'] = None
star['Enif'] = None
star['Gamma Cas'] = None
# star['Gemma'] = None
# star['Gienah Ghurab'] = None
star['Hamal'] = None
star['Kochab'] = None
star['Lambda Aqr'] = None
star['Menkar'] = None
star['Menkent'] = None
star['Mirach'] = None
star['Mirfak'] = None
star['Muscida'] = None
star['Nu Ophiuchi'] = None
star['Omega Cap'] = None
star['Pi Herculis'] = None
star['Polaris'] = None
star['Pollux'] = None
star['Procyon'] = None
# star['Ras Alhague'] = None
star['Regulus'] = None
star['Rho Puppis'] = None
star['Rigel'] = None
star['Scheat'] = None
star['Sirius'] = None
star['Spica'] = None
star['Unukalhai'] = None
star['Vega'] = None
star['Vindemiatrix'] = None
star['Zaurak'] = None
star['Zeta Herculis'] = None
star['Zeta Persei'] = None
# star['Zuben el Genubi'] = None

for name in star:
    star[name] = astropy.coordinates.SkyCoord.from_name(name)
    print(name)

with open('stars.dat', 'w') as outfile:
    outfile.write("star['{0}'] = ({1}, {2})\n".format(name, star[name].ra.to_value(), star[name].dec.to_value()))

