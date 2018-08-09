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

