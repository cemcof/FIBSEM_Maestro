# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'FIBSEM_Maestro_GUI.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout,
    QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QMenu, QMenuBar, QPushButton, QScrollArea,
    QSizePolicy, QSpacerItem, QStatusBar, QTabWidget,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.setWindowModality(Qt.NonModal)
        MainWindow.resize(1334, 1008)
        MainWindow.setStyleSheet(u"")
        self.actionLoad = QAction(MainWindow)
        self.actionLoad.setObjectName(u"actionLoad")
        self.actionSaveSettingsAs = QAction(MainWindow)
        self.actionSaveSettingsAs.setObjectName(u"actionSaveSettingsAs")
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.actionResize = QAction(MainWindow)
        self.actionResize.setObjectName(u"actionResize")
        self.actionEmail = QAction(MainWindow)
        self.actionEmail.setObjectName(u"actionEmail")
        self.actionSetFolderProject = QAction(MainWindow)
        self.actionSetFolderProject.setObjectName(u"actionSetFolderProject")
        self.actionLoadProject = QAction(MainWindow)
        self.actionLoadProject.setObjectName(u"actionLoadProject")
        self.actionSetFolder = QAction(MainWindow)
        self.actionSetFolder.setObjectName(u"actionSetFolder")
        self.actionEnable_buttons = QAction(MainWindow)
        self.actionEnable_buttons.setObjectName(u"actionEnable_buttons")
        self.actionSaveSettings = QAction(MainWindow)
        self.actionSaveSettings.setObjectName(u"actionSaveSettings")
        self.actionLoadSettings = QAction(MainWindow)
        self.actionLoadSettings.setObjectName(u"actionLoadSettings")
        self.actionErrorActions = QAction(MainWindow)
        self.actionErrorActions.setObjectName(u"actionErrorActions")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 1306, 874))
        self.gridLayout_2 = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.tabWidget = QTabWidget(self.scrollAreaWidgetContents)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setEnabled(True)
        self.tabWidget.setStyleSheet(u"")
        self.tabFib = QWidget()
        self.tabFib.setObjectName(u"tabFib")
        self.verticalLayout = QVBoxLayout(self.tabFib)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.fibVerticalLayout = QVBoxLayout()
        self.fibVerticalLayout.setObjectName(u"fibVerticalLayout")
        self.fibImageLabel = QLabel(self.tabFib)
        self.fibImageLabel.setObjectName(u"fibImageLabel")

        self.fibVerticalLayout.addWidget(self.fibImageLabel)

        self.label_3 = QLabel(self.tabFib)
        self.label_3.setObjectName(u"label_3")
        font = QFont()
        font.setBold(True)
        self.label_3.setFont(font)

        self.fibVerticalLayout.addWidget(self.label_3)

        self.fibFormLayout = QFormLayout()
        self.fibFormLayout.setObjectName(u"fibFormLayout")

        self.fibVerticalLayout.addLayout(self.fibFormLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.getFibImagePushButton = QPushButton(self.tabFib)
        self.getFibImagePushButton.setObjectName(u"getFibImagePushButton")

        self.horizontalLayout_3.addWidget(self.getFibImagePushButton)

        self.setFibFiducialPushButton = QPushButton(self.tabFib)
        self.setFibFiducialPushButton.setObjectName(u"setFibFiducialPushButton")

        self.horizontalLayout_3.addWidget(self.setFibFiducialPushButton)

        self.setFibAreaPushButton = QPushButton(self.tabFib)
        self.setFibAreaPushButton.setObjectName(u"setFibAreaPushButton")

        self.horizontalLayout_3.addWidget(self.setFibAreaPushButton)

        self.makeSlicePushButton = QPushButton(self.tabFib)
        self.makeSlicePushButton.setObjectName(u"makeSlicePushButton")

        self.horizontalLayout_3.addWidget(self.makeSlicePushButton)

        self.loadFibSettingsPushButton = QPushButton(self.tabFib)
        self.loadFibSettingsPushButton.setObjectName(u"loadFibSettingsPushButton")

        self.horizontalLayout_3.addWidget(self.loadFibSettingsPushButton)


        self.fibVerticalLayout.addLayout(self.horizontalLayout_3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.fibVerticalLayout.addItem(self.verticalSpacer_2)


        self.verticalLayout.addLayout(self.fibVerticalLayout)

        self.tabWidget.addTab(self.tabFib, "")
        self.tabSem = QWidget()
        self.tabSem.setObjectName(u"tabSem")
        self.verticalLayout1 = QVBoxLayout(self.tabSem)
        self.verticalLayout1.setObjectName(u"verticalLayout1")
        self.semVerticalLayout = QVBoxLayout()
        self.semVerticalLayout.setObjectName(u"semVerticalLayout")
        self.imageLabel = QLabel(self.tabSem)
        self.imageLabel.setObjectName(u"imageLabel")

        self.semVerticalLayout.addWidget(self.imageLabel)

        self.label_2 = QLabel(self.tabSem)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setFont(font)

        self.semVerticalLayout.addWidget(self.label_2)

        self.semFormLayout = QFormLayout()
        self.semFormLayout.setObjectName(u"semFormLayout")

        self.semVerticalLayout.addLayout(self.semFormLayout)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.alignedImagingDirectionPushButton = QPushButton(self.tabSem)
        self.alignedImagingDirectionPushButton.setObjectName(u"alignedImagingDirectionPushButton")

        self.horizontalLayout_7.addWidget(self.alignedImagingDirectionPushButton)

        self.alignedSampleSurfacePushButton = QPushButton(self.tabSem)
        self.alignedSampleSurfacePushButton.setObjectName(u"alignedSampleSurfacePushButton")

        self.horizontalLayout_7.addWidget(self.alignedSampleSurfacePushButton)


        self.semVerticalLayout.addLayout(self.horizontalLayout_7)


        self.verticalLayout1.addLayout(self.semVerticalLayout)

        self.semImagingVerticalLayout = QVBoxLayout()
        self.semImagingVerticalLayout.setObjectName(u"semImagingVerticalLayout")
        self.label = QLabel(self.tabSem)
        self.label.setObjectName(u"label")
        font1 = QFont()
        font1.setBold(True)
        font1.setItalic(False)
        self.label.setFont(font1)
        self.label.setTextFormat(Qt.AutoText)

        self.semImagingVerticalLayout.addWidget(self.label)

        self.imageSettingsFormLayout = QFormLayout()
        self.imageSettingsFormLayout.setObjectName(u"imageSettingsFormLayout")

        self.semImagingVerticalLayout.addLayout(self.imageSettingsFormLayout)

        self.label_6 = QLabel(self.tabSem)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setFont(font1)

        self.semImagingVerticalLayout.addWidget(self.label_6)

        self.imageCriterionFormLayout = QFormLayout()
        self.imageCriterionFormLayout.setObjectName(u"imageCriterionFormLayout")

        self.semImagingVerticalLayout.addLayout(self.imageCriterionFormLayout)


        self.verticalLayout1.addLayout(self.semImagingVerticalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.getImagePushButton = QPushButton(self.tabSem)
        self.getImagePushButton.setObjectName(u"getImagePushButton")

        self.horizontalLayout.addWidget(self.getImagePushButton)

        self.setImagingPushButton = QPushButton(self.tabSem)
        self.setImagingPushButton.setObjectName(u"setImagingPushButton")

        self.horizontalLayout.addWidget(self.setImagingPushButton)

        self.testImagingPushButton = QPushButton(self.tabSem)
        self.testImagingPushButton.setObjectName(u"testImagingPushButton")

        self.horizontalLayout.addWidget(self.testImagingPushButton)

        self.fastScanCheckBox = QCheckBox(self.tabSem)
        self.fastScanCheckBox.setObjectName(u"fastScanCheckBox")
        self.fastScanCheckBox.setChecked(True)

        self.horizontalLayout.addWidget(self.fastScanCheckBox)


        self.verticalLayout1.addLayout(self.horizontalLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout1.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.tabSem, "")
        self.tabAutofunctions = QWidget()
        self.tabAutofunctions.setObjectName(u"tabAutofunctions")
        self.verticalLayout_2 = QVBoxLayout(self.tabAutofunctions)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.autofunctionsVerticalLayout = QVBoxLayout()
        self.autofunctionsVerticalLayout.setObjectName(u"autofunctionsVerticalLayout")
        self.autofunctionsImageLabel = QLabel(self.tabAutofunctions)
        self.autofunctionsImageLabel.setObjectName(u"autofunctionsImageLabel")

        self.autofunctionsVerticalLayout.addWidget(self.autofunctionsImageLabel)

        self.autofunctionLabel = QLabel(self.tabAutofunctions)
        self.autofunctionLabel.setObjectName(u"autofunctionLabel")

        self.autofunctionsVerticalLayout.addWidget(self.autofunctionLabel)

        self.autofunctionComboBox = QComboBox(self.tabAutofunctions)
        self.autofunctionComboBox.setObjectName(u"autofunctionComboBox")

        self.autofunctionsVerticalLayout.addWidget(self.autofunctionComboBox)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.cloneAutofunctionPushButton = QPushButton(self.tabAutofunctions)
        self.cloneAutofunctionPushButton.setObjectName(u"cloneAutofunctionPushButton")

        self.horizontalLayout_4.addWidget(self.cloneAutofunctionPushButton)

        self.removeAutofunctionPushButton = QPushButton(self.tabAutofunctions)
        self.removeAutofunctionPushButton.setObjectName(u"removeAutofunctionPushButton")

        self.horizontalLayout_4.addWidget(self.removeAutofunctionPushButton)


        self.autofunctionsVerticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.setAfAreaPushButton = QPushButton(self.tabAutofunctions)
        self.setAfAreaPushButton.setObjectName(u"setAfAreaPushButton")

        self.horizontalLayout_6.addWidget(self.setAfAreaPushButton)

        self.testAfPushButton = QPushButton(self.tabAutofunctions)
        self.testAfPushButton.setObjectName(u"testAfPushButton")

        self.horizontalLayout_6.addWidget(self.testAfPushButton)


        self.autofunctionsVerticalLayout.addLayout(self.horizontalLayout_6)

        self.autofunctionFormLayout = QFormLayout()
        self.autofunctionFormLayout.setObjectName(u"autofunctionFormLayout")

        self.autofunctionsVerticalLayout.addLayout(self.autofunctionFormLayout)

        self.label_4 = QLabel(self.tabAutofunctions)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setFont(font)

        self.autofunctionsVerticalLayout.addWidget(self.label_4)

        self.autofunctionCriteriumFormLayout = QFormLayout()
        self.autofunctionCriteriumFormLayout.setObjectName(u"autofunctionCriteriumFormLayout")

        self.autofunctionsVerticalLayout.addLayout(self.autofunctionCriteriumFormLayout)

        self.label_5 = QLabel(self.tabAutofunctions)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setFont(font)

        self.autofunctionsVerticalLayout.addWidget(self.label_5)

        self.autofunctionImagingFormLayout = QFormLayout()
        self.autofunctionImagingFormLayout.setObjectName(u"autofunctionImagingFormLayout")

        self.autofunctionsVerticalLayout.addLayout(self.autofunctionImagingFormLayout)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.autofunctionsVerticalLayout.addItem(self.verticalSpacer_3)


        self.verticalLayout_2.addLayout(self.autofunctionsVerticalLayout)

        self.tabWidget.addTab(self.tabAutofunctions, "")
        self.tabDriftCorrection = QWidget()
        self.tabDriftCorrection.setObjectName(u"tabDriftCorrection")
        self.maskingVerticalLayout = QVBoxLayout(self.tabDriftCorrection)
        self.maskingVerticalLayout.setObjectName(u"maskingVerticalLayout")
        self.driftcorrVerticalLayout = QVBoxLayout()
        self.driftcorrVerticalLayout.setObjectName(u"driftcorrVerticalLayout")
        self.driftcorrImageLabel = QLabel(self.tabDriftCorrection)
        self.driftcorrImageLabel.setObjectName(u"driftcorrImageLabel")

        self.driftcorrVerticalLayout.addWidget(self.driftcorrImageLabel)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.addDriftCorrPushButton = QPushButton(self.tabDriftCorrection)
        self.addDriftCorrPushButton.setObjectName(u"addDriftCorrPushButton")

        self.horizontalLayout_5.addWidget(self.addDriftCorrPushButton)

        self.removeDriftCorrPushButton = QPushButton(self.tabDriftCorrection)
        self.removeDriftCorrPushButton.setObjectName(u"removeDriftCorrPushButton")

        self.horizontalLayout_5.addWidget(self.removeDriftCorrPushButton)

        self.updateDriftCorrPushButton = QPushButton(self.tabDriftCorrection)
        self.updateDriftCorrPushButton.setObjectName(u"updateDriftCorrPushButton")

        self.horizontalLayout_5.addWidget(self.updateDriftCorrPushButton)

        self.testDriftCorrPushButton = QPushButton(self.tabDriftCorrection)
        self.testDriftCorrPushButton.setObjectName(u"testDriftCorrPushButton")

        self.horizontalLayout_5.addWidget(self.testDriftCorrPushButton)

        self.driftCorrUpdateImagePushButton = QPushButton(self.tabDriftCorrection)
        self.driftCorrUpdateImagePushButton.setObjectName(u"driftCorrUpdateImagePushButton")

        self.horizontalLayout_5.addWidget(self.driftCorrUpdateImagePushButton)


        self.driftcorrVerticalLayout.addLayout(self.horizontalLayout_5)


        self.maskingVerticalLayout.addLayout(self.driftcorrVerticalLayout)

        self.driftCorrFormLayout = QFormLayout()
        self.driftCorrFormLayout.setObjectName(u"driftCorrFormLayout")

        self.maskingVerticalLayout.addLayout(self.driftCorrFormLayout)

        self.label_7 = QLabel(self.tabDriftCorrection)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font)

        self.maskingVerticalLayout.addWidget(self.label_7)

        self.driftCorrImagingFormLayout = QFormLayout()
        self.driftCorrImagingFormLayout.setObjectName(u"driftCorrImagingFormLayout")

        self.maskingVerticalLayout.addLayout(self.driftCorrImagingFormLayout)

        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.maskingVerticalLayout.addItem(self.verticalSpacer_5)

        self.tabWidget.addTab(self.tabDriftCorrection, "")
        self.tabAcb = QWidget()
        self.tabAcb.setObjectName(u"tabAcb")
        self.acbVerticalLayout = QVBoxLayout(self.tabAcb)
        self.acbVerticalLayout.setObjectName(u"acbVerticalLayout")
        self.acbVerticalLayout_2 = QVBoxLayout()
        self.acbVerticalLayout_2.setObjectName(u"acbVerticalLayout_2")
        self.acbImageLabel = QLabel(self.tabAcb)
        self.acbImageLabel.setObjectName(u"acbImageLabel")

        self.acbVerticalLayout_2.addWidget(self.acbImageLabel)

        self.setAcbPushButton = QPushButton(self.tabAcb)
        self.setAcbPushButton.setObjectName(u"setAcbPushButton")

        self.acbVerticalLayout_2.addWidget(self.setAcbPushButton)

        self.acbFormLayout = QFormLayout()
        self.acbFormLayout.setObjectName(u"acbFormLayout")

        self.acbVerticalLayout_2.addLayout(self.acbFormLayout)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.acbVerticalLayout_2.addItem(self.verticalSpacer_4)


        self.acbVerticalLayout.addLayout(self.acbVerticalLayout_2)

        self.tabWidget.addTab(self.tabAcb, "")

        self.gridLayout_2.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout.addWidget(self.scrollArea, 0, 0, 1, 1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.runPushButton = QPushButton(self.centralwidget)
        self.runPushButton.setObjectName(u"runPushButton")

        self.horizontalLayout_2.addWidget(self.runPushButton)

        self.stopPushButton = QPushButton(self.centralwidget)
        self.stopPushButton.setObjectName(u"stopPushButton")

        self.horizontalLayout_2.addWidget(self.stopPushButton)


        self.gridLayout.addLayout(self.horizontalLayout_2, 1, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1334, 31))
        self.menuSetting = QMenu(self.menubar)
        self.menuSetting.setObjectName(u"menuSetting")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuCommand = QMenu(self.menubar)
        self.menuCommand.setObjectName(u"menuCommand")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuSetting.menuAction())
        self.menubar.addAction(self.menuCommand.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuSetting.addSeparator()
        self.menuSetting.addAction(self.actionLoadSettings)
        self.menuSetting.addAction(self.actionSaveSettings)
        self.menuSetting.addAction(self.actionSaveSettingsAs)
        self.menuSetting.addSeparator()
        self.menuSetting.addAction(self.actionEmail)
        self.menuSetting.addAction(self.actionErrorActions)
        self.menuHelp.addAction(self.actionAbout)
        self.menuCommand.addAction(self.actionEnable_buttons)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(3)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"FIBSEM_Maestro v ", None))
        self.actionLoad.setText(QCoreApplication.translate("MainWindow", u"Load Settings...", None))
        self.actionSaveSettingsAs.setText(QCoreApplication.translate("MainWindow", u"Save Settings As...", None))
        self.actionAbout.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.actionResize.setText(QCoreApplication.translate("MainWindow", u"Resize", None))
        self.actionEmail.setText(QCoreApplication.translate("MainWindow", u"Email...", None))
        self.actionSetFolderProject.setText(QCoreApplication.translate("MainWindow", u"Set folder", None))
        self.actionLoadProject.setText(QCoreApplication.translate("MainWindow", u"Load", None))
        self.actionSetFolder.setText(QCoreApplication.translate("MainWindow", u"Set Folder...", None))
        self.actionEnable_buttons.setText(QCoreApplication.translate("MainWindow", u"Enable buttons", None))
        self.actionSaveSettings.setText(QCoreApplication.translate("MainWindow", u"Save Settings", None))
        self.actionLoadSettings.setText(QCoreApplication.translate("MainWindow", u"Load Settings", None))
        self.actionErrorActions.setText(QCoreApplication.translate("MainWindow", u"Error actions...", None))
        self.fibImageLabel.setText("")
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.getFibImagePushButton.setText(QCoreApplication.translate("MainWindow", u"Get image", None))
        self.setFibFiducialPushButton.setText(QCoreApplication.translate("MainWindow", u"Set fiducial", None))
        self.setFibAreaPushButton.setText(QCoreApplication.translate("MainWindow", u"Set slicing area", None))
        self.makeSlicePushButton.setText(QCoreApplication.translate("MainWindow", u"Make slice", None))
        self.loadFibSettingsPushButton.setText(QCoreApplication.translate("MainWindow", u"Load settings", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabFib), QCoreApplication.translate("MainWindow", u"FIB", None))
        self.imageLabel.setText("")
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Acquisition", None))
        self.alignedImagingDirectionPushButton.setText(QCoreApplication.translate("MainWindow", u"Aligned by imaging direction (38\u00b0)", None))
        self.alignedSampleSurfacePushButton.setText(QCoreApplication.translate("MainWindow", u"Aligned along sample surface (38\u00b0)", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Imaging", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"Criterion", None))
        self.getImagePushButton.setText(QCoreApplication.translate("MainWindow", u"Get image", None))
        self.setImagingPushButton.setText(QCoreApplication.translate("MainWindow", u"Set imaging", None))
        self.testImagingPushButton.setText(QCoreApplication.translate("MainWindow", u"Test imaging", None))
        self.fastScanCheckBox.setText(QCoreApplication.translate("MainWindow", u"Fast scan", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabSem), QCoreApplication.translate("MainWindow", u"SEM", None))
        self.autofunctionsImageLabel.setText("")
        self.autofunctionLabel.setText(QCoreApplication.translate("MainWindow", u"Autofunction", None))
        self.cloneAutofunctionPushButton.setText(QCoreApplication.translate("MainWindow", u"Clone autofunction", None))
        self.removeAutofunctionPushButton.setText(QCoreApplication.translate("MainWindow", u"Remove autofunction", None))
        self.setAfAreaPushButton.setText(QCoreApplication.translate("MainWindow", u"Set af area", None))
        self.testAfPushButton.setText(QCoreApplication.translate("MainWindow", u"Test", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Criterium", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Imaging", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabAutofunctions), QCoreApplication.translate("MainWindow", u"Autofunctions", None))
        self.driftcorrImageLabel.setText("")
        self.addDriftCorrPushButton.setText(QCoreApplication.translate("MainWindow", u"Set drift correction area", None))
        self.removeDriftCorrPushButton.setText(QCoreApplication.translate("MainWindow", u"Remove areas", None))
        self.updateDriftCorrPushButton.setText(QCoreApplication.translate("MainWindow", u"Update areas", None))
        self.testDriftCorrPushButton.setText(QCoreApplication.translate("MainWindow", u"Test", None))
        self.driftCorrUpdateImagePushButton.setText(QCoreApplication.translate("MainWindow", u"Update image", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Imaging", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabDriftCorrection), QCoreApplication.translate("MainWindow", u"Drift corr", None))
        self.acbImageLabel.setText("")
        self.setAcbPushButton.setText(QCoreApplication.translate("MainWindow", u"Set ACB area", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabAcb), QCoreApplication.translate("MainWindow", u"ACB", None))
        self.runPushButton.setText(QCoreApplication.translate("MainWindow", u"Run", None))
        self.stopPushButton.setText(QCoreApplication.translate("MainWindow", u"Stop", None))
        self.menuSetting.setTitle(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
        self.menuCommand.setTitle(QCoreApplication.translate("MainWindow", u"Command", None))
    # retranslateUi

