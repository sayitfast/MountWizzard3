# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'analyse_dialog_ui.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AnalyseDialog(object):
    def setupUi(self, AnalyseDialog):
        AnalyseDialog.setObjectName("AnalyseDialog")
        AnalyseDialog.resize(791, 641)
        self.analyse = QtWidgets.QWidget(AnalyseDialog)
        self.analyse.setGeometry(QtCore.QRect(10, 80, 771, 551))
        font = QtGui.QFont()
        font.setFamily("Arial")
        self.analyse.setFont(font)
        self.analyse.setAutoFillBackground(True)
        self.analyse.setObjectName("analyse")
        self.btn_errorTime = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_errorTime.setGeometry(QtCore.QRect(140, 20, 111, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_errorTime.setFont(font)
        self.btn_errorTime.setObjectName("btn_errorTime")
        self.btn_errorOverview = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_errorOverview.setGeometry(QtCore.QRect(20, 20, 111, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_errorOverview.setFont(font)
        self.btn_errorOverview.setObjectName("btn_errorOverview")
        self.analyseBackground = QtWidgets.QLabel(AnalyseDialog)
        self.analyseBackground.setGeometry(QtCore.QRect(0, 0, 790, 66))
        self.analyseBackground.setText("")
        self.analyseBackground.setObjectName("analyseBackground")
        self.btn_errorAzAlt = QtWidgets.QPushButton(AnalyseDialog)
        self.btn_errorAzAlt.setGeometry(QtCore.QRect(260, 20, 111, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_errorAzAlt.setFont(font)
        self.btn_errorAzAlt.setObjectName("btn_errorAzAlt")
        self.analyseBackground.raise_()
        self.btn_errorTime.raise_()
        self.btn_errorOverview.raise_()
        self.analyse.raise_()
        self.btn_errorAzAlt.raise_()

        self.retranslateUi(AnalyseDialog)
        QtCore.QMetaObject.connectSlotsByName(AnalyseDialog)

    def retranslateUi(self, AnalyseDialog):
        _translate = QtCore.QCoreApplication.translate
        AnalyseDialog.setWindowTitle(_translate("AnalyseDialog", "Analyse"))
        self.btn_errorTime.setToolTip(_translate("AnalyseDialog", "<html><head/><body><p>Show Dec Error in arc sec from modeling file</p></body></html>"))
        self.btn_errorTime.setText(_translate("AnalyseDialog", "Error over time"))
        self.btn_errorOverview.setToolTip(_translate("AnalyseDialog", "<html><head/><body><p>Show total error in colors over altitude and azimuth in polar diagram. blue: points west, green: points east.</p></body></html>"))
        self.btn_errorOverview.setText(_translate("AnalyseDialog", "Error overview"))
        self.btn_errorAzAlt.setToolTip(_translate("AnalyseDialog", "<html><head/><body><p>Show Dec Error in arc sec from modeling file</p></body></html>"))
        self.btn_errorAzAlt.setText(_translate("AnalyseDialog", "Error over Az/Alt"))

