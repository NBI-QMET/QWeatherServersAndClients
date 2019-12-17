#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Gui for the Blackfly Camera

"""


from PyQt5.QtWidgets import *
from PyQt5 import QtGui,QtCore
import sys
import asyncio
from qweather import QWeatherClient
import time
import numpy as np
import pyqtgraph as pg
from matplotlib import cm
import os
import subprocess
from StrontiumBrainGUI import SrBrainGui, mySpinbox
from scipy.optimize import curve_fit
import datetime




__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '4.0'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'

class mySpinbox(QDoubleSpinBox):
    def __init__(self):
        super().__init__()
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.setDecimals(4)
        self.setMaximum(3000)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English,QtCore.QLocale.UnitedStates)) #set locale to us, so decimal point means decimal point


class CamGui(QWidget):

    def __init__(self,loop = None):
        super().__init__()
        QWeatherStationIP = "tcp://10.90.61.13:5559"
        name = 'CameraGUI'
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        self.client = QWeatherClient(QWeatherStationIP,name=name,loop=self.loop)
        self.camprocess = None
        self.SrBrainprocess = None
        self.logpath = 'Z:\Sr1\MOT Image Logging'

        self.setWindowTitle('BlackFly Camera GUI')
        self.setFont(QtGui.QFont('Helvetica',12))
        self.initialize_GUI()
        self.restore_GUI()
        self.saving = False
        self.TempMeasuring = False
        #sys.stdout = EmittingStream(textWritten = self.write_logmessage)
        #sys.stderr = EmittingStream(textWritten = self.write_logmessage)
        self.loop.create_task(self.client.run())

  


    def initialize_GUI(self):
        self.resultarray = []
        logpanel = self.make_logpanel()
        imagepanel = self.make_imagepanel()


        settingspanel =self.make_settingspanel()
        self.Srbrainpanel = SrBrainGui()#self.make_SRbrainpanel()
        #self.Srbrain = self.Srbrainpanel.Srbrain
        buttonpanel = self.make_buttonspanel()
        temppanel = self.make_temppanel()
        
        tabwig = QTabWidget()
        tabwig.addTab(settingspanel,'Settings')
        tabwig.addTab(self.Srbrainpanel,'Timings')
        tabwig.addTab(logpanel,'Log')
        tabwig.addTab(temppanel,'Temperature')


        layout = QGridLayout()
        layout.addWidget(imagepanel,0,0)

        layout.addWidget(tabwig,1,0)
        layout.addWidget(buttonpanel,2,0)
        self.setLayout(layout)

        self.show()

    def make_logpanel(self):
        panel = QFrame()
        camstart = QPushButton('Start Cam Server')
        Srstart = QPushButton('Start Sr Brain Server')
        camkill = QPushButton('Stop Cam Server')
        Srkill = QPushButton('Stop Sr Brain Server')
        self.logtextfield = QTextEdit()
        self.logtextfield.setReadOnly(True)
        camstart.pressed.connect(lambda : self.start_server('Cam'))
        camkill.pressed.connect(lambda: self.kill_server('Cam'))
        Srstart.pressed.connect(lambda: self.start_server('Brain'))
        Srkill.pressed.connect(lambda: self.kill_server('Brain'))
        layout = QGridLayout()
        layout.addWidget(QLabel('Log Print'),0,0)
        layout.addWidget(camstart,1,0)
        layout.addWidget(Srstart,1,7)
        layout.addWidget(camkill,1,1)
        layout.addWidget(Srkill,1,8)

        layout.addWidget(self.logtextfield,3,0,5,8)

        panel.setLayout(layout)
        camstart.click()
        Srstart.click()
        time.sleep(2)
        self.camera = self.client.BlackflyCamera
        self.Srbrain = self.client.StrontiumBrain
        return panel

    def start_server(self,CamOrBrain):
        if CamOrBrain is 'Cam':
            if self.camprocess is None:
                self.camprocess = QtCore.QProcess()
                self.camprocess.readyReadStandardOutput.connect(lambda : self.read_output(self.camprocess,'CAM'))
                self.camprocess.started.connect(lambda : self.write_logmessage('CAM: Server started')) 
                self.camprocess.finished.connect(lambda : self.write_logmessage('CAM: Server stopped'))
                self.camprocess.setProcessChannelMode(QtCore.QProcess.MergedChannels)
                self.camprocess.start('python',['-u','Z:/Dataprogrammer/Qweather/Servers/BlackFlyCameraServer.py'])
            else:
                self.write_logmessage('CAM: Cannot start server, as it is already running')
        elif CamOrBrain is 'Brain':
            if self.SrBrainprocess is None:
                self.SrBrainprocess = QtCore.QProcess()
                self.SrBrainprocess.readyReadStandardOutput.connect(lambda : self.read_output(self.SrBrainprocess,'SrBrain'))
                self.SrBrainprocess.started.connect(lambda : self.write_logmessage('SrBrain: Server started')) 
                self.SrBrainprocess.finished.connect(lambda : self.write_logmessage('SrBrain: Server stopped'))
                self.SrBrainprocess.setProcessChannelMode(QtCore.QProcess.MergedChannels)
                self.SrBrainprocess.start('python',['-u','Z:/Dataprogrammer/Qweather/Servers/Ni6259.py'])
            else:
                self.write_logmessage('SrBrain: Cannot start server, as it is already running')

    def kill_server(self,CamOrBrain):
        if CamOrBrain is 'Cam':
            if self.camprocess is not None:
                self.camprocess.terminate()
                self.camprocess = None
                self.write_logmessage('CAM: Terminated server')
            else:
               self.write_logmessage('CAM: Cannot terminate CAM, as it is not running')
        elif CamOrBrain is 'Brain':
            if self.SrBrainprocess is not None:
                self.SrBrainprocess.terminate()
                self.SrBrainprocess = None
                self.write_logmessage('SrBrain: Terminated server')
            else:
               self.write_logmessage('SrBrain: Cannot terminate SrBrain, as it is not running')

    def write_logmessage(self,message,color = None):
        self.logtextfield.append(message)

    def read_output(self,process,msgprefix):
        data = process.readAllStandardOutput()
        self.write_logmessage(msgprefix + ':' + str(data, 'utf-8'))    

    async def grab_image(self,stop):
        while not stop.is_set():
            image = await self.camera.getImage()
            if image is None:
                print('None')
                pass
            else:
                self.update_images(image)


    async def get_single_image(self,sender):
        self.camera.acquisitionMode('single')
        image = await self.camera.acquireSingleImage()
        thisimage=QtGui.QImage(image,1920,1200,1920,QtGui.QImage.Format_Grayscale8)
        self.update_images(thisimage)



    def wait_for_trigger_clicked(self,state):
        if state:
            self.imagehistoryarray = []
            if self.SaveImagesBox.value() is not 0:
                self.saving=True
                self.resultarray = []
            self.sender().setText('Waiting for trigger (press to abort)')
            self.camera.acquisitionMode('cont')
            self.camera.triggerMode('on')
            self.camera.triggerSource('hardware')
            self.stopcont = asyncio.Event()
            self.camera.beginAcquisition()
            self.loop.create_task(self.grab_image(self.stopcont))
        if not state:
            self.sender().setText('Wait for trigger')
            self.camera.endAcquisition()
            self.camera.triggerMode('off')
            self.stopcont.set()

    def measure_clicked(self,state):
        if state:
            self.sender().setText('Measurement in progress, press to cancel')
            Tlist = np.arange(self.TStartbox.value(),self.TStopbox.value(),self.dTbox.value())
            self.measuretask = self.loop.create_task(self.startTempMeas(Tlist))
        if not state:
            if self.measuretask is not None:
                self.measuretask.cancel()
                self.measuretask = None
            self.sender().setText('Start Temperature Measurement')

    def update_images(self,image):
        image = image.astype(float)
        image = image.reshape(self.expectedPixels[1],self.expectedPixels[0])
        image = np.transpose(image)
        if len(self.imagehistoryarray) > 1:
            self.imagehistoryarray = []
        self.imagehistoryarray.insert(0,image)
        if len(self.imagehistoryarray) == 2:
            diffim = (self.imagehistoryarray[0]-self.imagehistoryarray[1])
            self.mainImage.setImage(diffim)
            smallim1 = self.imagehistoryarray[0]
            smallim2 = self.imagehistoryarray[1]
            for i, anim in enumerate([smallim1,smallim2]):
                self.imagehistorycontainer[i].setImage(anim)
            self.update_histogram(diffim)
            if self.saving or self.TempMeasuring:
                self.resultarray.append(self.ROI.getArrayRegion(diffim,self.mainImage))
                if self.TempMeasuring:
                    self.progressbar.setValue(self.progressbar.value() +1)

                if len(self.resultarray) >= self.SaveImagesBox.value():
                    self.waitbutton.toggle()
                    date = datetime.datetime.now().strftime('%Y%m%d')
                    tm = datetime.datetime.now().strftime('%H%M_%S')
                    self.savepath = self.logpath + '\\' + date + '\\' + tm
                    self.save_images(self.resultarray,'')
                    self.saving=False
                    self.SaveImagesBox.setValue(0)

                if len(self.resultarray) >= self.Npicturebox.value():
                    self.TempMeasuring = False
            
    def update_histogram(self,diffimage):
        ROIimage = self.ROI.getArrayRegion(diffimage,self.mainImage)
        coords = self.ROI.parentBounds()
        xsize = np.size(ROIimage,0)
        ysize = np.size(ROIimage,1)
        try:
            xdata = ROIimage[:,int(ysize/2+0.5)]
            ydata = ROIimage[int(xsize/2+0.5),:]

            self.histogramplot[0].setData(x = list(range(0,xsize)), y = xdata) #red
            self.histogramplot[1].setData(x = list(range(0,ysize)), y = ydata) #green

            self.xline.setData(x = [coords.x(),coords.x()+coords.width()],y = [coords.y()+coords.height()/2, coords.y()+coords.height()/2]) #red
            
            self.yline.setData(x = [coords.x()+coords.width()/2, coords.x()+coords.width()/2],y = [coords.y(),coords.y()+coords.height()]) #green
        except Exception as e:
            print(e)



    def make_imagepanel(self):
        self.expectedPixels = (1920,1200)
        panel = QFrame()
        panel.setFrameStyle(QFrame.Raised | QFrame.Panel)
        MainPwig = pg.PlotWidget()

        # Get the colormap
        colormap = cm.get_cmap("nipy_spectral")  # cm.get_cmap("CMRmap")
        colormap._init()
        self.lut = (colormap._lut * 255).view(np.ndarray)  # Convert matplotlib colormap from 0-1 to 0 -255 for Qt

        self.mainImage = pg.ImageItem()
        self.mainImage.setLookupTable(self.lut)
        MainPwig.addItem(self.mainImage)
        MainPwig.setMaximumSize(640,400)
        sp = MainPwig.sizePolicy()
        sp.setHorizontalPolicy(QSizePolicy.Fixed)
        sp.setVerticalPolicy(QSizePolicy.Fixed)
        MainPwig.setSizePolicy( sp )

        layout = QGridLayout()

        self.imagehistorycontainer = [pg.ImageItem() for i in range(2)]#[QLabel() for i in range(3)]
        for animage in self.imagehistorycontainer:
            animage.setLookupTable(self.lut)

        self.imagehistoryarray = [None,None,None,None]
        for i,awidget in enumerate([pg.PlotWidget() for i in range(2)]):     
            awidget.setMaximumSize(213,133)
            sp = awidget.sizePolicy()
            sp.setHorizontalPolicy(QSizePolicy.Fixed)#setHeightForWidth( True)
            sp.setVerticalPolicy(QSizePolicy.Fixed)
            awidget.setSizePolicy( sp )
            awidget.addItem(self.imagehistorycontainer[i])
            layout.addWidget(awidget,i+1,4)



        #Histogramplot

        histplot = pg.PlotWidget()
        histplot.setMaximumSize(213,133)
        sp = histplot.sizePolicy()
        sp.setHorizontalPolicy(QSizePolicy.Fixed)#setHeightForWidth( True)
        sp.setVerticalPolicy(QSizePolicy.Fixed)
        histplot.setSizePolicy( sp )
        self.histogramplot = [histplot.plot(),histplot.plot(),histplot.plot(),histplot.plot()]
        self.histogramplot[0].setPen((255,0,0))
        self.histogramplot[1].setPen((0,255,0))
        self.histogramplot[2].setPen((255,0,0))
        self.histogramplot[3].setPen((0,255,0))
        self.xline = MainPwig.plot()
        self.yline = MainPwig.plot()
        self.xline.setPen((255,0,0))
        self.yline.setPen((0,255,0))


        #Region of interest
        self.ROI = pg.ROI([450,100],[400,500],pen=pg.mkPen(color='k',width=2))
        MainPwig.addItem(self.ROI)
        ## handles scaling horizontally around center
        self.ROI.addScaleHandle([1, 0.5], [0.5, 0.5])
        self.ROI.addScaleHandle([0, 0.5], [0.5, 0.5])

        ## handles scaling vertically from opposite edge
        self.ROI.addScaleHandle([0.5, 0], [0.5, 1])
        self.ROI.addScaleHandle([0.5, 1], [0.5, 0])

        ## handles scaling both vertically and horizontally
        self.ROI.addScaleHandle([1, 1], [0, 0])
        self.ROI.addScaleHandle([0, 0], [1, 1])




        layout.addWidget(histplot,3,4)


        layout.addWidget(QLabel('Current image'),0,1)
        layout.addWidget(MainPwig,1,0,3,3)

        layout.addWidget(QLabel('NoMot'),1,5)
        layout.addWidget(QLabel('MOT'),2,5)
        layout.setAlignment(QtCore.Qt.AlignCenter)

        panel.setLayout(layout)
        return panel

    def make_buttonspanel(self):
        panel = QFrame()
        self.measurebutton = QPushButton('Start Temperature Measurement')
        self.measurebutton.setCheckable(True)
        self.waitbutton = QPushButton('Wait for Trigger')
        self.waitbutton.setCheckable(True)
        self.waitbutton.toggled.connect(self.wait_for_trigger_clicked)
        self.measurebutton.clicked.connect(self.measure_clicked)


        layout = QGridLayout()
        layout.addWidget(self.measurebutton,0,0)
        layout.addWidget(self.waitbutton,0,2)

        panel.setLayout(layout)
        return panel

    def check_autobutton(self,state,box):
        name = self.sender().text().split()[1]
        print(name,state,box)
        if state:
            box.setReadOnly(True)
            box.setKeyboardTracking(False)
            if name == 'Exposure':
                self.camera.exposureAuto('on')
            elif name == 'Gain':
                self.camera.gainAuto('on')
            elif name == 'level':
                self.camera.BlacklevelAuto('on')
        else:
            box.setReadOnly(False)
            box.setKeyboardTracking(True)
            if name == 'Exposure':
                self.camera.exposureAuto('off')
                #box.setValue(self.camera.exposure())
            elif name == 'Gain':
                print('Turning autogain off')
                self.camera.gainAuto('off')
                #box.setValue(self.camera.gain())
            elif name == 'Level':
                self.camera.blacklevelAuto('off')
                #box.setValue(self.camera.blacklevel())

    

    def change_bitmode(self,state):
        if state:
            self.sender().setText('12 bit')
            self.camera.bitFormat(12)
        else:
            self.sender().setText('8 bit')
            self.camera.bitFormat(8)


    def make_settingspanel(self):
       #Load current settings from the camera
        CamExp = self.camera.exposure()
        CamExpAuto = self.camera.exposureAuto()
        CamGain = self.camera.gain()
        CamGainAuto = self.camera.gainAuto()
        CamBlack = self.camera.blacklevel()
        CamBit = self.camera.bitFormat()
        CamBin = self.camera.binning()

        panel = QFrame()
        Expolabel = QLabel('Exposure Time')
        Expobox = QDoubleSpinBox()
        Expobox.setValue(CamExp/1000)
        Expobox.setDecimals(3)
        Expobox.setRange(0.019,3900)
        Expobox.setSuffix(' ms')
        ExpoAuto = QCheckBox('Auto Exposure')
        if CamExpAuto == 'on':
            ExpoAuto.setChecked(True)
        else:
            ExpoAuto.setChecked(False)
        Gainlabel = QLabel('Gain Factor')
        Gainbox = QDoubleSpinBox()
        Gainbox.setValue(CamGain)
        Gainbox.setSuffix(' dB')
        Gainbox.setDecimals(2)
        Gainbox.setRange(0.00,29.99)
        GainAuto = QCheckBox('Auto Gain')
        if CamGainAuto == 'on':
            GainAuto.setChecked(True)
        BlackLevellabel = QLabel('Black Level')
        BlackLevelbox = QSpinBox()
        BlackLevelbox.setValue(CamBlack)
        BlackLevelbox.setRange(0,100)
        BlackLevelbox.setSuffix(' %')

        bitBut = QPushButton('8 Bit')
        bitBut.setCheckable(True)
        if CamBit[0] == 'Mono8':
            bitBut.setChecked(False)
        bitBut.toggled.connect(self.change_bitmode)

        binDrop = QComboBox()
        binDrop.addItems(['No binning','2x2 binning','4x4 binning'])
        if CamBin == (2,2):
            binDrop.setCurrentIndex(1)
            self.expectedPixels = (960,600)
        elif CamBin == (4,4):
            binDrop.setCurrentIndex(2)
            self.expectedPixels = (480,300)

        binDrop.currentTextChanged.connect(self.change_binning)

        self.SaveImagesBox = QSpinBox()
        savelabel = QLabel('Number of images to save (0 to disable)')
        self.saveBar = QProgressBar()
        self.saveBar.hide()
        self.saveLocLabel = QLabel()



        self.autobuttonlist = []
        for abut,abox in [(ExpoAuto,Expobox),(GainAuto,Gainbox)]:
            if abut.isChecked():
                abox.setKeyboardTracking(False)
                abox.setReadOnly(True)
            abut.toggled.connect(lambda state,box = abox: self.check_autobutton(state,box))
            self.autobuttonlist.append(abut)

        Expobox.valueChanged.connect(lambda value: self.camera.exposure(value*1000))
        Expobox.valueChanged.connect(lambda :Expobox.lineEdit().deselect(), QtCore.Qt.QueuedConnection)
        Gainbox.valueChanged.connect(self.camera.gain)
        Gainbox.valueChanged.connect(lambda :Gainbox.lineEdit().deselect(), QtCore.Qt.QueuedConnection)
        BlackLevelbox.valueChanged.connect(self.camera.blacklevel)
        BlackLevelbox.valueChanged.connect(lambda :BlackLevelbox.lineEdit().deselect(), QtCore.Qt.QueuedConnection)

        layout = QGridLayout()
        layout.addWidget(Expolabel,      0,0)
        layout.addWidget(Expobox,        0,1)
        layout.addWidget(ExpoAuto,       0,2)
        layout.addWidget(Gainlabel,      1,0)
        layout.addWidget(Gainbox,        1,1)
        layout.addWidget(GainAuto,       1,2)
        layout.addWidget(BlackLevellabel,2,0)
        layout.addWidget(BlackLevelbox,  2,1)
        layout.addWidget(bitBut,3,0)
        layout.addWidget(binDrop,3,1)
        layout.addWidget(self.saveLocLabel,3,2)
        layout.addWidget(savelabel,4,0)
        layout.addWidget(self.SaveImagesBox,4,1)
        layout.addWidget(self.saveBar,4,2)

        panel.setLayout(layout)
        return panel

    def change_binning(self,text):
        if text == 'No binning':
            self.camera.binning((1,1))
            self.expectedPixels = (1920,1200)
        elif text == '2x2 binning':
            self.camera.binning((2,2))
            #self.camera.binningMode('Average')
            self.expectedPixels = (960,600)
        elif text == '4x4 binning':
            self.camera.binning((4,4))
            #self.camera.binningMode('Average')
            self.expectedPixels = (480,300)

    def make_temppanel(self):
        panel = QFrame()
        self.TStartbox = mySpinbox()
        self.TStartbox.setValue(600)
        self.TStopbox = mySpinbox()
        self.TStopbox.setValue(601)
        self.dTbox = mySpinbox()
        self.dTbox.setValue(0.2)
        self.Npicturebox = QSpinBox()
        self.Npicturebox.setValue(10)
        self.SaveTempImages = QCheckBox()
        self.SaveTempImages.setChecked(False)
        Toplayout = QGridLayout()
        timings = QGridLayout()
        timings.addWidget(QLabel('Start time (ms)'),0,0)
        timings.addWidget(self.TStartbox,0,1)
        timings.addWidget(QLabel('Stop time (ms)'),1,0)
        timings.addWidget(self.TStopbox,1,1)
        timings.addWidget(QLabel('timestep (ms)'),2,0)
        timings.addWidget(self.dTbox,2,1)#3
        timings.addWidget(QLabel('Number of pictures for each timestep'),3,0)
        timings.addWidget(self.Npicturebox,3,1)#3
        timings.addWidget(QLabel('Save the images to the default logpath'),4,0)
        timings.addWidget(self.SaveTempImages,4,1)#3



        Toplayout.addLayout(timings,0,0)
        self.progressbar = QProgressBar()
        Toplayout.addWidget(self.progressbar,1,0)

        TempPlot = pg.PlotWidget(background=pg.mkColor('w'))
        TempPlot.setMaximumSize(320,200)
        sp = TempPlot.sizePolicy()
        sp.setHorizontalPolicy(QSizePolicy.Fixed)#setHeightForWidth( True)
        sp.setVerticalPolicy(QSizePolicy.Fixed)
        TempPlot.setSizePolicy( sp )
        self.TempDatax = pg.ErrorBarItem(x=np.array([0,1,2,3]),y=np.array([0,1,2,3]),height =np.array([0,1,2,3]))
        self.TempDatay = pg.ErrorBarItem(x=np.array([0,1,2,3]),y=np.array([0,1,2,3]),height =np.array([0,1,2,3]))
        self.TempFitx = TempPlot.plot()
        self.TempFity = TempPlot.plot()
        TempPlot.addItem(self.TempDatax)
        TempPlot.addItem(self.TempDatay)
        TempPlot.addItem(self.TempFitx)
        TempPlot.addItem(self.TempFity)
        Toplayout.addWidget(TempPlot,1,1)

        self.fitim = pg.ImageItem()
        self.fitim.setLookupTable(self.lut)
        self.fitcurve = pg.EllipseROI((200,200),(20,20),pen=pg.mkPen(color='k',width=2))
        fitwig = pg.PlotWidget()
        fitwig.addItem(self.fitim)
        fitwig.addItem(self.fitcurve)
        fitwig.setMaximumSize(320,200)
        sp = fitwig.sizePolicy()
        sp.setHorizontalPolicy(QSizePolicy.Fixed)#setHeightForWidth( True)
        sp.setVerticalPolicy(QSizePolicy.Fixed)
        fitwig.setSizePolicy( sp )
        Toplayout.addWidget(fitwig,0,1)


        panel.setLayout(Toplayout)

        return panel




    async def startTempMeas(self,Tlist):
        for aname,achannelrow,rownumber in zip(self.Srbrainpanel.channelsDO,self.Srbrainpanel.timingboxes,range(len(self.Srbrainpanel.channelsDO))):
            if aname == 'CamTrigger':
                CamTriggerChannel = achannelrow
            elif aname=='ImagingAOM':
                AOMTriggerChannel = achannelrow
            elif aname=='Zeeman':
                ZeemanChannel = achannelrow

        if self.SaveTempImages.isChecked():
            logpath = 'Z:\Sr1\MOT Image Logging'
            date = datetime.datetime.now().strftime('%Y%m%d')
            tm = datetime.datetime.now().strftime('%H%M_%S')
            self.savepath = logpath + '\\' + date + '\\' + tm

        if self.expectedPixels == (480,300):
            convfac = (4*5.86*1e-6)
        elif self.expectedPixels == (960,600):        
            convfac = (2*5.86*1e-6)    
        elif self.expectedPixels == (1920,1200): 
            convfac = (5.86e-6)

        CamWidth = CamTriggerChannel[1].value()-CamTriggerChannel[0].value() #find width of camtrigger pulses
        AOMWidth = AOMTriggerChannel[1].value() - AOMTriggerChannel[0].value()
        secondPulsedelay = CamTriggerChannel[2].value()-CamTriggerChannel[0].value()
        self.progressbar.setRange(0,len(Tlist)*self.Npicturebox.value()*2)
        self.progressbar.setValue(0)
        self.TempDatax.setData(x=np.array([0,1,2,3]),y=np.array([0,1,2,3]),height =np.array([0,1,2,3]))
        self.TempDatay.setData(x=np.array([0,1,2,3]),y=np.array([0,1,2,3]),height =np.array([0,1,2,3]))
        self.TempFitx.setData([],[])
        self.TempFity.setData([],[])
        result = [[],[],[],[],[]]
        for aT in Tlist:
            CamTriggerChannel[0].setValue(aT)
            CamTriggerChannel[1].setValue(aT + CamWidth)
            CamTriggerChannel[2].setValue(secondPulsedelay + aT)
            CamTriggerChannel[3].setValue(secondPulsedelay + aT + CamWidth)


            AOMTriggerChannel[0].setValue(aT)
            AOMTriggerChannel[1].setValue(aT + AOMWidth)
            AOMTriggerChannel[2].setValue(secondPulsedelay + aT)
            AOMTriggerChannel[3].setValue(secondPulsedelay + aT + AOMWidth)

            ZeemanChannel[0].setValue(aT)
            ZeemanChannel[1].setValue(aT + CamWidth)
            ZeemanChannel[2].setValue(secondPulsedelay + aT)

            self.resultarray = []
            self.TempMeasuring = True
            self.Srbrainpanel.Srbrain.stopSequence()
            self.Srbrainpanel.arm_pattern()
            self.waitbutton.toggle()
            await asyncio.sleep(2)
            self.Srbrainpanel.Srbrain.startSequence()

            while self.TempMeasuring:
                await asyncio.sleep(1)

            self.Srbrainpanel.Srbrain.stopSequence()
            self.waitbutton.toggle()
            await asyncio.sleep(2)

            fitdat = await self.fit_routine(aT-Tlist[0])
            x0,y0,xsig,ysig,amplitude,offset = fitdat[0]
            x0err,y0err,xsigerr,ysigerr,amplitudeerr,offseterr = fitdat[1]

            result[0].append(aT-Tlist[0])
            result[1].append(xsig*convfac)
            result[2].append(ysig*convfac)
            result[3].append(xsigerr*convfac)
            result[4].append(ysigerr*convfac)

            self.TempDatax.setData(x = np.array(result[0])+0.01,y=np.array(result[1]),height=np.array(result[3])*2,pen=pg.mkPen(color='r'))
            self.TempDatay.setData(x = np.array(result[0])-0.01,y=np.array(result[2]),height=np.array(result[4])*2,pen=pg.mkPen(color='g'))

            self.fitcurve.setPos((x0-xsig,y0-ysig))
            self.fitcurve.setSize((2*xsig,2*ysig))

        def sigfit(x,a,b):
            return np.sqrt(b + a*x**2)

        kb = 1.38064852*1e-23
        m = 1.4592332*1e-25


        dtlist = np.linspace(0,Tlist[-1]-Tlist[0],100)
        try:
            parax,covmx = curve_fit(sigfit,np.array(result[0])*1e-3,np.array(result[1]),sigma=result[3],p0=[8e-4,kb*5e-3/m])
            fitx = sigfit(dtlist*1e-3,*parax)
            self.TempFitx.setData(dtlist,fitx,pen=pg.mkPen(color='r',width=2))
        except Exception as e:
            print(e)
        #xTemperature
#            xerr = np.sqrt(np.diag(covmx))
          #Txerr = (ms/kb)*xerr[0]
        Tx = parax[0]*(m/kb)*1e3
        print('Tx:',Tx,'mK')
        
        #yfitting
        ##sigysq = np.array(points[1])
        #sigysq = np.multiply(sigysq,convfac)
        #uncerty = np.array(points[3])
        #uncerty = np.mult iply(uncerty,convfac)
        try:
            paray,covmy = curve_fit(sigfit,np.array(result[0])*1e-3,np.array(result[2]),sigma=result[4],p0=[8e-4,kb*5e-3/m])
            fity = sigfit(dtlist*1e-3,*paray)
            self.TempFity.setData(dtlist,fity,pen=pg.mkPen(color='g',width=2))
        except Exception as e:
            print(e)
        Ty = paray[0]*(m/kb)*1e3
        print('Ty:',Ty,'mK')
        #yTemperature
#            yerr = np.sqrt(np.diag(covmy))
#            Tyerr = (ms/kb)*yerr[0]
#            Ty = paray[0]*(ms/kb)




    async def fit_routine(self,adT):

        def gaussian2d(x, y, x0, y0, xalpha, yalpha, A, offset):
            return offset + A * np.exp( -((x-x0)**2/(2*xalpha**2)) -((y-y0)**2/(2*yalpha**2)))

        def _gaussian(M, *args):
            x, y = M
            arr = np.zeros(x.shape)
            arr = gaussian(x, y, *args)
            return arr
        def gaussian(data,center,sigma,amp,offset):
            return offset + amp * np.exp( -((data-center)**2/(2*sigma**2)))
        
        ylen = np.size(self.resultarray[0],1)
        xlen = np.size(self.resultarray[0],0)
        y = np.arange(0,ylen,1)
        x = np.arange(0,xlen,1)
        X,Y = np.meshgrid(x,y)
        xdata = np.vstack((X.ravel(), Y.ravel()))
        fitvalues = []
        xfitlist = []
        yfitlist = []

        p0 = [xlen/2, ylen/2, xlen, ylen, 10, 0]
        for i in range(len(self.resultarray)):
            data = self.resultarray[i]
            xdata = data[:,int(ylen/2+0.5)]
            ydata = data[int(xlen/2+0.5),:]
            try:
                #popt, pcov = curve_fit(_gaussian, xdata, data.ravel(),p0)
                poptx, pcovx = curve_fit(gaussian, x,xdata ,[xlen/2,200,20,0])
                popty, pcovy = curve_fit(gaussian, y,ydata ,[ylen/2,200,20,0])

                fitvalues.append([poptx[0],popty[0],abs(poptx[1]),abs(popty[1]),poptx[2],poptx[3]])
                xfitlist.append(gaussian(x,*poptx))
                yfitlist.append(gaussian(y,*popty))
            except RuntimeError as e:
                fitvalues.append([np.nan,np.nan,np.nan,np.nan,np.nan,np.nan])
                xfitlist.append(np.nan)
                yfitlist.append(np.nan)
                print(e)

            self.progressbar.setValue(self.progressbar.value() +1)
            
            popt_array = np.array(fitvalues)

            asyncio.sleep(0.1)
        try:
            self.Imagecheck = PopupInspection(self.resultarray,self.lut,x,y,xfitlist,yfitlist)
            a = self.Imagecheck.exec_()
            keeplist = self.Imagecheck.keeplist

            fitvalues = np.array(fitvalues)[keeplist]
        except Exception as e:
            print(e)
        fitvalues = fitvalues[~np.isnan(fitvalues).any(axis=1)] #remove all NaN values that we have not deselected
        if len(fitvalues) == 0:
            return(np.ones(6)*np.nan,np.ones(6)*np.nan)

        if self.SaveTempImages.isChecked():
            savepath = 'dT_' + str.replace('{:3.3f}'.format(adT),'.','_') + '_ms'
            imagelist = []
            for i in range(len(resultarray)):
                if keeplist[i]:
                    imagelist.append(resultarray[i])
            self.save_images(imagelist,savepath)

        meanval = np.mean(fitvalues,axis=0)
        stdval = np.std(fitvalues,axis=0)
               
        meanim = np.mean(self.resultarray,axis=0)

        self.fitim.setImage(meanim)

        self.histogramplot[2].setData(x,gaussian(x,*poptx))
        self.histogramplot[3].setData(y,gaussian(y,*popty))

        return (meanval,stdval)

    def save_images(self,images,saveloc):
        try:
            savelocation = self.savepath + '\\' + saveloc
            if not os.path.exists(savelocation):
                os.makedirs(savelocation)
            self.saveBar.show()
            self.saveLocLabel.setText('Saving {:d} images to "{:s}"'.format(len(images),savelocation))
            self.saveBar.setRange(0,len(images)-1)
            for i in range(len(images)):
                 np.savetxt(savelocation + '\_{:d}.txt'.format(i), images[i], delimiter=",")
                 self.saveBar.setValue(i)
            self.saveLocLabel.setText('')
            self.saveBar.hide()
        except Exception as e:
            print(e)
            print(savelocation)



    def restore_GUI(self):
        pass
        '''
        settings = QtCore.QSettings('CameraGUi.ini',QtCore.QSettings.IniFormat)

        for aspinbox in self.findChildren(QDoubleSpinBox) + self.findChildren(QSpinBox):
            name = aspinbox.objectName()
            if settings.contains(name):
                value = settings.value(name,type=float)
                aspinbox.setValue(value)
        for i,achan in enumerate(self.channelsDO):
            self.timingboxes[i] = settings.value('TimingChannel{:s}'.format(achan),type=list)
        print(self.timingboxes)


    def closeEvent(self,e):
        settings = QtCore.QSettings('CameraGui.ini',QtCore.QSettings.IniFormat)

        for aspinbox in self.findChildren(QDoubleSpinBox) + self.findChildren(QSpinBox):
            name = aspinbox.objectName()
            value = aspinbox.value()
            if name is not "":
                settings.setValue(name,value)
        settings.setValue('Timingboxes',self.timingboxes)
        for achan,timings in zip(self.channelsDO,self.timingboxes):
            settings.setValue('TimingChannel{:s}'.format(achan),self.timingboxes)

        settings.sync()
        self.loop.stop()
        '''


class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)

    def write(self,text):
        self.textWritten.emit(str(text))



async def process_events(qapp):
    while True:
        await asyncio.sleep(0.1)
        qapp.processEvents()
#        print(qapp.allWidgets())
#        print(len(qapp.allWidgets()))
#        qapp.connect.lastWindowClosed(lambda: qapp.quit())


class PopupInspection(QDialog):

    def __init__(self,resultarray,LUT,histx,histy,xfitlist,yfitlist):
        super().__init__()
        
        self.resultarray = resultarray
        self.lut = LUT
        self.histx = histx
        self.histy = histy
        self.xfitlist = xfitlist
        self.yfitlist=yfitlist
        self.setupLayout()


    def setupLayout(self):
        frame = QFrame()
        scrollarea = QScrollArea()
        layout = QHBoxLayout()
        self.boxlist = []
        for i in range(len(self.resultarray)):
            sublayout = QVBoxLayout()
            data = self.resultarray[i]
            pw1 = pg.PlotWidget()
            iw = pg.ImageItem()
            iw.setLookupTable(self.lut)
            pw1.addItem(iw)
            pw1.setMaximumSize(213,133)
            sp =pw1.sizePolicy()
            sp.setHorizontalPolicy(QSizePolicy.Fixed)
            sp.setVerticalPolicy(QSizePolicy.Fixed)
            pw1.setSizePolicy( sp )

            pw2 = pg.PlotWidget()
            hist1 = pw2.plot()
            hist2 = pw2.plot()
            hist1.setPen((255,0,0))
            hist2.setPen((0,255,0))
            fit1 = pw2.plot()
            fit2 = pw2.plot()
            fit1.setPen((255,0,0))
            fit2.setPen((0,255,0))

            pw2.setMaximumSize(213,133)
            pw2.setSizePolicy(sp)
            histxdata = data[:,int(max(self.histy)/2+0.5)]
            histydata = data[int(max(self.histx)/2+0.5),:]
            hist1.setData(self.histx,histxdata)
            hist2.setData(self.histy,histydata)
            fit1.setData(self.histx,self.xfitlist[i])
            fit2.setData(self.histy,self.yfitlist[i])


            iw.setImage(data)

            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.boxlist.append(checkbox)
            sublayout.addWidget(checkbox)
            sublayout.addWidget(pw1)
            sublayout.addWidget(pw2)

            layout.addLayout(sublayout)
        frame.setLayout(layout)
        scrollarea.setWidget(frame)
        toplayout = QHBoxLayout()
        toplayout.addWidget(scrollarea)
        self.setLayout(toplayout)
        self.show()


    def closeEvent(self,event):
        self.keeplist =np.array([i.isChecked() for i in self.boxlist])

 

      

def icon():
    iconstring = ["77 63 806 2","    c None",".  c #A8ACA8","+   c #787C78","@   c #C0A070","#   c #605860","$   c #888888","%   c #606460","&   c #807880","*   c #888488","=   c #706C70","-   c #707470",";   c #101010",">   c #281C28",
    ",   c #302830","'   c #787478",")   c #807C80","!   c #403C40","~   c #282028","{   c #E8E870","]   c #302C30","^   c #787078","/   c #080408","(   c #282428","_   c #303030",":   c #787878","<   c #888C88","[   c #383838",
    "}   c #282828","|   c #707070","1   c #808880","2   c #404040","3   c #080808","4   c #686868","5   c #989490","6   c #909088","7   c #484C48","8   c #303430","9   c #585C58","0   c #606060","a   c #303830","b   c #303020",
    "c   c #606858","d   c #606058","e   c #989088","f   c #908C88","g   c #707478","h   c #586060","i   c #484840","j   c #505448","k   c #404440","l   c #585848","m   c #808C78","n   c #98A090","o   c #989C90","p   c #909888",
    "q   c #A09490","r   c #808480","s   c #707878","t   c #404C40","u   c #203C28","v   c #202C20","w   c #182418","x   c #182018","y   c #485C58","z   c #080C08","A   c #202828","B   c #505850","C   c #585C50","D   c #606050",
    "E   c #585C48","F   c #687460","G   c #889080","H   c #A0A498","I   c #988C88","J   c #909488","K   c #888880","L   c #283C28","M   c #405C50","N   c #283828","O   c #304040","P   c #202C30","Q   c #182020","R   c #283830",
    "S   c #283430","T   c #405440","U   c #687058","V   c #788070","W   c #808478","X   c #888C80","Y   c #485848","Z   c #405848","`   c #304838"," .  c #283020","..  c #304430","+.  c #384838","@.  c #303428","#.  c #404C38",
    "$.  c #586C50","%.  c #303C40","&.  c #383C38","*.  c #384038","=.  c #305040","-.  c #506C68",";.  c #506868",">.  c #405850",",.  c #284030","'.  c #304438",").  c #385038","!.  c #384C38","~.  c #485C48","{.  c #909CA0",
    "].  c #A8A8B0","^.  c #A8ACB0","/.  c #C0B8B8","(.  c #B8B4A0","_.  c #B8C8C0",":.  c #686468","<.  c #686850","[.  c #184828","}.  c #102808","|.  c #202818","1.  c #182828","2.  c #202820","3.  c #202420","4.  c #384040",
    "5.  c #304C40","6.  c #405448","7.  c #405438","8.  c #708078","9.  c #B0ACB0","0.  c #B8B0B0","a.  c #98B4A8","b.  c #B0B8A0","c.  c #386420","d.  c #607C60","e.  c #185820","f.  c #607848","g.  c #A8A898","h.  c #98A0A0",
    "i.  c #889490","j.  c #808C88","k.  c #788480","l.  c #687C70","m.  c #605C40","n.  c #100C10","o.  c #283030","p.  c #304C38","q.  c #384840","r.  c #586C58","s.  c #688470","t.  c #406430","u.  c #182C00","v.  c #182010",
    "w.  c #101000","x.  c #181810","y.  c #181800","z.  c #101008","A.  c #100808","B.  c #101800","C.  c #081408","D.  c #78A0A0","E.  c #98B4D0","F.  c #909898","G.  c #688070","H.  c #587460","I.  c #486850","J.  c #485C50",
    "K.  c #283820","L.  c #507058","M.  c #586C60","N.  c #788488","O.  c #688480","P.  c #282C28","Q.  c #101C10","R.  c #203028","S.  c #587858","T.  c #708070","U.  c #687C68","V.  c #708870","W.  c #988C58","X.  c #202008",
    "Y.  c #100C08","Z.  c #081000","`.  c #181008"," +  c #203C00",".+  c #304448","++  c #88A8A0","@+  c #687868","#+  c #506058","$+  c #283420","%+  c #404838","&+  c #A8C0D0","*+  c #102018","=+  c #203428","-+  c #303C30",
    ";+  c #283C30",">+  c #486458",",+  c #506C58","'+  c #607468",")+  c #607C68","!+  c #183410","~+  c #101408","{+  c #100C00","]+  c #081008","^+  c #606848","/+  c #405418","(+  c #587468","_+  c #404840",":+  c #384438",
    "<+  c #303828","[+  c #506458","}+  c #182C20","|+  c #486048","1+  c #507060","2+  c #106050","3+  c #506050","4+  c #485448","5+  c #101C08","6+  c #101808","7+  c #202C18","8+  c #307048","9+  c #788068","0+  c #587868",
    "a+  c #505C50","b+  c #002010","c+  c #183828","d+  c #406448","e+  c #385848","f+  c #484408","g+  c #609880","h+  c #707860","i+  c #505C48","j+  c #385440","k+  c #708478","l+  c #586458","m+  c #607068","n+  c #082810",
    "o+  c #384C30","p+  c #305C48","q+  c #185C28","r+  c #486450","s+  c #081400","t+  c #787448","u+  c #082000","v+  c #708470","w+  c #507458","x+  c #485840","y+  c #282C20","z+  c #586860","A+  c #708080","B+  c #384830",
    "C+  c #304030","D+  c #001C10","E+  c #203420","F+  c #305440","G+  c #789878","H+  c #181808","I+  c #080C00","J+  c #504C30","K+  c #104C10","L+  c #483420","M+  c #102010","N+  c #101410","O+  c #809480","P+  c #708C70",
    "Q+  c #384430","R+  c #203020","S+  c #788C90","T+  c #687C78","U+  c #304038","V+  c #183020","W+ c #B8A4A0","X+  c #181408","Y+  c #484028","Z+  c #706440","`+  c #304428"," @  c #080000",".@  c #202C10","+@  c #686028",
    "@@  c #202410","#@  c #181C08","$@  c #001808","%@  c #687068","&@  c #607060","*@  c #385040","=@  c #788080","-@  c #889CA8",";@  c #305848",">@  c #486058",",@  c #405450","'@  c #384C48",")@  c #182C18","!@  c #988878",
    "~@  c #606C50","{@  c #181400","]@  c #201C10","^@  c #605438","/@  c #988460","(@  c #181C10","_@  c #606860",":@  c #607460","<@  c #203828","[@  c #103020","}@  c #384440","|@  c #303C38","1@  c #485858","2@  c #384448",
    "3@  c #506468","4@  c #405428","5@  c #101400","6@  c #786848","7@  c #708448","8@  c #607058","9@  c #788470","0@  c #405040","a@  c #708C80","b@  c #084830","c@  c #202428","d@  c #101810","e@  c #485458","f@  c #707858",
    "g@  c #505C38","h@  c #283410","i@  c #303420","j@  c #083410","k@  c #407C68","l@  c #103C10","m@  c #909C88","n@  c #506848","o@  c #707C68","p@  c #707C80","q@  c #486870","r@  c #183420","s@  c #101818","t@  c #405050",
    "u@  c #687450","v@  c #606C40","w@  c #506048","x@  c #505048","y@  c #708068","z@  c #586858","A@  c #487448","B@  c #384848","C@  c #587070","D@  c #403C30","E@  c #606C48","F@  c #202010","G@  c #685808","H@  c #383008",
    "I@  c #607458","J@  c #586440","K@  c #284818","L@  c #103C08","M@  c #283010","N@  c #503800","O@  c #202408","P@  c #282808","Q@  c #405030","R@  c #687830","S@  c #282408","T@  c #707460","U@  c #305038","V@  c #404C48",
    "W@  c #383030","X@  c #586840","Y@  c #203410","Z@  c #303410","`@  c #284020"," #  c #305030",".#  c #385C38","+#  c #103820","@#  c #081810","##  c #909C68","$#  c #787860","%#  c #485440","&#  c #385840","*#  c #687878",
    "=#  c #487480","-#  c #586450",";#  c #506440",">#  c #203808",",#  c #203018","'#  c #204020",")#  c #405430","!#  c #304808","~#  c #504C08","{#  c #081C10","]#  c #201008","^#  c #081010","/#  c #707458","(#  c #707450",
    "_#  c #506C60",":#  c #687468","<#  c #485048","[#  c #586850","}#  c #586838","|#  c #182808","1#  c #181000","2#  c #182810","3#  c #303800","4#  c #282000","5#  c #003820","6#  c #888478","7#  c #788058","8#  c #485C40",
    "9#  c #607470","0#  c #506060","a#  c #586448","b#  c #586848","c#  c #303818","d#  c #182008","e#  c #182410","f#  c #C8B090","g#  c #A8A0A0","h#  c #787868","i#  c #484428","j#  c #102008","k#  c #787C58","l#  c #383430",
    "m#  c #788C80","n#  c #506460","o#  c #908C48","p#  c #887420","q#  c #404820","r#  c #282818","s#  c #202800","t#  c #401C18","u#  c #082010","v#  c #181410","w#  c #687050","x#  c #485438","y#  c #404038","z#  c #181818",
    "A#  c #586C68","B#  c #383438","C#  c #687018","D#  c #484020","E#  c #281810","F#  c #685420","G#  c #281008","H#  c #001C18","I#  c #202000","J#  c #506040","K#  c #484418","L#  c #484430","M#  c #484838","N#  c #201808",
    "O#  c #283018","P#  c #684C10","Q#  c #708460","R#  c #A89880","S#  c #505438","T#  c #505C40","U#  c #383420","V#  c #686C68","W#  c #505840","X#  c #383C28","Y#  c #103C00","Z#  c #080008","`#  c #A88448"," $  c #908068",
    ".$  c #202C00","+$  c #403810","@$  c #504420","#$  c #585840","$$  c #585440","%$  c #302818","&$  c #282010","*$  c #686458","=$  c #686408","-$  c #C08C48",";$  c #401800",">$  c #605840",",$  c #807860","'$  c #787458",
    ")$  c #605430","!$  c #687848","~$  c #505C58","{$  c #201800","]$  c #888890","^$  c #707068","/$  c #282C10","($  c #508070","_$  c #200400",":$  c #705C40","<$  c #706048","[$  c #706448","}$  c #887C68","|$  c #685C38",
    "1$  c #808C58","2$  c #485050","3$  c #C0A450","4$  c #484810","5$  c #404848","6$  c #505050","7$  c #381000","8$  c #281800","9$  c #282820","0$  c #908878","a$  c #A09488","b$  c #A89C98","c$  c #504820","d$  c #302C20",
    "e$  c #C8AC68","f$  c #989468","g$  c #605848","h$  c #080400","i$  c #485450","j$  c #403010","k$  c #382C10","l$  c #808088","m$  c #707078","n$  c #404438","o$  c #202810","p$  c #504430","q$  c #988880","r$  c #B0A4A8",
    "s$  c #B0A8A8","t$  c #B0ACA8","u$  c #686060","v$  c #403C38","w$  c #282418","x$  c #A09868","y$  c #685C48","z$  c #A8A048","A$  c #282008","B$  c #584410","C$  c #504410","D$  c #201810","E$  c #908C90","F$  c #C0B8C8",
    "G$  c #787880","H$  c #B8B4B0","I$  c #787870","J$  c #685850","K$  c #786860","L$  c #988C90","M$  c #B0A0A0","N$  c #B0A4A0","O$  c #989090","P$  c #504448","Q$  c #382C08","R$  c #807060","S$  c #405858","T$ c #908820",
    "U$  c #887010","V$  c #382808","W$  c #302808","X$  c #201C08","Y$  c #302C10","Z$  c #484438","`$  c #706860"," %  c #807870",".%  c #B0A8A0","+%  c #C0B4B0","@%  c #C8BCB8","#%  c #D0C4C0","$%  c #D0C8C8",R"%%  c #C8C0C0",
    "&%  c #C8BCC0","*%  c #A8A4A0","=%  c #908488","-%  c #A89CA0",";%  c #C0BCB8",">%  c #585458",",%  c #302408","'%  c #504828",")%  c #A8A468","!%  c #201408","~%  c #908438","{%  c #684810","]%  c #382408","^%  c #281C08",
    "/%  c #402800","(%  c #685820","_%  c #404030",":%  c #606048","<%  c #888070","[%  c #887868","}%  c #D8D0D0","|%  c #C8C4C0","1%  c #D0CCC8","2%  c #A09498","3%  c #887C80","4%  c #787070","5%  c #383010","6%  c #403410",
    "7%  c #908040","8%  c #301C08","9%  c #382410","0%  c #584408","a%  c #483810","b%  c #786818","c%  c #403C20","d%  c #786850","e%  c #887860","f%  c #A09078","g%  c #B0A088","h%  c #C0AC98","i%  c #C8AC90","j%  c #A89458",
    "k%  c #D8C498","l%  c #B8AC78","m%  c #B8B078","n%  c #908C60","o%  c #403830","p%  c #383028","q%  c #302820","r%  c #201C18","s%  c #584010","t%  c #908C80","u%  c #C0A888","v%  c #302410","w%  c #605C38","x%  c #705808",
    "y%  c #504010","z%  c #302810","A%  c #281C10","B%  c #684C20","C%  c #604818","D%  c #403418","E%  c #282410","F%  c #787460","G%  c #483818","H%  c #605C28","I%  c #282810","J%  c #605420","K%  c #484420","L%  c #303018",
    "M%  c #302C18","N%  c #403420","O%  c #382C18","P%  c #605C48","Q%  c #A08428","R%  c #685C30","S%  c #605820","T%  c #403C18","U%  c #806C28","V%  c #706428","W%  c #907C40","X%  c #585428","Y%  c #584C28","Z%  c #604C28",
    "`%  c #B0A8B0"," &  c #584418",".&  c #907848","+&  c #504428","@&  c #987C40","#&  c #A09050","$&  c #706038","%&  c #302010","&&  c #887038","*&  c #887438","=&  c #705C30","-&  c #988048",";&  c #584C20",">&  c #806828",
    ",&  c #886C28","'&  c #B09058",")&  c #C0A060","!&  c #B09048","~&  c #705420","{&  c #806020","]&  c #705820","^&  c #383418","/&  c #A08458","(&  c #806428","_&  c #503C20",":&  c #807040","<&  c #605020","[&  c #585020",
    "}&  c #504418","|&  c #404018","1&  c #907838","2&  c #A88850","3&  c #705828","4&  c #604820","5&  c #D8D4D8","6&  c #605828","7&  c #585420","8&  c #785C20","9&  c #C8A430","0&  c #685010","a&  c #886820","b&  c #A88440",
    "c&  c #A07C38","d&  c #806028","e&  c #806420","f&  c #685838","g&  c #706848","h&  c #807858","i&  c #807458","j&  c #684818","k&  c #786038","l&  c #A08448","m&  c #907448","n&  c #B09050","o&  c #A88848","p&  c #706028",
    "q&  c #685C28","r&  c #484818","s&  c #786828","t&  c #605408","u&  c #605428","v&  c #504808","w&  c #685020","x&  c #705818","y&  c #503818","z&  c #604C10","A&  c #382810","B&  c #604C18","C&  c #584818","D&  c #483418",
    "E&  c #605038","F&  c #A89070","G&  c #806030","H&  c #908C68","I&  c #989478","J&  c #403018","K&  c #302800","L&  c #383000","M&  c #B89448","N&  c #D8B468","O&  c #685428","P&  c #705C28","Q&  c #786428","R&  c #987018",
    "S&  c #D0A848","T&  c #605010","U&  c #504018","V&  c #181010","W&  c #504028","X&  c #584830","Y&  c #909070","Z&  c #504838","`&  c #987828"," *  c #B88C30",".*  c #B89038","+*  c #786C38","@*  c #484820","#*  c #988440",
    "$*  c #685828","%*  c #786410","&*  c #605018","**  c #483410","=*  c #402C18","-*  c #483018",";*  c #B89878",">*  c #585040",",*  c #504810","'*  c #786438",")*  c #B89C60","!*  c #706030","~*  c #806C38","{*  c #786010",
    "]*  c #705C10","^*  c #585010","/*  c #B09068","(*  c #605448","_*  c #000400",":*  c #A89050","<*  c #B89C58","[*  c #A88C50","}*  c #806830","|*  c #685410","1*  c #604828","2*  c #B08C60","3*  c #787068","4*  c #080800",
    "5*  c #A88C48","6*  c #B09450","7*  c #302418","8*  c #907840","9*  c #705C18","0*  c #302008","a*  c #584810","b*  c #906838","c*  c #888C78","d*  c #807C70","e*  c #907030","f*  c #987C30","g*  c #604808","h*  c #886030",
    "i*  c #808870","j*  c #605028","k*  c #A08038","l*  c #987C38","m*  c #281808","n*  c #805830","o*  c #403828","p*  c #584820","q*  c #A08440","r*  c #806C30","s*  c #604410","t*  c #907450","u*  c #686450","v*  c #382C20",
    "w*  c #808470","x*  c #909480","y*  c #A0A090","z*  c #382C28","A*  c #282020","B*  c #484038","C*  c #403430","D*  c #402C10","E*  c #604420",
"                                    . . + +                                                                                                               ",
"                                  . @ @ # . $                                                   . . . %                                                   ",
"                                  + . + + + & *                                               . = # - . -                                                 ",
"                                    ;     > , ' )                                           . = ! ~ - . { { .                                             ",
"                                            ~ ] ^ .                                         . = ] /   - . . -                                             ",
"                                              ( _ : .                                     < ) [ }                                                         ",
"                                                } [ | .                               - < 1 2 _                                                           ",
"                                                3 _ 4 - -                           5 6 % 7 8                                                             ",
"                                                  ] [ 9 0 - - a a b c c c d 8   . e f g h                                                                 ",
"                                                  ] [ i j k 7 - - l m n o p l . q e r s t u v w x                                                         ",
"                                    y           z A a B C D E l - F G n H 6 e e I J K L M L L N N v                                                       ",
"          y y y y y                 y O P Q x R S S T B U V W J J < * ) ' $ : . X o Y Z ` L L  .L ..+.@.      #.$.                                        ",
"        y %.&.*.&.8 y               =.-.;.>.,.'.).!.~.{.].].^./.(./._.H = :.:.| : + f <.[.}.L L L ,.!.#.#.#.#.$.|.                                        ",
"        y 1.2.3.&.&.4.y             =.=.5.5.Z 6.7.8.].9.0.a.b.c.d.3 e.f.a./._.g.h.i.j.k.l.m.m.L L |.!.T ~.~.$.$.|.                                        ",
"      %.A n.          o.y y       =.;.p.q.r.~.s.. . | t.u.v.w.x.3 3 y.z.A.B.C.w.d.D.E.F.F.G.H.I.J.|.|.K.K.T L.M.N.                                        ",
"      O.P.            Q.R.S y y ;.;.p.I.S.T.U.V.W.w.A.X.Y.Y.w.Z.3 3 z.3 3 A.C.w.`. +.+[.++D.r @+#+t |.|.$+N #.%+N.N.                                      ",
"    O.&+O.              *+=+R -+;+>+,+I.'+)+!+~+w.w.Y.Y.{+w.w.{+3 3 z.z.B.C.]+Y.y.x.y.!+!+w.^+/+m (+_+|.|.|.:+<+[+N.t                                     ",
"    O.&+&+O.              }+R.!.|+1+2+3+4+Z.z.z.w.w.w.w.w.w.w.w.3 3 5+6+B.z.3 C.]+3 A.x.A.w.7+[.8+9+0+*.a |.|. .Z N.N.a+                                  ",
"      O.O.                b+c+d+e+8+3+:+z.z.z.w.w.w.w.w.w.w.`.Z.3 w.f+3 z.B.5+C.w.w.Y.A.w.w.Z.A.z.g+h+H.i+#.|.|.j+M.k+l+m+                                ",
"                          n+o+p+q+r.r+w.z.z.w.w.w.w.w.w.Z.Z.B.s+Z.Z.3 t+~+]+5+3 ]+3 3 ]+w.w.3 `.Z.u+m v+w+x+#.v y+[+z+N.A+B+~.C+                          ",
"                        D+E+F+p+F G+A.w.w.w.w.{+H+w.Z.I+J+w.z.f+K+e.L+d.G+M+f+3 N+N+5+]+z 3 y.B.3 w.w.O+P+$.3+Q+R+@.a+k.S+T+z+-+U+                        ",
"                        V+!.Z W+F [.w.w.w.w.w.X+X+Y+I+Z+`+K+ @s.A.D..@e.y.+@8+Z.f+d.@@#@3 3 A.A.B.`.w.$@%@G.&@-+N @.*@=@-@;@>@,@U+'@y ;.O.O.              ",
R"                        )@-+!@~@~@Z.3 {+w.{@z.]@w.^@A./@ @t+ @% ++3 Z.D..@s.z.d.z.(@D.d.Z.3 3 Z.A.y.w.`._@:@&@!.N <@*@Z -@t.[@}@U+U+|@1@2@1@3@O.          ",
"                        Q.'.h+4@Z.3 z.5@5@z.#@z.w.Z.6@ @K+z.f+u+3  @ @ @@ B.t+y.x.7@3 3 3 3 A.A.A.w.w.z.; 8@9@~.0@;+-+` a@| b@      P.} c@Q d@e@3@        ",
"                        R <.f@g@z z 5@5@~+z.h@z. @{+f+ @ @3  @ @ @ @ @ @ @i@A.L+j@k@l@[.B.m@3 y.z.3 n.Z.A.n@o@T.3+C++.'.p@q@[.r@            s@N+t@,@      ",
"                      3 *.u@v@Y.z z.5@~+~+z.~+~+w@x@Z. @D. @ @ @ @ @ @ @ @ @$@K+e.L+d.G+M+v.3 N+`.3 n.n.A.3 8@y@z@0@+.'.M s.A@!+                N+B@C@C@  ",
"                      ] D@E@K+Y.z 5@5@5@~+F@@@3 G@B.[. @H@ @ @ @ @ @ @ @ @ @s.+@D..@e.y.+@8+Z.A.d@B.3 n.; A.3 I@o@i++.*@>+s.q@.+                  C@&+&+C@",
"                      ] J@K@L@z z.5@~+~+B..@M@(@N@z.f+O@P@ @ @ @ @ @ @ @ @ @% ++++Q@D..@s.R@Q.z.(@(@S@A.A.A.z.3 V T@0@U@V@s.d.R@                  / C@C@  ",
"                    ] W@X@Y@Y.z z.{@~+{+(@Z@`@ #.#+@3 f+3  @ @ @ @ @ @ @ @ @u+3 [.3 ++Q@q+t++#x.@#(@z.H+3 z.A.3 ##$#%#&#_+*#=#|                           ",
"                    ] -#;#>#Y.z z.z.~+{+(@,#'#3 )#..!#~#G@ @ @ @ @ @ @ @ @ @##f.7+##[.3 3 z.`.&+{#(@]#^#A.]#3 ~+ @/#(#Y 2 _#p@:#<#                        ",
"                  ] ] [#}#|#Y.Y.Z.z.A.]#w.H+1#3 t+2#3#3 4# @ @ @ @ @ @ @ @ @`+m@5#f.7+##Z.6#^#y.{#(@3 #@~+z.Z.~+z.7@7#Y 8#[ O.9#&.                        ",
R"                  0#a#b#c#d#y.z.~+3 3 z.e#X+]@i@z.X+A.3 3 ~# @ @ @ @ @ @ @f#% g#`+m@5#h#t.a.i#j#Q.v.y.H+~+]#^#~+3  @k#T x+l#k m#n#                        ",
R"                0#( o#p#q#u.~+z.Y.A.z.3 z.w.x.r#8#Z. ++@s#3#@  @ @ @ @ @@ @ t#f#% g#A.K+u+`+[@u#Q.z.y.v#v#3 #@~+A.u+w#7.x#y#z#] A#i@                      ",
"              O.B# @o#o#C#D##@O@#@H+Y.y.Y.Y.1#r#r#t. +3 u++@p#E#4#@ N@F#G#F#@ @ t#F#+@+#!+H#M+Q.Q.z.^#I#Z.y.H+~+y.z.b.X@x#J#z#B#2 O.                      ",
"            O.]    @7@t+K#L#i@M#@@#@~+z.Z.Y.z.N#F@O#z.x.3 i@~#4#t+~#4#@ N@F#G#F#P#N@Q#A@w@!+5+Q.z.3 A.A.z.y.v#v#Z.X+@@R#S#T#z#3 3 2 O.                    ",
"          O.}     @@o#R@q#U#7 V#W#X#d#~+Z.z.5@I#`.A.A.Y#3 3 3 Z# @4#t+~#w@x@`# $.$s#!+s.B.8+d@v.A.A.A.A.z.^#I#z.6++$@$R##$$$`.    ,@n#O.                  ",
"        O.B#      G@o#C#3#%$&$! ) *$@.@.Z.Z.B.]#x.F@3 3 z.Z.3#3 =$Z# @@@G@N@-$p#N@F#C#!+u+!+Q.3 A.A.A.A.3 ;$]#>$,$'$)$b.!$$$ @      V@~$                  ",
"      O.2         o#o#=$+@4#{$( _ ]$^$y#k Z.Z.v#v.F@F@/$3 z.u+L+x.R@G@y.N@R@;$F#o#L+L+($Q.Q.A.A.A.A.A.A._$:$<$[$}$0.|$@ 1$$$A.        2$O.                ",
"    O.2           3$o#=$~#4$4#3 &$3 ]$]$5$7 7 6$x.x.F@@@h@z z.z.3 N@u+;$;$7$N@8$9$!+Q@Q.M+A.A.A.z.z.3 3 0$a$b$0.c$3 d$e$f$g$h$          4.i$              ",
"    O.            3$o#F#.$3#N#j$k$H+3 ]$]$l$= m$4+t n$B o$Z@z.`.X+{$.$v.A.!+!+A.A.A.A.A.A.3 z.p$Y+q$r$s$t$u$v$3 3 3 w$i#x$y$h$            n#              ",
"  O.O.2           z$o#G@7+~#A$k$B$C$D$3 4#E$F$G$l$E$H$- - I$K y+y+y+3 u+A.A.A.A.A.A.A.9$9$J$K$L$M$N$O$P$Q$H+3 3 4#X+]@U#@ R$ @          S$A#9#            ",
R"O.&+&+O.           $T$U$j#N#V$G@W$A$X$Y$]@3 z.Z$`$ %.%+%@%#%$%%%&%/.*%5 * ) & & =%L$-%r$0.;%g#:.>%2 4#,%A$#@H+4#W$z.H+'%)%}$!%3         9#&+&+9#          ",
R"O.&+O.2           T$~%{%]%^%/%k$B$F@k$(%&$]@3 3 z._%:%<%[%a$}%}%}%;%|%$%1%1%1%1%1%0.r$2%3%4%4 x@P.3 H+X$5%6%j$H+z.z.X+F@g#R#!%3         S$S$S$S$          ",
R"2 2 2             )%7%8%9%]#0%a%W$A$b%c$c%F@5%3 3 3 4#d%^@^@e%f%g%h%i%j%k%l%m%n%y$o%p%q%r%4#3 3 3 3 5%s%a%S@H+z.]@H+~+w$t%u%v%Y.                          ",
R"                )%w%!%!%]#]#x%k$H+F@y%(%@$z%x.D#& 3 3 3 3 N#N#N#N#N#N#N#N#A%&$w$q%p%N#{$3 3 3 3 & 5%B%C%D%H+~+~+~+]@E%w$F%)%G%z.!%                        ",
R"                )%w%!%!%  Z#H%z%4#I%J%c$c$K%L%M%w$]@3 & 3 3 3 3 3 4#3 N#z.3 3 3 3 3 3 3 3 3 3 5%5%F#5%Q$X.#@H+&$I%N%O%E%P%Q%R%]@D$                        ",
R"              )%w%!%!%    S%T%z%3 S@U%V%W%X%Y%c%Z%M%D%`%3 3 & 3 3 & 3 3 3 3 & 3 3 & 3 3 3 & 5% &F#.&+$s%D%W$j$z%Y$+&@&D%E%#&$&^@%&;                       ",
R"            )%w%!%!%      S%Y$z%  ]+E%&&*&=&-&;&>&,&Y+%$v#D#`%3 3 `%3 3 3 3 `%3 3 `%v%j$6%`%a%'&)&!&~&{&]&M%%$5%Y$^&Y%/&(&_&:&[$9%;                       ",
R"          )%w%!%!%      <&,%X$  3 I+(@Z@[&I%}&|&1&)&2&3&j$4&5&6&7&5&`%G@J+`%5&8&`%5&9&0&s%k$F#a&b&c&d&]&e&D#v%D$M%M%f&:$/&A%g&h&i&!%                      ",
R"        )%w%!%!%      j&6%H+z.      F@R%0%3 k&l&m&n&o&3&j$p&p&q&S%r&s&t&u&v&w&x&y&9&9&0&z&j$A&B&B&e&8&C& &D&z./ v#D$v%E&F&G&3 H&I&J&                      ",
R"      )%w%!%          j&H+~+          Y%@$B&K&L&M&N&A&z%Z%O&P&Q&r&r&s&t&u&v&w&x&y&D&R&S&T&k$A&z%z%U&U&U&G%V&Y.      !%W&X&u%  Y&b.Z&                      ",
R"      )%!%          ~&Y$z               E%k$`& *.*X$A$z%=&+*@*)&)&#*<&$*P&%*&*C&**A&A&=*a&k$&$]@D$D$]@x.              -*O%;*    b.>*                      ",
R"    )%w%!%          3&~+3                 z.v%k$`.N#,*'*-&)*)&)&W%!*~*!*w&{*]*^*a%j$v%0&z&j$D&X$X+V&3                 !%!%/*    b.(*                      ",
R"    )%!%            3&~+                        _*a%N#)$:&:*<*[*@$$*&&}*C$Q$,%|*T&j$R&S&T&1*G%#@~+                      !%2*    b.3*                      ",
R"    )%!%            3&~+                          h$h$4*N#5*6*n&v%7*@&8*9*|*0*X$a*A&A&=*`.Y.I%X+_*                      !%b*    c*d*                      ",
R"    )%w%            3&~+                                `.1&5*J&h$=&e*f*9*g*0*X$a%j$v%`.3 3 _*                          !%h*  b.i*Z&                      ",
R"      )%!%          ~+3&                                  X+4&{+h$j*5*k*l*P#m*z T&4*N#{+3                               !%n*b.T@o*                        ",
"        )%            ~+3&                                        p*q*r*b&s*_*                                          !%t*u*o*v*                        ",
"                        ~+3&3&                                        P&s*                                              w*x*p%q%                          ",
"                          ~+~+                                                                                      b.y*z*A*A*                            ",
R"                                                                                                                  *$B*C*q%9%                              ",
"                                                                                                                        D*A&                              ",
"                                                                                                                      E*9%                                "]
    return iconstring
if __name__=="__main__":
    a = QApplication(sys.argv)
    a.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(icon())))
    import ctypes
    myappid = u'mycompany.myproduct.subproduct.version1' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    loop = asyncio.get_event_loop()
    w = CamGui(loop)
    loop.create_task(process_events(a))
    loop.run_until_complete(process_events(a))

