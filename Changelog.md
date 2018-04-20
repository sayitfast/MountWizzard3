
3.2 todo
- check for suthern hemisphere and latitudes < 0
- function clear message window
- get stored models from mount in list
- show directions how to turn know for polar alignment

3.1 todo
- check TSX
- show best polar alignment star (south, closed to eclipse)
- Image Window: image calculations to separat thread (threadpool)

3.0 todo

star = astropy.coordinates.SkyCoord.from_name('M51')
topo = star.transform_to(astropy.coordinates.AltAz(location=location, obstime=otime))
otime = astropy.time.Time('2018-04-19 21:00')
location = astropy.coordinates.EarthLocation(lat='49', lon='11')