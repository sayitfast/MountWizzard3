from mpl_toolkits.mplot3d import Axes3D
import numpy

def drawEarth(Radius):
	pi = np.pi
	phi, theta = numpy.mgrid[0.0:pi:100j, 0.0:2.0*pi:100j]
	x = Radius*numpy.sin(phi)*numpy.cos(theta)
	y = Radius*numpy.sin(phi)*numpy.sin(theta)
  z = Radius*numpy.cos(phi)
	return x, y, z

def drawEarth(self)
  fig = plt.figure(2)
  ax = Axes3D(fig)
  ax.set_xlim3d([-10000, 10000])
  ax.set_xlabel('X [km]')
  ax.set_ylim3d([-10000, 10000])
  ax.set_ylabel('Y [km]')
  ax.set_zlim3d([-10000, 10000])
  ax.set_zlabel('Z [km]')
  ax.set_title('3D Oribital Trajectory Animation')
  ax.plot_surface(x, y, z, rstride=4, cstride=4, alpha=0.5, color='g')

def makecubelimits(axis, centers=None, hw=None):
    lims = ax.get_xlim(), ax.get_ylim(), ax.get_zlim()
    if centers == None:
        centers = [0.5*sum(pair) for pair in lims] 

    if hw == None:
        widths  = [pair[1] - pair[0] for pair in lims]
        hw      = 0.5*max(widths)
        ax.set_xlim(centers[0]-hw, centers[0]+hw)
        ax.set_ylim(centers[1]-hw, centers[1]+hw)
        ax.set_zlim(centers[2]-hw, centers[2]+hw)
        print "hw was None so set to:", hw

# Install with:
#   conda install -c conda-forge jplephem 
#   conda install -c conda-forge sgp4
#   conda install -c conda-forge skyfield
#
# Download JPL ephemeris (https://en.wikipedia.org/wiki/Jet_Propulsion_Laboratory_Development_Ephemeris) from
#   wget https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de430.bsp
#

from skyfield.api import load, EarthSatellite
from skyfield.timelib import Time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def makecubelimits(axis, centers=None, hw=None):
    lims = ax.get_xlim(), ax.get_ylim(), ax.get_zlim()
    if centers == None:
        centers = [0.5*sum(pair) for pair in lims] 

    if hw == None:
        widths  = [pair[1] - pair[0] for pair in lims]
        hw      = 0.5*max(widths)
        ax.set_xlim(centers[0]-hw, centers[0]+hw)
        ax.set_ylim(centers[1]-hw, centers[1]+hw)
        ax.set_zlim(centers[2]-hw, centers[2]+hw)
        print("hw was None so set to:", hw)
    else:
        try:
            hwx, hwy, hwz = hw
            print("ok hw requested: ", hwx, hwy, hwz)

            ax.set_xlim(centers[0]-hwx, centers[0]+hwx)
            ax.set_ylim(centers[1]-hwy, centers[1]+hwy)
            ax.set_zlim(centers[2]-hwz, centers[2]+hwz)
        except:
            print("nope hw requested: ", hw)
            ax.set_xlim(centers[0]-hw, centers[0]+hw)
            ax.set_ylim(centers[1]-hw, centers[1]+hw)
            ax.set_zlim(centers[2]-hw, centers[2]+hw)

    return centers, hw

TLE = """1 43205U 18017A   18038.05572532 +.00020608 -51169-6 +11058-3 0  9993
2 43205 029.0165 287.1006 3403068 180.4827 179.1544 08.75117793000017"""
L1, L2 = TLE.splitlines()


halfpi, pi, twopi = [f*np.pi for f in (0.5, 1, 2)]
degs, rads = 180/pi, pi/180

data = load('de430.bsp')
ts   = load.timescale()

planets = load('de430.bsp')
earth   = planets['earth']

Roadster = EarthSatellite(L1, L2)

print(Roadster.epoch.tt)
hours = np.arange(0, 3, 0.01)

time = ts.utc(2018, 2, 7, hours)

Rpos    = Roadster.at(time).position.km
Rposecl = Roadster.at(time).ecliptic_position().km

print(Rpos.shape)

re = 6378.

theta = np.linspace(0, twopi, 201)
cth, sth, zth = [f(theta) for f in (np.cos, np.sin, np.zeros_like)]
lon0 = re*np.vstack((cth, zth, sth))
lons = []
for phi in rads*np.arange(0, 180, 15):
    cph, sph = [f(phi) for f in (np.cos, np.sin)]
    lon = np.vstack((lon0[0]*cph - lon0[1]*sph,
                     lon0[1]*cph + lon0[0]*sph,
                     lon0[2]) )
    lons.append(lon)

lat0 = re*np.vstack((cth, sth, zth))
lats = []
for phi in rads*np.arange(-75, 90, 15):
    cph, sph = [f(phi) for f in (np.cos, np.sin)]
    lat = re*np.vstack((cth*cph, sth*cph, zth+sph))
    lats.append(lat)

if True:    
    fig = plt.figure(figsize=[10, 8])  # [12, 10]

    ax  = fig.add_subplot(1, 1, 1, projection='3d')

    x, y, z = Rpos
    ax.plot(x, y, z)
    for x, y, z in lons:
        ax.plot(x, y, z, '-k')
    for x, y, z in lats:
        ax.plot(x, y, z, '-k')

    centers, hw = makecubelimits(ax)

    print("centers are: ", centers)
    print("hw is:       ", hw)

    plt.show()

r_Roadster = np.sqrt((Rpos**2).sum(axis=0))
alt_roadster = r_Roadster - re

if True:
    plt.figure()
    plt.plot(hours, r_Roadster)
    plt.plot(hours, alt_roadster)
    plt.xlabel('hours', fontsize=14)
    plt.ylabel('Geocenter radius or altitude (km)', fontsize=14)
    plt.show()
