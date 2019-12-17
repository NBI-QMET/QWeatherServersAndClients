#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Gui for the AD9959 boards controlled by a raspberry Pi

"""

from PyQt5.QtWidgets import *
from PyQt5 import QtGui,QtCore
import sys
import asyncio
from qweather import QWeatherClient

__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '0.9'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'


class AD9959Gui(QWidget):

    def __init__(self,loop = None):
        super().__init__()
        QWeatherStationIP = "tcp://172.24.22.3:5559"
        name = 'AD9959GUI'
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        self.client = QWeatherClient(QWeatherStationIP,name=name,loop=self.loop)
        try:
            self.server = self.client.ACEDDSB
        except Exception as e:
            print(e,'could not find server')
        self.setWindowTitle('AD9959')
        self.setFont(QtGui.QFont('Helvetica',16))

        self.initialize()
        self.restoreGUI()
        self.loop.create_task(self.client.run())

    def initialize(self):
        titlelabel = QLabel(self.server.name)
        titlelabel.setFont(QtGui.QFont('Helvetica',20,75))
        channelpattern = self.make_channel_panel()
        frequencyPanel = self.make_frequency_panel()
        amppanel = self.make_amp_panel()
        phasepanel = self.make_phase_panel()
        layout = QVBoxLayout()

        layout.addWidget(titlelabel)
        layout.addWidget(channelpattern)
        layout.addWidget(frequencyPanel)
        layout.addWidget(amppanel)
        layout.addWidget(phasepanel)

        self.setLayout(layout)
        self.show()

    def make_channel_panel(self):
        panel = QFrame()
        buttonnames = ['0','1','2','3']
        buttonlist = [QRadioButton() for alabel in buttonnames]
        labellist = [QLabel(alabel) for alabel in buttonnames]
        self.channeldata = [[0,0,0,None,None,None] for abutton in buttonlist ]
        titlelabel = QLabel('Channel')
        titlelabel.setAlignment(QtCore.Qt.AlignCenter)
        font = titlelabel.font()
        font.setBold(True)
        titlelabel.setFont(font)
        layout = QGridLayout()
        layout.addWidget(titlelabel,0,0,1,len(buttonlist),QtCore.Qt.AlignHCenter)
        for ind,(abut,alab) in enumerate(zip(buttonlist,labellist)):
            layout.addWidget(alab,1,ind,QtCore.Qt.AlignHCenter)
            layout.addWidget(abut,2,ind,QtCore.Qt.AlignHCenter)
            abut.clicked.connect(lambda state,x=ind: self.set_channel(x) if state else None)

        buttonlist[0].click()


        panel.setLayout(layout)
        panel.setFrameStyle(0x00001)
        return panel

    def set_channel(self,channel):
        if channel == 4:
            self.currentchannel = -1 ## Because the dds code is written sich that -1 is all channels.
        else:
            self.currentchannel = channel
            try:
                freq,amp,phase,freqbox,ampbox,phasebox = self.channeldata[self.currentchannel-1]
                freqbox.setValue(freq)
                ampbox.setValue(amp)
                phasebox.setValue(phase)
                for abox in [freqbox,ampbox,phasebox]:
                    abox.editingFinished.emit()
            except AttributeError as e:
                pass

    def make_frequency_panel(self):
        panel = QFrame()
        freqbox = QDoubleSpinBox()
        freqbox.setRange(640,770)
        freqbox.setSingleStep(1)
        freqbox.setDecimals(6)
        freqbox.setSuffix(' MHz')
        freqbox.setObjectName('FreqBox')
        resbox = QComboBox()
        resbox.addItems(['MHz','100 kHz','10 kHz', 'kHz'])


        freqlabel = QLabel('#### MHz')
        titlelabel = QLabel('Frequency')
        font = titlelabel.font()
        font.setBold(True)
        titlelabel.setFont(font) 
        for achan in self.channeldata:
            achan[3] = freqbox

        def freqedited(freq):
            self.currentchannel = -1
            if self.currentchannel == -1:
                for achan in self.channeldata:
                    achan[0] = freq
            self.server.setFrequency(self.currentchannel,freq)
            freqlabel.setText('{:.6f} MHz'.format(freq))
            self.channeldata[self.currentchannel-1][0] = freq

        resbox.currentIndexChanged.connect(lambda ind: freqbox.setSingleStep(10**(-ind*1)))
        freqbox.valueChanged.connect(lambda :freqedited(freqbox.value()))
        freqbox.valueChanged.connect(lambda :freqbox.lineEdit().deselect(), QtCore.Qt.QueuedConnection)


     

        layout = QGridLayout()
        layout.addWidget(titlelabel,0,0)
        layout.addWidget(freqbox,1,0)
        layout.addWidget(resbox,0,1)
        layout.addWidget(freqlabel,1,1,QtCore.Qt.AlignRight)
        panel.setLayout(layout)
        return panel


    def make_amp_panel(self):
        panel = QFrame()
        ampbox = QSpinBox()
        ampbox.setRange(0,100)
        ampbox.setSingleStep(1)
        ampbox.setSuffix(' %')
        ampbox.setObjectName('AmpBox')


        amplabel = QLabel('#### %')
        titlelabel = QLabel('Amplitude')
        font = titlelabel.font()
        font.setBold(True)
        titlelabel.setFont(font) 

        for achan in self.channeldata:
            achan[4] = ampbox

        def ampedited(amp):
            if self.currentchannel == -1:
                for achan in self.channeldata:
                    achan[1] = amp
            self.server.setAmplitude(self.currentchannel,amp)
            amplabel.setText('{:d} %'.format(amp))
            self.channeldata[self.currentchannel-1][1] = amp


        ampbox.valueChanged.connect(lambda :ampedited(ampbox.value()))
        ampbox.valueChanged.connect(lambda :ampbox.lineEdit().deselect(), QtCore.Qt.QueuedConnection)


        layout = QGridLayout()
        layout.addWidget(titlelabel,0,0)
        layout.addWidget(ampbox,1,0)
        layout.addWidget(amplabel,1,1,QtCore.Qt.AlignRight)
        panel.setLayout(layout)
        return panel

    def make_phase_panel(self):
        panel = QFrame()
        phasebox = QDoubleSpinBox()
        phasebox.setRange(0,360)
        phasebox.setSingleStep(1)
        phasebox.setDecimals(1)
        phasebox.setSuffix(' degrees')
        phasebox.setObjectName('PhaseBox')

#        resbox.set_

        phaselabel = QLabel('#### Degrees')
        titlelabel = QLabel('Phase')
        font = titlelabel.font()
        font.setBold(True)
        titlelabel.setFont(font) 

        for achan in self.channeldata:
            achan[5] = phasebox


        def phaseedited(phase):
            if self.currentchannel == -1:
                for achan in self.channeldata:
                    achan[2] = phase
            self.server.setPhase(self.currentchannel,phase)
            phaselabel.setText('{:.1f} Degrees'.format(phase))
            self.channeldata[self.currentchannel-1][2] = phase

        phasebox.valueChanged.connect(lambda :phaseedited(phasebox.value()))
        phasebox.valueChanged.connect(lambda :phasebox.lineEdit().deselect(), QtCore.Qt.QueuedConnection)


        layout = QGridLayout()
        layout.addWidget(titlelabel,0,0)
        layout.addWidget(phasebox,1,0)
        layout.addWidget(phaselabel,1,1,QtCore.Qt.AlignRight)
        panel.setLayout(layout)
        return panel

    def restoreGUI(self):
        settings = QtCore.QSettings(self.server.name+'_gui.ini',QtCore.QSettings.IniFormat)

        for aspinbox in self.findChildren(QDoubleSpinBox) + self.findChildren(QSpinBox):
            name = aspinbox.objectName()
            if settings.contains(name):
                value = settings.value(name,type=float)
                aspinbox.setValue(value)
        #if settings.contains('windowposition'):
        #    self.move(settings.value("windowposition").toPoint());
        #if settings.contains('windowsize'):
        #    self.resize(settings.value("windowsize").toSize());

            for i in range(len(self.channeldata)):
                name = 'channel{:.1f}'.format(i+1)
                if settings.contains(name):
                    value = settings.value(name,type=float)
                    self.channeldata[i][0] = value[0]
                    self.channeldata[i][1] = value[1]
                    self.channeldata[i][2] = value[2]



    def closeEvent(self,e):
        settings = QtCore.QSettings(self.server.name+'_gui.ini',QtCore.QSettings.IniFormat)

        for aspinbox in self.findChildren(QDoubleSpinBox) + self.findChildren(QSpinBox):
            name = aspinbox.objectName()
            value = aspinbox.value()
            settings.setValue(name,value)
        for i in range(len(self.channeldata)):
            settings.setValue('channel{:d}'.format(i+1),self.channeldata[i][:3])

        settings.setValue('windowposition',self.pos())
        settings.setValue('windowsize',self.size())
        settings.sync()
        self.loop.stop()


async def process_events(qapp):
    while True:
        await asyncio.sleep(0)
        qapp.processEvents()
#        print(qapp.allWidgets())
#        print(len(qapp.allWidgets()))
#        qapp.connect.lastWindowClosed(lambda: qapp.quit())

def icon():
    iconstring = ["20 20 3 1","   c #FFFFFF",".  c #000000","+  c #FDFDFD",
                "                    ","                    ","                    ","                ... ","                ....",
                "                ....","   ........     . ..","   .      .     . . ","   .      .     .   ","   ........     .   ",
                "   .      .     .   ","   .      .     .   ","   .      .     .   ","+  .      .  ....   "," ...      . .....   ",
                "....      . .....   ","....    ...  ...    "," ..    ....         ","       ....         ","        ..          "]
    return iconstring
if __name__=="__main__":
    a = QApplication(sys.argv)
    a.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(icon())))
    import ctypes
    myappid = u'mycompany.myproduct.subproduct.version' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    loop = asyncio.get_event_loop()
    w = AD9959Gui(loop)
    #loop.create_task(process_events(a))
    #loop.run_forever()
#    try:
    loop.run_until_complete(process_events(a))
  #  finally:
   #     loop.close()

    #loop.call_soon(process_events(a),loop)



