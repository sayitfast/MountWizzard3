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
import copy
import logging
from PyQt5.QtWidgets import *
from baseclasses import widget
from astrometry import transform
import numpy
import matplotlib
from gui import hemisphere_dialog_ui

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.artist import Artist
from matplotlib.mlab import dist_point_to_segment


class PolygonInteractor(object):
    """
    An polygon editor.

    Key-bindings

      't' toggle vertex markers on and off.  When vertex markers are on,
          you can move them, delete them

      'd' delete the vertex under point

      'i' insert a vertex at point.  You must be within epsilon of the
          line connecting two existing vertices

    """

    showverts = True
    epsilon = 5  # max pixel distance to count as a vertex hit

    def __init__(self, ax, poly):
        if poly.figure is None:
            raise RuntimeError('You must first add the polygon to a figure or canvas before defining the interactor')
        self.ax = ax
        canvas = poly.figure.canvas
        self.poly = poly

        x, y = zip(*self.poly.xy)
        self.line = Line2D(x, y, marker='o', markerfacecolor='r', animated=True)
        self.ax.add_line(self.line)
        #self._update_line(poly)

        cid = self.poly.add_callback(self.poly_changed)
        self._ind = None  # the active vert

        canvas.mpl_connect('draw_event', self.draw_callback)
        canvas.mpl_connect('button_press_event', self.button_press_callback)
        canvas.mpl_connect('key_press_event', self.key_press_callback)
        canvas.mpl_connect('button_release_event', self.button_release_callback)
        canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        self.canvas = canvas

    def draw_callback(self, event):
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.ax.draw_artist(self.poly)
        self.ax.draw_artist(self.line)
        self.canvas.blit(self.ax.bbox)

    def poly_changed(self, poly):
        'this method is called whenever the polygon object is called'
        # only copy the artist props to the line (except visibility)
        vis = self.line.get_visible()
        Artist.update_from(self.line, poly)
        self.line.set_visible(vis)  # don't use the poly visibility state

    def get_ind_under_point(self, event):
        'get the index of the vertex under point if within epsilon tolerance'

        # display coords
        xy = np.asarray(self.poly.xy)
        xyt = self.poly.get_transform().transform(xy)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.sqrt((xt - event.x)**2 + (yt - event.y)**2)
        indseq = np.nonzero(np.equal(d, np.amin(d)))[0]
        ind = indseq[0]

        if d[ind] >= self.epsilon:
            ind = None

        return ind

    def button_press_callback(self, event):
        'whenever a mouse button is pressed'
        if not self.showverts:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        self._ind = self.get_ind_under_point(event)

    def button_release_callback(self, event):
        'whenever a mouse button is released'
        if not self.showverts:
            return
        if event.button != 1:
            return
        self._ind = None

    def key_press_callback(self, event):
        'whenever a key is pressed'
        if not event.inaxes:
            return
        if event.key == 't':
            self.showverts = not self.showverts
            self.line.set_visible(self.showverts)
            if not self.showverts:
                self._ind = None
        elif event.key == 'd':
            ind = self.get_ind_under_point(event)
            if ind is not None:
                self.poly.xy = [tup for i, tup in enumerate(self.poly.xy) if i != ind]
                self.line.set_data(zip(*self.poly.xy))
        elif event.key == 'i':
            xys = self.poly.get_transform().transform(self.poly.xy)
            p = event.x, event.y  # display coords
            for i in range(len(xys) - 1):
                s0 = xys[i]
                s1 = xys[i + 1]
                d = dist_point_to_segment(p, s0, s1)
                if d <= self.epsilon:
                    self.poly.xy = np.array(
                        list(self.poly.xy[:i]) +
                        [(event.xdata, event.ydata)] +
                        list(self.poly.xy[i:]))
                    self.line.set_data(zip(*self.poly.xy))
                    break

        self.canvas.draw()

    def motion_notify_callback(self, event):
        'on mouse movement'
        if not self.showverts:
            return
        if self._ind is None:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        x, y = event.xdata, event.ydata

        self.poly.xy[self._ind] = x, y
        if self._ind == 0:
            self.poly.xy[-1] = x, y
        elif self._ind == len(self.poly.xy) - 1:
            self.poly.xy[0] = x, y
        self.line.set_data(zip(*self.poly.xy))

        self.canvas.restore_region(self.background)
        self.ax.draw_artist(self.poly)
        self.ax.draw_artist(self.line)
        self.canvas.blit(self.ax.bbox)


class HemisphereWindow(widget.MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(HemisphereWindow, self).__init__()
        self.app = app
        self.transform = transform.Transform(self.app)
        self.pointerAzAlt1 = None
        self.pointerAzAlt2 = None
        self.pointerDome1 = None
        self.pointerDome2 = None
        self.pointerTrack = None
        self.line1 = None
        self.line2 = None
        self.annotate = list()
        self.offx = 0
        self.offy = 0
        self.ui = hemisphere_dialog_ui.Ui_HemisphereDialog()
        self.ui.setupUi(self)
        self.initUI()
        self.initConfig()
        # setup the plot styles
        self.hemisphereMatplotlib = widget.IntegrateMatplotlib(self.ui.hemisphere)
        self.hemisphereMatplotlib.axes = self.hemisphereMatplotlib.fig.add_subplot(111)
        self.hemisphereMatplotlib.fig.subplots_adjust(left=0.075, right=0.925, bottom=0.075, top=0.925)
        # signal connections
        self.app.workerMountDispatcher.signalMountAzAltPointer.connect(self.setAzAltPointer)
        self.app.workerModelingDispatcher.signalModelPointsRedraw.connect(self.drawHemisphere)
        self.ui.btn_deletePoints.clicked.connect(lambda: self.app.workerModelingDispatcher.commandDispatcher('DeletePoints'))
        # self.ui.checkShowNumbers.stateChanged.connect(self.drawHemisphere)
        self.app.workerDome.signalDomePointer.connect(self.setDomePointer)
        self.app.workerDome.signalDomePointerVisibility.connect(self.setDomePointerVisibility)
        # from start on invisible
        self.showStatus = False
        self.setVisible(False)

    def initConfig(self):
        try:
            if 'CoordinatePopupWindowPositionX' in self.app.config:
                x = self.app.config['CoordinatePopupWindowPositionX']
                y = self.app.config['CoordinatePopupWindowPositionY']
                if x > self.screenSizeX:
                    x = 0
                if y > self.screenSizeY:
                    y = 0
                self.move(x, y)
            if 'CoordinatePopupWindowShowStatus' in self.app.config:
                self.showStatus = self.app.config['CoordinatePopupWindowShowStatus']
        except Exception as e:
            self.logger.error('item in config.cfg not be initialize, error:{0}'.format(e))
        finally:
            pass

    def storeConfig(self):
        self.app.config['CoordinatePopupWindowPositionX'] = self.pos().x()
        self.app.config['CoordinatePopupWindowPositionY'] = self.pos().y()
        self.app.config['CoordinatePopupWindowShowStatus'] = self.showStatus

    def showWindow(self):
        self.showStatus = True
        self.setVisible(True)
        self.drawHemisphere()
        self.show()

    def selectHorizonPointsMode(self):
        msg = self.app.workerModelingDispatcher.modelingRunner.modelPoints.loadHorizonPoints(self.app.ui.le_horizonPointsFileName.text(),
                                                                                             self.app.ui.checkUseFileHorizonLine.isChecked(),
                                                                                             self.app.ui.checkUseMinimumHorizonLine.isChecked(),
                                                                                             self.app.ui.altitudeMinimumHorizon.value())
        if msg:
            self.app.messageQueue.put(msg + '\n')
        self.drawHemisphere()

    def setAzAltPointer(self, az, alt):
        az += 0.5
        alt -= 0.125
        if self.showStatus:
            self.pointerAzAlt1.center = az, alt
            self.pointerAzAlt2.center = az, alt
            self.pointerAzAlt1.set_visible(True)
            self.pointerAzAlt2.set_visible(True)
            self.hemisphereMatplotlib.fig.canvas.draw()
            QApplication.processEvents()

    def setDomePointerVisibility(self, stat):
        if self.showStatus:
            self.pointerDome1.set_visible(stat)
            self.pointerDome2.set_visible(stat)
            self.hemisphereMatplotlib.fig.canvas.draw()
            QApplication.processEvents()

    def setDomePointer(self, az):
        if self.showStatus:
            self.pointerDome1.set_xy((az - 15, 1))
            self.pointerDome2.set_xy((az - 15, 1))
            self.hemisphereMatplotlib.fig.canvas.draw()
            QApplication.processEvents()

    def onMouse(self, event):
        if event.inaxes is None:
            return
        ind = self.get_ind_under_point(event, 2)
        points = self.app.workerModelingDispatcher.modelingRunner.modelPoints.modelPoints
        if event.button == 3 and ind is not None:
            # delete a point
            if len(points) > 0:
                # print(ind, len(self.annotate), len(points))
                del(points[ind])
                self.annotate[ind].remove()
                del(self.annotate[ind])
            # now redraw plot
            self.line1.set_data([i[0] for i in points], [i[1] for i in points])
            self.line2.set_data([i[0] for i in points], [i[1] for i in points])
        if event.button == 1 and ind is None:
            # add a point
            points.append((event.xdata, event.ydata))
            self.annotate.append(self.hemisphereMatplotlib.axes.annotate('{0:2d}'.format(len(points)), xy=(event.xdata - self.offx, event.ydata - self.offy), color='#E0E0E0'))
            # now redraw plot
            self.line1.set_data([i[0] for i in points], [i[1] for i in points])
            self.line2.set_data([i[0] for i in points], [i[1] for i in points])

        for i in range(0, len(points)):
            self.annotate[i].set_text('{0:2d}'.format(i + 1))
        self.hemisphereMatplotlib.fig.canvas.draw()

    def get_ind_under_point(self, event, epsilon):
        xy = self.app.workerModelingDispatcher.modelingRunner.modelPoints.modelPoints
        if len(xy) == 0:
            return None
        xt = np.asarray([i[0] for i in xy])
        yt = np.asarray([i[1] for i in xy])
        d = np.sqrt((xt - event.xdata)**2 / 16 + (yt - event.ydata)**2)
        indseq = np.nonzero(np.equal(d, np.amin(d)))[0]
        ind = indseq[0]
        if d[ind] >= epsilon:
            ind = None
        return ind

    def drawHemisphere(self):
        for i in range(0, len(self.annotate)):
            self.annotate[i].remove()
        self.annotate = list()
        self.hemisphereMatplotlib.fig.canvas.mpl_connect('button_press_event', self.onMouse)
        self.hemisphereMatplotlib.axes.cla()
        self.hemisphereMatplotlib.axes.spines['bottom'].set_color('#2090C0')
        self.hemisphereMatplotlib.axes.spines['top'].set_color('#2090C0')
        self.hemisphereMatplotlib.axes.spines['left'].set_color('#2090C0')
        self.hemisphereMatplotlib.axes.spines['right'].set_color('#2090C0')
        self.hemisphereMatplotlib.axes.grid(True, color='#404040')
        self.hemisphereMatplotlib.axes.set_facecolor((32 / 256, 32 / 256, 32 / 256))
        self.hemisphereMatplotlib.axes.tick_params(axis='x', colors='#2090C0', labelsize=12)
        self.hemisphereMatplotlib.axes.set_xlim(0, 360)
        self.hemisphereMatplotlib.axes.set_xticks(numpy.arange(0, 361, 30))
        self.hemisphereMatplotlib.axes.set_ylim(0, 90)
        self.hemisphereMatplotlib.axes.tick_params(axis='y', colors='#2090C0', which='both', labelleft='on', labelright='on', labelsize=12)
        # get the aspect ratio for circles etc:
        figW, figH = self.hemisphereMatplotlib.axes.get_figure().get_size_inches()
        _, _, w, h = self.hemisphereMatplotlib.axes.get_position().bounds
        displayRatio = (figH * h) / (figW * w)
        dataRatio = 90 / 360
        aspectRatio = displayRatio / dataRatio
        # horizon
        horizon = copy.copy(self.app.workerModelingDispatcher.modelingRunner.modelPoints.horizonPoints)
        horizon.insert(0, (0, 0))
        horizon.append((360, 0))
        self.hemisphereMatplotlib.axes.fill([i[0] for i in horizon], [i[1] for i in horizon], color='#002000', zorder=-20)
        self.hemisphereMatplotlib.axes.plot([i[0] for i in horizon], [i[1] for i in horizon], color='#006000', zorder=-20, lw=3)
        # model points
        self.offx = -2
        self.offy = 7 / aspectRatio
        points = self.app.workerModelingDispatcher.modelingRunner.modelPoints.modelPoints
        # draw points in two colors
        self.line1,  = self.hemisphereMatplotlib.axes.plot([i[0] for i in points], [i[1] for i in points], 'o', markersize=9, color='#00A000')
        self.line2,  = self.hemisphereMatplotlib.axes.plot([i[0] for i in points], [i[1] for i in points], 'o', markersize=3, color='#E0E000')
        # add text to points
        for i in range(0, len(points)):
            self.annotate.append(self.hemisphereMatplotlib.axes.annotate('{0:2d}'.format(i+1), xy=(points[i][0] - self.offx, points[i][1] - self.offy), color='#E0E0E0'))
        # adding the pointer of mount
        self.pointerAzAlt1 = matplotlib.patches.Ellipse((180, 45), 4 * aspectRatio, 4, zorder=10, color='#FF00FF', lw=2, fill=False, visible=False)
        self.pointerAzAlt2 = matplotlib.patches.Ellipse((180, 45), 1.5 * aspectRatio, 1.5, zorder=10, color='#FF00FF', lw=1, fill=False, visible=False)
        self.hemisphereMatplotlib.axes.add_patch(self.pointerAzAlt1)
        self.hemisphereMatplotlib.axes.add_patch(self.pointerAzAlt2)
        # adding pointer of dome if dome is present
        self.pointerDome1 = matplotlib.patches.Rectangle((165, 1), 30, 88, zorder=-30, color='#404040', lw=3, fill=True, visible=False)
        self.pointerDome2 = matplotlib.patches.Rectangle((165, 1), 30, 88, zorder=-30, color='#808080', lw=3, fill=False, visible=False)
        self.hemisphereMatplotlib.axes.add_patch(self.pointerDome1)
        self.hemisphereMatplotlib.axes.add_patch(self.pointerDome2)
        self.hemisphereMatplotlib.draw()

