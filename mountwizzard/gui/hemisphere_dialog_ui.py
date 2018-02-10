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
        self.btn_deletePoints.setGeometry(QtCore.QRect(20, 10, 111, 51))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_deletePoints.setFont(font)
        self.btn_deletePoints.setObjectName("btn_deletePoints")
        self.hemisphereBackground = QtWidgets.QLabel(HemisphereDialog)
        self.hemisphereBackground.setGeometry(QtCore.QRect(0, 0, 790, 71))
        self.hemisphereBackground.setText("")
        self.hemisphereBackground.setObjectName("hemisphereBackground")
        self.groupBox_2 = QtWidgets.QGroupBox(HemisphereDialog)
        self.groupBox_2.setGeometry(QtCore.QRect(150, 10, 201, 51))
        self.groupBox_2.setObjectName("groupBox_2")
        self.btn_editNone = QtWidgets.QRadioButton(self.groupBox_2)
        self.btn_editNone.setGeometry(QtCore.QRect(10, 20, 61, 21))
        self.btn_editNone.setChecked(True)
        self.btn_editNone.setObjectName("btn_editNone")
        self.btn_editModelPoints = QtWidgets.QRadioButton(self.groupBox_2)
        self.btn_editModelPoints.setGeometry(QtCore.QRect(70, 20, 61, 21))
        self.btn_editModelPoints.setObjectName("btn_editModelPoints")
        self.btn_editHorizonMask = QtWidgets.QRadioButton(self.groupBox_2)
        self.btn_editHorizonMask.setGeometry(QtCore.QRect(140, 20, 61, 21))
        self.btn_editHorizonMask.setObjectName("btn_editHorizonMask")
        self.hemisphereBackground.raise_()
        self.hemisphere.raise_()
        self.btn_deletePoints.raise_()
        self.groupBox_2.raise_()

        self.retranslateUi(HemisphereDialog)
        QtCore.QMetaObject.connectSlotsByName(HemisphereDialog)

    def retranslateUi(self, HemisphereDialog):
        _translate = QtCore.QCoreApplication.translate
        HemisphereDialog.setWindowTitle(_translate("HemisphereDialog", "Hemisphere"))
        self.btn_deletePoints.setToolTip(_translate("HemisphereDialog", "<html><head/><body><p>Delete all points on coordinate window including Base / Model</p></body></html>"))
        self.btn_deletePoints.setText(_translate("HemisphereDialog", "Clear\n"
"Model Points"))
        self.groupBox_2.setTitle(_translate("HemisphereDialog", "Edit"))
        self.btn_editNone.setText(_translate("HemisphereDialog", "None"))
        self.btn_editModelPoints.setText(_translate("HemisphereDialog", "Points"))
        self.btn_editHorizonMask.setText(_translate("HemisphereDialog", "Mask"))

