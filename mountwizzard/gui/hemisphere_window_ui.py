# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'hemisphere_window_ui.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
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
        self.hemisphere.setGeometry(QtCore.QRect(10, 115, 771, 516))
        self.hemisphere.setAutoFillBackground(True)
        self.hemisphere.setStyleSheet("")
        self.hemisphere.setObjectName("hemisphere")
        self.btn_deletePoints = QtWidgets.QPushButton(HemisphereDialog)
        self.btn_deletePoints.setGeometry(QtCore.QRect(20, 15, 131, 31))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_deletePoints.setFont(font)
        self.btn_deletePoints.setObjectName("btn_deletePoints")
        self.hemisphereBackground = QtWidgets.QLabel(HemisphereDialog)
        self.hemisphereBackground.setGeometry(QtCore.QRect(0, 0, 791, 126))
        self.hemisphereBackground.setText("")
        self.hemisphereBackground.setObjectName("hemisphereBackground")
        self.groupBox_2 = QtWidgets.QGroupBox(HemisphereDialog)
        self.groupBox_2.setGeometry(QtCore.QRect(250, 10, 166, 106))
        self.groupBox_2.setObjectName("groupBox_2")
        self.btn_editNone = QtWidgets.QRadioButton(self.groupBox_2)
        self.btn_editNone.setGeometry(QtCore.QRect(10, 15, 111, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_editNone.setFont(font)
        self.btn_editNone.setChecked(True)
        self.btn_editNone.setObjectName("btn_editNone")
        self.btn_editModelPoints = QtWidgets.QRadioButton(self.groupBox_2)
        self.btn_editModelPoints.setGeometry(QtCore.QRect(10, 35, 146, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_editModelPoints.setFont(font)
        self.btn_editModelPoints.setObjectName("btn_editModelPoints")
        self.btn_editHorizonMask = QtWidgets.QRadioButton(self.groupBox_2)
        self.btn_editHorizonMask.setGeometry(QtCore.QRect(10, 55, 141, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.btn_editHorizonMask.setFont(font)
        self.btn_editHorizonMask.setObjectName("btn_editHorizonMask")
        self.checkPolarAlignment = QtWidgets.QRadioButton(self.groupBox_2)
        self.checkPolarAlignment.setEnabled(False)
        self.checkPolarAlignment.setGeometry(QtCore.QRect(10, 75, 136, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.checkPolarAlignment.setFont(font)
        self.checkPolarAlignment.setObjectName("checkPolarAlignment")
        self.hemisphereMoving = QtWidgets.QWidget(HemisphereDialog)
        self.hemisphereMoving.setEnabled(True)
        self.hemisphereMoving.setGeometry(QtCore.QRect(10, 115, 771, 516))
        self.hemisphereMoving.setAutoFillBackground(False)
        self.hemisphereMoving.setStyleSheet("")
        self.hemisphereMoving.setObjectName("hemisphereMoving")
        self.hemisphereStar = QtWidgets.QWidget(self.hemisphereMoving)
        self.hemisphereStar.setEnabled(True)
        self.hemisphereStar.setGeometry(QtCore.QRect(0, 0, 771, 516))
        self.hemisphereStar.setAutoFillBackground(False)
        self.hemisphereStar.setStyleSheet("")
        self.hemisphereStar.setObjectName("hemisphereStar")
        self.checkShowAlignmentStars = QtWidgets.QCheckBox(HemisphereDialog)
        self.checkShowAlignmentStars.setGeometry(QtCore.QRect(20, 55, 131, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.checkShowAlignmentStars.setFont(font)
        self.checkShowAlignmentStars.setObjectName("checkShowAlignmentStars")
        self.groupBox = QtWidgets.QGroupBox(HemisphereDialog)
        self.groupBox.setGeometry(QtCore.QRect(425, 10, 356, 106))
        self.groupBox.setObjectName("groupBox")
        self.label_100 = QtWidgets.QLabel(self.groupBox)
        self.label_100.setGeometry(QtCore.QRect(10, 20, 66, 16))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_100.setFont(font)
        self.label_100.setObjectName("label_100")
        self.le_numberPointsImaged = QtWidgets.QLineEdit(self.groupBox)
        self.le_numberPointsImaged.setEnabled(False)
        self.le_numberPointsImaged.setGeometry(QtCore.QRect(70, 40, 26, 16))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.le_numberPointsImaged.setFont(font)
        self.le_numberPointsImaged.setMouseTracking(False)
        self.le_numberPointsImaged.setFocusPolicy(QtCore.Qt.NoFocus)
        self.le_numberPointsImaged.setAcceptDrops(False)
        self.le_numberPointsImaged.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.le_numberPointsImaged.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.le_numberPointsImaged.setReadOnly(True)
        self.le_numberPointsImaged.setObjectName("le_numberPointsImaged")
        self.bar_numberPointsProcessed = QtWidgets.QProgressBar(self.groupBox)
        self.bar_numberPointsProcessed.setGeometry(QtCore.QRect(145, 80, 201, 16))
        self.bar_numberPointsProcessed.setMaximum(1000)
        self.bar_numberPointsProcessed.setProperty("value", 1)
        self.bar_numberPointsProcessed.setTextVisible(False)
        self.bar_numberPointsProcessed.setObjectName("bar_numberPointsProcessed")
        self.label_77 = QtWidgets.QLabel(self.groupBox)
        self.label_77.setGeometry(QtCore.QRect(10, 40, 66, 16))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_77.setFont(font)
        self.label_77.setObjectName("label_77")
        self.bar_numberPointsImaged = QtWidgets.QProgressBar(self.groupBox)
        self.bar_numberPointsImaged.setGeometry(QtCore.QRect(145, 40, 201, 16))
        self.bar_numberPointsImaged.setMaximum(1000)
        self.bar_numberPointsImaged.setProperty("value", 1)
        self.bar_numberPointsImaged.setTextVisible(False)
        self.bar_numberPointsImaged.setObjectName("bar_numberPointsImaged")
        self.label_81 = QtWidgets.QLabel(self.groupBox)
        self.label_81.setGeometry(QtCore.QRect(10, 80, 66, 16))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_81.setFont(font)
        self.label_81.setObjectName("label_81")
        self.le_numberPointsProcessed = QtWidgets.QLineEdit(self.groupBox)
        self.le_numberPointsProcessed.setEnabled(False)
        self.le_numberPointsProcessed.setGeometry(QtCore.QRect(70, 80, 26, 16))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.le_numberPointsProcessed.setFont(font)
        self.le_numberPointsProcessed.setMouseTracking(False)
        self.le_numberPointsProcessed.setFocusPolicy(QtCore.Qt.NoFocus)
        self.le_numberPointsProcessed.setAcceptDrops(False)
        self.le_numberPointsProcessed.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.le_numberPointsProcessed.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.le_numberPointsProcessed.setReadOnly(True)
        self.le_numberPointsProcessed.setObjectName("le_numberPointsProcessed")
        self.bar_numberPointsSlewed = QtWidgets.QProgressBar(self.groupBox)
        self.bar_numberPointsSlewed.setGeometry(QtCore.QRect(145, 20, 201, 16))
        self.bar_numberPointsSlewed.setMinimum(0)
        self.bar_numberPointsSlewed.setMaximum(1000)
        self.bar_numberPointsSlewed.setProperty("value", 0)
        self.bar_numberPointsSlewed.setTextVisible(False)
        self.bar_numberPointsSlewed.setOrientation(QtCore.Qt.Horizontal)
        self.bar_numberPointsSlewed.setInvertedAppearance(False)
        self.bar_numberPointsSlewed.setTextDirection(QtWidgets.QProgressBar.BottomToTop)
        self.bar_numberPointsSlewed.setObjectName("bar_numberPointsSlewed")
        self.le_numberPointsSlewed = QtWidgets.QLineEdit(self.groupBox)
        self.le_numberPointsSlewed.setEnabled(False)
        self.le_numberPointsSlewed.setGeometry(QtCore.QRect(70, 20, 26, 16))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.le_numberPointsSlewed.setFont(font)
        self.le_numberPointsSlewed.setMouseTracking(False)
        self.le_numberPointsSlewed.setFocusPolicy(QtCore.Qt.NoFocus)
        self.le_numberPointsSlewed.setAcceptDrops(False)
        self.le_numberPointsSlewed.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.le_numberPointsSlewed.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.le_numberPointsSlewed.setReadOnly(True)
        self.le_numberPointsSlewed.setObjectName("le_numberPointsSlewed")
        self.le_numberPointsSolved = QtWidgets.QLineEdit(self.groupBox)
        self.le_numberPointsSolved.setEnabled(False)
        self.le_numberPointsSolved.setGeometry(QtCore.QRect(70, 60, 26, 16))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.le_numberPointsSolved.setFont(font)
        self.le_numberPointsSolved.setMouseTracking(False)
        self.le_numberPointsSolved.setFocusPolicy(QtCore.Qt.NoFocus)
        self.le_numberPointsSolved.setAcceptDrops(False)
        self.le_numberPointsSolved.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.le_numberPointsSolved.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.le_numberPointsSolved.setReadOnly(True)
        self.le_numberPointsSolved.setObjectName("le_numberPointsSolved")
        self.bar_numberPointsSolved = QtWidgets.QProgressBar(self.groupBox)
        self.bar_numberPointsSolved.setGeometry(QtCore.QRect(145, 60, 201, 16))
        self.bar_numberPointsSolved.setMaximum(1000)
        self.bar_numberPointsSolved.setProperty("value", 1)
        self.bar_numberPointsSolved.setTextVisible(False)
        self.bar_numberPointsSolved.setObjectName("bar_numberPointsSolved")
        self.label_28 = QtWidgets.QLabel(self.groupBox)
        self.label_28.setGeometry(QtCore.QRect(10, 60, 66, 16))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_28.setFont(font)
        self.label_28.setObjectName("label_28")
        self.le_numberPointsToProcess1 = QtWidgets.QLineEdit(self.groupBox)
        self.le_numberPointsToProcess1.setEnabled(False)
        self.le_numberPointsToProcess1.setGeometry(QtCore.QRect(110, 20, 26, 16))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.le_numberPointsToProcess1.setFont(font)
        self.le_numberPointsToProcess1.setMouseTracking(False)
        self.le_numberPointsToProcess1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.le_numberPointsToProcess1.setAcceptDrops(False)
        self.le_numberPointsToProcess1.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.le_numberPointsToProcess1.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.le_numberPointsToProcess1.setReadOnly(True)
        self.le_numberPointsToProcess1.setObjectName("le_numberPointsToProcess1")
        self.le_numberPointsToProcess2 = QtWidgets.QLineEdit(self.groupBox)
        self.le_numberPointsToProcess2.setEnabled(False)
        self.le_numberPointsToProcess2.setGeometry(QtCore.QRect(110, 40, 26, 16))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.le_numberPointsToProcess2.setFont(font)
        self.le_numberPointsToProcess2.setMouseTracking(False)
        self.le_numberPointsToProcess2.setFocusPolicy(QtCore.Qt.NoFocus)
        self.le_numberPointsToProcess2.setAcceptDrops(False)
        self.le_numberPointsToProcess2.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.le_numberPointsToProcess2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.le_numberPointsToProcess2.setReadOnly(True)
        self.le_numberPointsToProcess2.setObjectName("le_numberPointsToProcess2")
        self.le_numberPointsToProcess3 = QtWidgets.QLineEdit(self.groupBox)
        self.le_numberPointsToProcess3.setEnabled(False)
        self.le_numberPointsToProcess3.setGeometry(QtCore.QRect(110, 60, 26, 16))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.le_numberPointsToProcess3.setFont(font)
        self.le_numberPointsToProcess3.setMouseTracking(False)
        self.le_numberPointsToProcess3.setFocusPolicy(QtCore.Qt.NoFocus)
        self.le_numberPointsToProcess3.setAcceptDrops(False)
        self.le_numberPointsToProcess3.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.le_numberPointsToProcess3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.le_numberPointsToProcess3.setReadOnly(True)
        self.le_numberPointsToProcess3.setObjectName("le_numberPointsToProcess3")
        self.le_numberPointsToProcess4 = QtWidgets.QLineEdit(self.groupBox)
        self.le_numberPointsToProcess4.setEnabled(False)
        self.le_numberPointsToProcess4.setGeometry(QtCore.QRect(110, 80, 26, 16))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(8)
        font.setBold(False)
        font.setWeight(50)
        self.le_numberPointsToProcess4.setFont(font)
        self.le_numberPointsToProcess4.setMouseTracking(False)
        self.le_numberPointsToProcess4.setFocusPolicy(QtCore.Qt.NoFocus)
        self.le_numberPointsToProcess4.setAcceptDrops(False)
        self.le_numberPointsToProcess4.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.le_numberPointsToProcess4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.le_numberPointsToProcess4.setReadOnly(True)
        self.le_numberPointsToProcess4.setObjectName("le_numberPointsToProcess4")
        self.label_78 = QtWidgets.QLabel(self.groupBox)
        self.label_78.setGeometry(QtCore.QRect(100, 20, 16, 16))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_78.setFont(font)
        self.label_78.setObjectName("label_78")
        self.label_79 = QtWidgets.QLabel(self.groupBox)
        self.label_79.setGeometry(QtCore.QRect(100, 40, 16, 16))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_79.setFont(font)
        self.label_79.setObjectName("label_79")
        self.label_80 = QtWidgets.QLabel(self.groupBox)
        self.label_80.setGeometry(QtCore.QRect(100, 60, 16, 16))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_80.setFont(font)
        self.label_80.setObjectName("label_80")
        self.label_82 = QtWidgets.QLabel(self.groupBox)
        self.label_82.setGeometry(QtCore.QRect(100, 80, 16, 16))
        font = QtGui.QFont()
        font.setFamily("MS Shell Dlg 2")
        font.setPointSize(10)
        font.setBold(False)
        font.setWeight(50)
        self.label_82.setFont(font)
        self.label_82.setObjectName("label_82")
        self.hemisphereBackground.raise_()
        self.btn_deletePoints.raise_()
        self.groupBox_2.raise_()
        self.hemisphere.raise_()
        self.hemisphereMoving.raise_()
        self.checkShowAlignmentStars.raise_()
        self.groupBox.raise_()

        self.retranslateUi(HemisphereDialog)
        QtCore.QMetaObject.connectSlotsByName(HemisphereDialog)

    def retranslateUi(self, HemisphereDialog):
        _translate = QtCore.QCoreApplication.translate
        HemisphereDialog.setWindowTitle(_translate("HemisphereDialog", "Hemisphere"))
        self.btn_deletePoints.setToolTip(_translate("HemisphereDialog", "<html><head/><body><p>Delete all points on coordinate window including Base / Model</p></body></html>"))
        self.btn_deletePoints.setText(_translate("HemisphereDialog", "Clear Points"))
        self.hemisphereBackground.setProperty("color", _translate("HemisphereDialog", "blue"))
        self.groupBox_2.setTitle(_translate("HemisphereDialog", "Operation mode"))
        self.btn_editNone.setText(_translate("HemisphereDialog", "Normal mode"))
        self.btn_editModelPoints.setText(_translate("HemisphereDialog", "Edit Model Points"))
        self.btn_editHorizonMask.setText(_translate("HemisphereDialog", "Edit Horizon Mask"))
        self.checkPolarAlignment.setText(_translate("HemisphereDialog", "Select PolarAlign"))
        self.checkShowAlignmentStars.setText(_translate("HemisphereDialog", "Show Align Stars"))
        self.groupBox.setTitle(_translate("HemisphereDialog", "Modeling progress"))
        self.label_100.setText(_translate("HemisphereDialog", "Slewed:"))
        self.le_numberPointsImaged.setToolTip(_translate("HemisphereDialog", "<html><head/><body><p><span style=\" font-size:10pt;\">Progress in modeling.</span></p></body></html>"))
        self.le_numberPointsImaged.setText(_translate("HemisphereDialog", "0"))
        self.label_77.setText(_translate("HemisphereDialog", "Imaged:"))
        self.label_81.setText(_translate("HemisphereDialog", "Program:"))
        self.le_numberPointsProcessed.setToolTip(_translate("HemisphereDialog", "<html><head/><body><p><span style=\" font-size:10pt;\">Progress in modeling.</span></p></body></html>"))
        self.le_numberPointsProcessed.setText(_translate("HemisphereDialog", "0"))
        self.bar_numberPointsSlewed.setFormat(_translate("HemisphereDialog", "%p%"))
        self.le_numberPointsSlewed.setToolTip(_translate("HemisphereDialog", "<html><head/><body><p><span style=\" font-size:10pt;\">Progress in modeling.</span></p></body></html>"))
        self.le_numberPointsSlewed.setText(_translate("HemisphereDialog", "0"))
        self.le_numberPointsSolved.setToolTip(_translate("HemisphereDialog", "<html><head/><body><p><span style=\" font-size:10pt;\">Progress in modeling.</span></p></body></html>"))
        self.le_numberPointsSolved.setText(_translate("HemisphereDialog", "0"))
        self.label_28.setText(_translate("HemisphereDialog", "Solved:"))
        self.le_numberPointsToProcess1.setToolTip(_translate("HemisphereDialog", "<html><head/><body><p><span style=\" font-size:10pt;\">Progress in modeling.</span></p></body></html>"))
        self.le_numberPointsToProcess1.setText(_translate("HemisphereDialog", "0"))
        self.le_numberPointsToProcess2.setToolTip(_translate("HemisphereDialog", "<html><head/><body><p><span style=\" font-size:10pt;\">Progress in modeling.</span></p></body></html>"))
        self.le_numberPointsToProcess2.setText(_translate("HemisphereDialog", "0"))
        self.le_numberPointsToProcess3.setToolTip(_translate("HemisphereDialog", "<html><head/><body><p><span style=\" font-size:10pt;\">Progress in modeling.</span></p></body></html>"))
        self.le_numberPointsToProcess3.setText(_translate("HemisphereDialog", "0"))
        self.le_numberPointsToProcess4.setToolTip(_translate("HemisphereDialog", "<html><head/><body><p><span style=\" font-size:10pt;\">Progress in modeling.</span></p></body></html>"))
        self.le_numberPointsToProcess4.setText(_translate("HemisphereDialog", "0"))
        self.label_78.setText(_translate("HemisphereDialog", "/"))
        self.label_79.setText(_translate("HemisphereDialog", "/"))
        self.label_80.setText(_translate("HemisphereDialog", "/"))
        self.label_82.setText(_translate("HemisphereDialog", "/"))

