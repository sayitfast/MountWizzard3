# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'hemisphere_dialog_ui.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_HemisphereDialog(object):
    def setupUi(self, HemisphereDialog):
        HemisphereDialog.setObjectName("HemisphereDialog")
        HemisphereDialog.resize(791, 641)
        font = QtGui.QFont()
        font.setFamily("Arial")
        HemisphereDialog.setFont(font)
        self.hemisphere = QtWidgets.QWidget(HemisphereDialog)
        self.hemisphere.setEnabled(True)
        self.hemisphere.setGeometry(QtCore.QRect(10, 80, 771, 551))
        self.hemisphere.setAutoFillBackground(True)
        self.hemisphere.setStyleSheet("")
        self.hemisphere.setObjectName("hemisphere")
        self.btn_deletePoints = QtWidgets.QPushButton(HemisphereDialog)
        self.btn_deletePoints.setGeometry(QtCore.QRect(20, 20, 111, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_deletePoints.setFont(font)
        self.btn_deletePoints.setObjectName("btn_deletePoints")
        self.checkShowNumbers = QtWidgets.QCheckBox(HemisphereDialog)
        self.checkShowNumbers.setGeometry(QtCore.QRect(140, 20, 111, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.checkShowNumbers.setFont(font)
        self.checkShowNumbers.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.checkShowNumbers.setChecked(True)
        self.checkShowNumbers.setObjectName("checkShowNumbers")
        self.hemisphereBackground = QtWidgets.QLabel(HemisphereDialog)
        self.hemisphereBackground.setGeometry(QtCore.QRect(0, 0, 790, 71))
        self.hemisphereBackground.setText("")
        self.hemisphereBackground.setObjectName("hemisphereBackground")
        self.hemisphereBackground.raise_()
        self.hemisphere.raise_()
        self.btn_deletePoints.raise_()
        self.checkShowNumbers.raise_()

        self.retranslateUi(HemisphereDialog)
        QtCore.QMetaObject.connectSlotsByName(HemisphereDialog)

    def retranslateUi(self, HemisphereDialog):
        _translate = QtCore.QCoreApplication.translate
        HemisphereDialog.setWindowTitle(_translate("HemisphereDialog", "Hemisphere"))
        self.btn_deletePoints.setToolTip(_translate("HemisphereDialog", "<html><head/><body><p>Delete all points on coordinate window including Base / Model</p></body></html>"))
        self.btn_deletePoints.setText(_translate("HemisphereDialog", "Clear Points"))
        self.checkShowNumbers.setToolTip(_translate("HemisphereDialog", "<html><head/><body><p>Checked if you would like to see the tracking line and flip time in the window</p></body></html>"))
        self.checkShowNumbers.setText(_translate("HemisphereDialog", "Show Numbers"))

