# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'coordinate_dialog_ui.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CoordinateDialog(object):
    def setupUi(self, CoordinateDialog):
        CoordinateDialog.setObjectName("CoordinateDialog")
        CoordinateDialog.resize(791, 671)
        self.windowTitle = QtWidgets.QLabel(CoordinateDialog)
        self.windowTitle.setGeometry(QtCore.QRect(0, 0, 791, 31))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.windowTitle.setFont(font)
        self.windowTitle.setAutoFillBackground(True)
        self.windowTitle.setAlignment(QtCore.Qt.AlignCenter)
        self.windowTitle.setObjectName("windowTitle")
        self.btn_selectClose = QtWidgets.QPushButton(CoordinateDialog)
        self.btn_selectClose.setGeometry(QtCore.QRect(750, 0, 41, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.btn_selectClose.setFont(font)
        self.btn_selectClose.setObjectName("btn_selectClose")
        self.modelPointsPlot = QtWidgets.QGraphicsView(CoordinateDialog)
        self.modelPointsPlot.setGeometry(QtCore.QRect(10, 50, 771, 371))
        self.modelPointsPlot.viewport().setProperty("cursor", QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.modelPointsPlot.setAutoFillBackground(True)
        self.modelPointsPlot.setFrameShadow(QtWidgets.QFrame.Plain)
        self.modelPointsPlot.setSceneRect(QtCore.QRectF(0.0, 0.0, 769.0, 369.0))
        self.modelPointsPlot.setObjectName("modelPointsPlot")
        self.modellingLog = QtWidgets.QTextBrowser(CoordinateDialog)
        self.modellingLog.setGeometry(QtCore.QRect(10, 430, 771, 231))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(8)
        self.modellingLog.setFont(font)
        self.modellingLog.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.modellingLog.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.modellingLog.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.modellingLog.setAcceptRichText(False)
        self.modellingLog.setObjectName("modellingLog")

        self.retranslateUi(CoordinateDialog)
        QtCore.QMetaObject.connectSlotsByName(CoordinateDialog)

    def retranslateUi(self, CoordinateDialog):
        _translate = QtCore.QCoreApplication.translate
        CoordinateDialog.setWindowTitle(_translate("CoordinateDialog", "Form"))
        self.windowTitle.setText(_translate("CoordinateDialog", "Pointing Coordinates"))
        self.btn_selectClose.setToolTip(_translate("CoordinateDialog", "Sets dual tracking on / off"))
        self.btn_selectClose.setText(_translate("CoordinateDialog", "X"))
        self.modellingLog.setHtml(_translate("CoordinateDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))

