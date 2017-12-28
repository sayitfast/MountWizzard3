# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'coordinate_dialog_ui.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CoordinateDialog(object):
    def setupUi(self, CoordinateDialog):
        CoordinateDialog.setObjectName("CoordinateDialog")
        CoordinateDialog.resize(791, 639)
        font = QtGui.QFont()
        font.setFamily("Arial")
        CoordinateDialog.setFont(font)
        self.checkRunTrackingWidget = QtWidgets.QCheckBox(CoordinateDialog)
        self.checkRunTrackingWidget.setGeometry(QtCore.QRect(250, 10, 111, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.checkRunTrackingWidget.setFont(font)
        self.checkRunTrackingWidget.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.checkRunTrackingWidget.setChecked(True)
        self.checkRunTrackingWidget.setObjectName("checkRunTrackingWidget")
        self.hemisphere = QtWidgets.QWidget(CoordinateDialog)
        self.hemisphere.setEnabled(True)
        self.hemisphere.setGeometry(QtCore.QRect(10, 60, 771, 571))
        self.hemisphere.setAutoFillBackground(True)
        self.hemisphere.setStyleSheet("")
        self.hemisphere.setObjectName("hemisphere")
        self.btn_deletePoints = QtWidgets.QPushButton(CoordinateDialog)
        self.btn_deletePoints.setGeometry(QtCore.QRect(10, 10, 111, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_deletePoints.setFont(font)
        self.btn_deletePoints.setObjectName("btn_deletePoints")
        self.checkShowNumbers = QtWidgets.QCheckBox(CoordinateDialog)
        self.checkShowNumbers.setGeometry(QtCore.QRect(130, 10, 111, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.checkShowNumbers.setFont(font)
        self.checkShowNumbers.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.checkShowNumbers.setChecked(True)
        self.checkShowNumbers.setObjectName("checkShowNumbers")
        self.hemisphere.raise_()
        self.checkRunTrackingWidget.raise_()
        self.btn_deletePoints.raise_()
        self.checkShowNumbers.raise_()

        self.retranslateUi(CoordinateDialog)
        QtCore.QMetaObject.connectSlotsByName(CoordinateDialog)

    def retranslateUi(self, CoordinateDialog):
        _translate = QtCore.QCoreApplication.translate
        CoordinateDialog.setWindowTitle(_translate("CoordinateDialog", "Modeling Plot"))
        self.checkRunTrackingWidget.setToolTip(_translate("CoordinateDialog", "<html><head/><body><p>Checked if you would like to see the tracking line and flip time in the window</p></body></html>"))
        self.checkRunTrackingWidget.setText(_translate("CoordinateDialog", "Show Track"))
        self.btn_deletePoints.setToolTip(_translate("CoordinateDialog", "<html><head/><body><p>Delete all points on coordinate window including Base / Model</p></body></html>"))
        self.btn_deletePoints.setText(_translate("CoordinateDialog", "Clear Points"))
        self.checkShowNumbers.setToolTip(_translate("CoordinateDialog", "<html><head/><body><p>Checked if you would like to see the tracking line and flip time in the window</p></body></html>"))
        self.checkShowNumbers.setText(_translate("CoordinateDialog", "Show Numbers"))

