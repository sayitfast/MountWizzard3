# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'popup_dialog_ui.ui'
#
# Created by: PyQt5 UI code generator 5.8.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_PopupDialog(object):
    def setupUi(self, PopupDialog):
        PopupDialog.setObjectName("PopupDialog")
        PopupDialog.resize(400, 511)
        self.windowTitle = QtWidgets.QLabel(PopupDialog)
        self.windowTitle.setGeometry(QtCore.QRect(0, 0, 401, 31))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.windowTitle.setFont(font)
        self.windowTitle.setAutoFillBackground(True)
        self.windowTitle.setAlignment(QtCore.Qt.AlignCenter)
        self.windowTitle.setObjectName("windowTitle")
        self.widgetPlot = QtWidgets.QWidget(PopupDialog)
        self.widgetPlot.setGeometry(QtCore.QRect(-1, 100, 401, 411))
        self.widgetPlot.setObjectName("widgetPlot")

        self.retranslateUi(PopupDialog)
        QtCore.QMetaObject.connectSlotsByName(PopupDialog)

    def retranslateUi(self, PopupDialog):
        _translate = QtCore.QCoreApplication.translate
        PopupDialog.setWindowTitle(_translate("PopupDialog", "Form"))
        self.windowTitle.setText(_translate("PopupDialog", "Popup"))

