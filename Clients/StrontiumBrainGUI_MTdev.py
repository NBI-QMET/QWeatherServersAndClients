#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""GUI for the NI6259 Board used to control digital (and analog) IO in Sr 1 experiment
   Only works if the NI6259 server is running
"""

from PyQt5.QtWidgets import *
from PyQt5 import QtGui,QtCore
import sys
import asyncio
from qweather import QWeatherClient
import time
import numpy as np
import pyqtgraph as pg
from AnalogOutputConfigPopup import aowindow

__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '1.0'
__credits__ = 'Mikkel Tang'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'


class mySpinbox(QDoubleSpinBox):
    
    
    def __init__(self):
        super().__init__()
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.setDecimals(3)
        self.setMaximum(1000000)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English,QtCore.QLocale.UnitedStates)) #set locale to us, so decimal point means decimal point


    def textFromValue(self,value):
        return '{:.10n}'.format(value)


class SrBrainGui(QWidget):

    
    def __init__(self,loop = None):
        super().__init__()
        QWeatherStationIP = "tcp://10.90.61.231:5559"
        name = 'Sr1Gui'
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        self.client = QWeatherClient(QWeatherStationIP,name=name,loop=self.loop)
        self.Srbrain = self.client.StrontiumBrain
        self.setWindowTitle('Strontium Pulse GUI')
        self.setFont(QtGui.QFont('Helvetica',12))
        self.initialize_GUI()
        self.loop.create_task(self.client.run())


    def initialize_GUI(self):
        SRbrainpanel = self.make_SRbrainpanel()
        buttonpanel = self.make_buttonspanel()
        

        layout = QVBoxLayout()
        layout.addWidget(buttonpanel)
        layout.addWidget(SRbrainpanel)

        self.setLayout(layout)

        self.show()


    def make_SRbrainpanel(self):
        panel = QSplitter()

        timingpanel = QFrame()

        if self.Srbrain is None:
            layout = QHBoxLayout()
            layout.addWidget(QLabel('StrontiumBrain not connected...'))
            panel.setLayout(layout)
        else:
            self.channelsDO, channelsAI, self.channelsAO = self.Srbrain.getChannelList()
            self.channelsDO = sorted(self.channelsDO)
            self.channelsAO = sorted(self.channelsAO)
            timinglayout = QtGui.QGridLayout()
            timinglayout.addWidget(QLabel('On/Off'),0,0)
            timinglayout.addWidget(QLabel('Name'),0,1)
            self.timeresolution = QComboBox()
            self.timeresolution.addItem('ms')
            self.timeresolution.setItemData(0,1e-3) 
            self.timeresolution.addItem('us') 
            self.timeresolution.setItemData(1,1e-6) 
            self.timeresolution.setEditable(False)
            timinglayout.addWidget(self.timeresolution,0,2)
#            timinglayout.addWidget(QLabel('Switches...'),0,2)
            helpbutton = QPushButton('Help')
            helpbutton.pressed.connect(lambda: QMessageBox.information(self, 
                                      'Oh shit - how does it work?', 
                                      "Timings are in us.\nEach timing indicates a switch from the previous state,\nwithout knowledge of what the previous state was.\nIf On/Off is checked, an uneven number of switches must happen. Else an even.",
                                       QMessageBox.Ok))
            add = QPushButton('+')
            subtract = QPushButton('-')
            save = QPushButton('Save')
            load = QPushButton('Load')
            timinglayout.addWidget(add,0,3)
            timinglayout.addWidget(subtract,0,4)
            timinglayout.addWidget(save,1,2)
            timinglayout.addWidget(load,1,3)
            timinglayout.addWidget(helpbutton,1,4)
            self.timingboxesDO = []
            self.timingboxesAO = []
            self.tAO0 = []
            self.UAO0 = []
            self.tAO1 = []
            self.UAO1 = []
            self.tUnit = 1e3 # Multiply by 1e3 to view 0.001 s as 1 ms, etc...
            self.aopanels = []
            self.channelOnDict = {}
            for name in self.channelsDO:
                startOn = QCheckBox()
                label = QLabel(name)
                currentrow = timinglayout.rowCount()
                timinglayout.addWidget(startOn,currentrow,0)
                timinglayout.addWidget(label,currentrow,1)
                self.channelOnDict[name] = False

                startOn.stateChanged.connect(lambda state, aname=name:self.onoff_changed(state,aname))

                self.timingboxesDO.append([])
                for i in range(3):
                    spinBox =mySpinbox()
                    self.timingboxesDO[-1].append(spinBox)
                    timinglayout.addWidget(self.timingboxesDO[-1][i],currentrow,i+2)
            for name in self.channelsAO:
                startOn = QCheckBox()
                label = QLabel(name)
                currentrow = timinglayout.rowCount()
                timinglayout.addWidget(startOn,currentrow,0)
                timinglayout.addWidget(label,currentrow,1)
                self.channelOnDict[name] = False

                startOn.stateChanged.connect(lambda state, aname=name:self.onoff_changed(state,aname))
                
                # Add button to configure AO signal and open popup. Unlike the DO boxes this is just informative and the info is edited with AO popup.
                if "0" in name: # AO0 channel
                    self.aoconfig = QPushButton('Configure')
                    timinglayout.addWidget(self.aoconfig,currentrow,2)
                    self.aoconfig.pressed.connect(lambda: SrBrainGui.make_aowindow(self))
                elif "1" in name: # AO1 channel
                    self.aoconfig1 = QPushButton('Configure')
                    timinglayout.addWidget(self.aoconfig1,currentrow,2)
                    self.aoconfig1.pressed.connect(lambda: SrBrainGui.make_aowindow1(self))
                
                # Add box to show the AO signal cycle time
                self.timingboxesAO.append([])
                spinBox =mySpinbox()
                self.timingboxesAO[-1].append(spinBox)
                timinglayout.addWidget(self.timingboxesAO[-1][0],currentrow,4)
                
            self.timeresolution.currentIndexChanged.connect(self.change_timeresolution)
            add.pressed.connect(lambda: self.modify_timings(self.timingboxesDO,timinglayout)) # Add switch time for DO
            subtract.pressed.connect(lambda: self.modify_timings(self.timingboxesDO,timinglayout,False)) # Remove switch time for DO
            save.pressed.connect(self.timings_save)
            load.pressed.connect(lambda: self.timings_load(timinglayout))
            timingpanel.setLayout(timinglayout)
            
            self.plotfig = pg.PlotWidget()
            self.plotfig.setYRange(0,len(self.channelsDO))
            panel.addWidget(timingpanel)
            panel.addWidget(self.plotfig)
        return panel


    def change_timeresolution(self,index):
        timeres = self.timeresolution.itemData(index)
        if timeres == 1e-6:
            modifier = 1e3
        elif timeres == 1e-3:
            modifier = 1e-3

        for arow in self.timingboxesDO:
            for abox in arow:
                abox.setValue(abox.value()*modifier)
        
        for arow in self.timingboxesAO:
            for abox in arow:
                abox.setValue(abox.value()*modifier)


    def timings_save(self):
        savefilename, _ = QtGui.QFileDialog.getSaveFileName(None,'Save file','Z:\Dataprogrammer\Qweather\Config files\Timings.dat','Timing files (*.dat)')
        if savefilename is not '':
            with open(savefilename,'w') as f:
                f.write('Time resolution = ' + self.timeresolution.currentText() + '\n')
                for aname,arow in zip(self.channelsDO,self.timingboxesDO):
                    f.write(aname)
                    for abox in arow:
                        f.write('\t' + str(abox.value()))
                    f.write('\n')


    def timings_load(self,layout):
        loadfilename, _ = QtGui.QFileDialog.getOpenFileName(None,'Load file','Z:\Dataprogrammer\Qweather\Config files','Timing files (*.dat)')
        loadchannels = []
        loadrows = []
        if loadfilename is not '':
            with open(loadfilename ,'r') as f:
                for line in f:
                    keyargs = line.split('=')
                    if len(keyargs) > 1:
                        if keyargs[0].strip() == 'Time resolution':
                            self.timeresolution.setCurrentText(keyargs[1].strip())
                    else:
                        loadrows.append([])
                        columns = line.split('\t')
                        loadchannels.append(str(columns[0]))
                        for acolumn in columns[1:]:
                            loadrows[-1].append(float(acolumn))
                if self.channelsDO == loadchannels:
                    columns = len(loadrows[0])
                    while columns > len(self.timingboxesDO[0]):
                        self.modify_timings(self.timingboxesDO,layout)

                    for arow in range(len(loadrows)):
                        for acolumn in range(len(loadrows[arow])):
                            self.timingboxesDO[arow][acolumn].setValue(loadrows[arow][acolumn])


    def make_buttonspanel(self):
        panel = QFrame()

        armButton = QPushButton('Arm Pattern')
        startTimingButton = QPushButton('Start Pattern')
        stopTimingButton = QPushButton('Stop Pattern')

        if self.Srbrain is not None:
            armButton.clicked.connect(self.arm_pattern)
            startTimingButton.clicked.connect(lambda state:self.Srbrain.startSequence())
            stopTimingButton.clicked.connect(lambda state:self.Srbrain.stopSequence())
        else:
            for i in [armbutton,startTimingButton,stopTimingButton]:
                i.setEnabled(False)

        layout = QGridLayout()
        layout.addWidget(armButton,0,0)
        layout.addWidget(startTimingButton,0,1)
        layout.addWidget(stopTimingButton,0,2)

        panel.setLayout(layout)
        return panel


    def onoff_changed(self,state,name):
        self.channelOnDict[name] = state
        
        self.Srbrain.clearDigitalSequence()
        self.Srbrain.clearAnalogOutput()
        for aname in self.channelsDO:
            if aname == name:
                if state:
                    self.Srbrain.addDigitalOutput(aname,0,1e-3)
                else:
                    self.Srbrain.addDigitalOutput(aname,0,0.5e-3)
        #self.Srbrain.clearAnalogSequence()
        for aname in self.channelsAO:
            if aname == name:
                if state:
                    self.Srbrain.addAnalogOutput(aname,0,1e-3)
                else:
                    self.Srbrain.addAnalogOutput(aname,0,0.5e-3)
        self.Srbrain.armSequence(self.UAO0,self.UAO1,user_Max_Time = 1e-3)
        self.Srbrain.startSequence(run_only_once=True)
        

    def modify_timings(self,boxes,layout,add = True): # Add DO switch time boxes
        currwidth = len(boxes)

        if add:
            for i,arow in enumerate(boxes):
                spinBox =mySpinbox()
                arow.append(spinBox)
                layout.addWidget(arow[-1],i+2,len(arow)+1)
        else:
            for arow in boxes:
                layout.removeWidget(arow[-1])
                arow[-1].hide()
                del arow[-1]
        allrows =[field for row in boxes for field in row]
        for firstbox,followingbox in zip(allrows,allrows[1:]):
            self.setTabOrder(firstbox,followingbox)


    def arm_pattern(self): # Arm digital and/or analog output patterns
        self.Srbrain.clearDigitalSequence()
        self.Srbrain.clearAnalogOutput()
        xdatalist = []
        ydatalist = []
        maxtime = 0
        for aname,achannelrow,rownumber in zip(self.channelsDO,self.timingboxesDO,range(len(self.channelsDO))):
            timings = sorted(list(set([i.value()*self.timeresolution.currentData() for i in achannelrow])))
            if timings[0] == 0:
                timings.pop(0)
            xdata = []
            ydata = []
            ylow = 0.25 + len(self.channelsDO) + len(self.channelsAO) -rownumber -1.5
            yhigh = 0.75 + len(self.channelsDO) + len(self.channelsAO) -rownumber -1.5
            if self.channelOnDict[aname]:
                timings.insert(0,0)
            if len(timings)%2 != 0:
                pass
            else:
                for tstart,tstop in zip(timings[::2],timings[1::2]):
                    if tstop> maxtime:
                        maxtime = tstop
                    self.Srbrain.addDigitalOutput(aname,tstart,tstop)
                    xdata += [tstart,tstart, tstop, tstop]
                    if len(ydata) == 0:
                        ydata +=[ylow, yhigh, yhigh, ylow]
                    else:
                        if ydata[-1] == yhigh:
                            ydata += [yhigh, ylow, ylow, yhigh]
                        else:
                            ydata += [ylow, yhigh, yhigh, ylow]
                xdatalist.append(np.array(xdata)*1000)
                ydatalist.append(np.array(ydata))
                
        for aname,achannelrow,rownumber in zip(self.channelsAO,self.timingboxesAO,range(len(self.channelsAO))):
            
            if len(self.tAO0) > 0 or len(self.tAO1) > 0: # Don't run this if there if the AO time array is empty
                if len(self.tAO0) > 0:
                    tstop = max(self.tAO0)
                else:
                    tstop = max(self.tAO1)
                if len(self.tAO1) > 0:
                    tstop = max({tstop,max(self.tAO1)})
                self.timingboxesAO[rownumber][0].setValue(tstop/self.timeresolution.currentData())# Update value displayed in GUI
                if tstop > maxtime:
                    maxtime = tstop
                    
                self.Srbrain.addAnalogOutput(aname,0.0,tstop,5.0) # Single value voltage
                
                if rownumber == 0 and len(self.tAO0) > 0:
                    xdatalist.append(np.float(1e3)*np.linspace(0,tstop,len(self.UAO0))) # UAO should be type np.float64
                    UAOrescaled = 0.5*(self.UAO0-min(self.UAO0))/(max(self.UAO0)-min(self.UAO0)) + len(self.channelsAO)-rownumber - 1.25
                    ydatalist.append(np.float(1)*UAOrescaled)
                elif rownumber == 1 and len(self.tAO1) > 0:
                    xdatalist.append(np.float(1e3)*np.linspace(0,tstop,len(self.UAO1))) # UAO should be type np.float64
                    UAOrescaled = 0.5*(self.UAO1-min(self.UAO1))/(max(self.UAO1)-min(self.UAO1)) + len(self.channelsAO)-rownumber - 1.25
                    ydatalist.append(np.float(1)*UAOrescaled)
                 
        maxtime += 1e-6 #added this to prevent some corner crashes when two signals have to turn off at the end of the time sequence.
        
        self.plot_timings(xdatalist,ydatalist) # Plot DO and AO signals
        self.Srbrain.armSequence(self.UAO0,self.UAO1,user_Max_Time = maxtime)
        
        
    def plot_timings(self,xlist,ylist):
        self.plotfig.clear()
        for i in range(len(xlist)):
            xdata = xlist[i]
            ydata = ylist[i]
            if len(xdata) > 0:
                self.plotfig.addItem(pg.InfiniteLine(min(ydata),angle=0))
                self.plotfig.addItem(pg.PlotCurveItem(xdata,ydata,pen='w'))
        
        
    def importAOdata(self,AOdata): # Import AO data from AO popup window
        [self.tAO0,self.UAO0] = AOdata # Get the data
        self.timingboxesAO[0][0].setValue(max(self.tAO0)/self.timeresolution.currentData()) # Update value displayed in GUI
    
    def importAOdata1(self,AOdata): # Import AO data from AO popup window
        [self.tAO1,self.UAO1] = AOdata # Get the data
        self.timingboxesAO[1][0].setValue(max(self.tAO1)/self.timeresolution.currentData()) # Update value displayed in GUI
    
        
    def make_aowindow(self): # Make AO configuration popup window
        self.aopopup = aowindow() # Make AO popup
        self.aopopup.sendAOsignal.connect(self.importAOdata) # Connect to AO popup
        
    def make_aowindow1(self): # Make AO configuration popup window
        self.aopopup1 = aowindow() # Make AO popup
        self.aopopup1.sendAOsignal.connect(self.importAOdata1) # Connect to AO popup


async def process_events(qapp):
    while True:
        await asyncio.sleep(0.1)
        qapp.processEvents()


def icon():
    iconstring = ["60 60 106 2 ","   c #000000",".  c #DF3F3F","X  c #BF7F00","o  c #C76F0F","O  c #C07E00","+  c #C6710D","@  c #CB6716","#  c #C76F10","$  c #C96B13","%  c #D74F2E","&  c #D35727","*  c #D25A25","=  c #D5532B",
    "-  c #DE413D",";  c #DF3F40",":  c #E33747",">  c #E13B43",",  c #EB2757","<  c #EA2955","1  c #ED245A","2  c #F31767","3  c #F21866","4  c #F5146B","5  c #FB0777","6  c #FD037B","7  c #BD8304","8  c #BA8809","9  c #AF9F1F",
    "0  c #B39617","q  c #B39718","w  c #B19B1C","e  c #AF9F20","r  c #AEA122","t  c #A7AF30","y  c #A5B334","u  c #A3B738","i  c #A2B93A","p  c #9CC647","a  c #9BC748","s  c #97CE4F","d  c #99CB4C","f  c #91DB5C","g  c #8FDF60",
    "h  c #8FE061","j  c #87EE6F","k  c #89EB6C","l  c #84F676","z  c #83F778","x  c #82F97A","c  c #010483","v  c #050C8B","b  c #091594","n  c #0E1E9D","m  c #0F209F","M  c #0F21A0","N  c #1022A1","B  c #152DAC","V  c #1730AF",
    "C  c #1731B0","Z  c #1832B0","A  c #1D3DBC","S  c #1F40BF","D  c #1F41C0","F  c #2042C0","G  c #264DCC","H  c #2750CF","J  c #2751D0","K  c #2853D1","L  c #2E5FDE","P  c #2F60DF","I  c #2F61E0","U  c #3164E3","Y  c #3368E6",
    "T  c #3975F4","R  c #3B78F7","E  c #3C7AFA","W  c #FA0C8B","Q  c #F8108F","!  c #F81090","~  c #F41897","^  c #F31B9A","/  c #EE25A4","(  c #E92DAC",")  c #E732B1","_  c #7EFE82","`  c #79F58B","'  c #74EA96","]  c #72E69A",
    "[  c #6CDBA5","{  c #6AD6A9","}  c #6BD8A8","|  c #65CBB5"," . c #63C7B9",".. c #63C8B9","X. c #5DBCC4","o. c #5BB8C8","O. c #4FA1DF","+. c #54A9D6","@. c #51A4DC","#. c #53A8D8","$. c #4F9FE1","%. c #4791EF","&. c #4892EE",
    "*. c #458CF4","=. c #4388F8","-. c gray100",
"-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.                                                  -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.-.-.-.-.          H -.I -.T -.*.-.O.-.o.-...-.{ -.  -.8 -.+ -.* -.-   -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.-.      m -.V -.A -.H -.P -.T -.*.-.O.-.o.-...-.{   r -.8 -.+ -.* -.-     -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.  v -.b -.n -.V -.A -.G -.L -.T -.=.-.O.-.o.-. .-.  -.r -.8 -.+ -.* -.- -.  -.-.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.  c -.v -.b -.n -.B -.A -.G -.L -.T -.*.-.O.-.o.-. .  i -.r -.8 -.+ -.* -.- -.  -.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.  c -.c -.v -.b -.n -.B -.A -.G -.L -.T -.=.-.O.-.o.-.  -.i -.r -.7 -.+ -.* -.- -.  -.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.  c -.c -.c -.c -.v -.n -.B -.Z -.G -.L -.T -.=.-.$.-.  -.s -.i -.r -.7 -.+ -.* -.- -.  -.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.  c -.c -.c -.v -.b -.n -.B -.A -.G -.L -.T -.*.-.$.-.  -.g -.s -.i -.r -.8 -.+ -.* -.- -.  -.-.-.-.-.-.-.-.-.-.",
"-.-.-.  v -.c -.c -.v -.b -.n -.B -.A -.G -.L -.T -.=.-.$.-.  -.j -.g -.s -.i -.r -.7 -.# -.* -.- -.  -.-.-.-.-.-.-.-.-.",
"-.-.  b -.v -.c -.v -.b -.n -.V -.Z -.G -.L -.T -.*.-.O.-.  -.x -.j -.g -.s -.u -.e -.7 -.# -.* -.-   -.-.-.-.-.-.-.-.-.",
"-.-.  -.b -.v -.v -.b -.n -.B -.A -.H -.L -.T -.*.-.O.-.  -._ -.x -.j -.g -.s -.i -.r -.7 -.# -.& -.  -.-.-.-.-.-.-.-.-.",
"-.    N -.b -.v -.b -.M -.V -.A -.H -.L -.T -.*.-.O.-.  -.` -._ -.x -.k -.h -.s -.y -.e -.7 -.o -.*   -.-.-.-.-.-.-.-.-.",
"-.  Z -.N -.b -.b -.m -.V -.A -.H -.I -.T -.*.-.O.-.  -.] -.` -._ -.x -.j -.f -.s -.u -.9 -.7 -.#     -.-.-.-.-.-.-.-.-.",
"-.  -.Z -.N -.b -.m -.V -.A -.H -.I -.T -.*.-.O.-.  -.{ -.] -.` -._ -.z -.j -.f -.s -.u -.r -.7   6 -.  -.-.-.-.-.-.-.-.",
"-.  F -.Z -.N -.m -.V -.A -.H -.I -.R -.*.-.@.-.X.-. .-.{ -.] -.` -._ -.z -.j -.f -.d -.y -.9   4 -.5 -.  -.-.-.-.-.-.-.",
"-.  -.F -.C -.M -.V -.A -.H -.I -.R -.*.-.@.-.X.-...-.} -.] -.` -._ -.z -.j -.f -.d -.u -.9   < -.2 -.5 -.  -.-.-.-.-.-.",
"-.  K -.F -.C -.V -.S -.H -.U -.R -.*.-.@.-.o.-.| -.} -.] -.` -._ -.z -.k -.f -.s -.y -.9   > -.< -.2 -.5   -.-.-.-.-.-.",
"-.  -.K -.D -.V -.S -.J -.U -.R -.*.-.@.-.o.-...-.} -.] -.` -._ -.z -.k -.f -.d -.y -.9   & -.; -.< -.3 -.  -.-.-.-.-.-.",
"-.  Y -.K -.D -.S -.H -.U -.R -.%.-.@.-.X.-.| -.} -.] -.` -._ -.z -.k -.f -.d -.y -.9   $ -.& -.. -.< -.3   -.-.-.-.-.-.",
"-.  -.U -.K -.S -.H -.U -.R -.*.-.@.-.X.-.| -.[ -.' -.` -._ -.l -.k -.f -.d -.y -.9 -.7 -.# -.& -.. -.<   -.-.-.-.-.-.-.",
"-.  E -.Y -.K -.K -.U -.T -.*.-.@.-.X.-.| -.[ -.] -.` -._ -.l -.k -.f -.d -.y -.9 -.7 -.# -.& -.. -.< -.  -.-.-.-.-.-.-.",
"-.  -.E -.U -.K -.U -.E -.%.-.#.-.X.-.| -.[ -.] -.` -._ -.l -.k -.f -.d -.y -.w -.7 -.# -.& -.. -.< -.3   -.-.-.-.-.-.-.",
"-.  &.-.E -.U -.U -.E -.%.-.#.-.X.-.| -.[ -.] -.` -._ -.j -.k -.f -.a -.y -.w -.7 -.$ -.& -.; -.< -.2 -.  -.-.-.-.-.-.-.",
"-.  -.&.-.E -.U -.R -.%.-.@.-.X.-.| -.[ -.' -.` -._ -.l -.k -.f -.a -.y -.w -.7 -.# -.& -.> -.< -.2 -.5 -.  -.-.-.-.-.-.",
"-.  +.-.&.-.E -.R -.%.-.#.-.X.-.| -.[ -.' -.        l -.k -.f -.p -.y -.w -.7 -.$ -.= -.; -.< -.2 -.6 -.W   -.-.-.-.-.-.",
"-.  -.+.-.&.-.E -.%.-.+.-.X.-.| -.[ -.' -.  -.f -.k -.h -.f -.p -.y -.q -.7 -.$ -.= -.; -., -.4 -.5 -.W -.  -.-.-.-.-.-.",
"-.-.  -.+.-.&.-.&.-.+.-.X.-.| -.[ -.' -.  -.p -.f -.k -.f -.p -.y -.w -.7 -.$ -.& -.>   , -.2 -.5 -.W -.~   -.-.-.-.-.-.",
"-.-.-.  -.+.-.&.-.+.-.X.-.| -.[ -.' -.  -.t -.p -.f -.f -.p -.t -.q -.7 -.$ -.& -.> -.,     -.6 -.W -.~   -.-.-.-.-.-.-.",
"-.-.-.-.  -.+.-.+.-.X.-.| -.[ -.' -.  -.0 -.t -.p -.f -.p -.t -.q -.7 -.$ -.= -.> -., -.2 -.  -.W -.~ -.  -.-.-.-.-.-.-.",
"-.-.-.-.-.  -.#.-.X.-.| -.[ -.' -.  -.O -.0 -.t -.p -.p -.t -.w -.7 -.$ -.= -.> -.1 -.2 -.6 -.  -.~ -.  -.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.  -.X.-.{ -.[ -.' -.  -.@ -.X -.0 -.t -.p -.y -.w -.7 -.@ -.= -.> -., -.4 -.6 -.W -.      -.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.    | -.[ -.' -.  -.% -.@ -.X -.q -.t -.t -.q -.7   @ -.= -.> -., -.4 -.6 -.W -.~   -.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.-.            -.: -.% -.@ -.X -.q -.t -.q -.    = -.= -.> -.1 -.4 -.6 -.W -.~ -.  -.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.-.-.-.-.-.-.  1 -.: -.% -.@ -.X -.q -.q -.  -.: -.= -.> -.1 -.4 -.6 -.W -.~ -./   -.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.  1 -.: -.= -.@ -.X -.q -.  -.1 -.: -.> -.1 -.4 -.6 -.W -.~ -./ -.  -.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.  1 -.: -.= -.@ -.7 -.  -.4 -.1 -.> -.1 -.4 -.6 -.W -.~ -./ -.(   -.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.  1 -.: -.= -.$ -.  -.W -.4 -.1   1 -.4 -.6 -.W -.^ -./ -.( -.  -.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.                    -.-.-.-.  1 -.: -.= -.  -.! -.6 -.4 -.  -.4 -.6 -.W -.^ -./ -.( -.  -.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.                      -.-.-.-.-.                  W -.6 -.4 -.  -.6 -.W -.^ -./ -.( -.  -.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.    -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.  Q -.6 -.6 -.  -.W -.^ -./ -.(     -.-.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.    -.-.-.-.-.-.-.-.-.-.-.-.                  -.-.-.  Q -.6 -.W -.  -.^ -./ -.(   -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.    -.-.-.-.-.-.-.-.-.-.-.                      -.-.-.  Q -.W -.^ -.  -./ -.(   -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.    -.-.-.-.-.-.-.-.-.-.-.    -.-.-.-.-.-.-.    -.-.-.-.  W -.^ -./ -.        -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.    -.-.-.-.-.-.-.-.-.-.-.    -.-.-.-.-.-.-.    -.-.-.-.-.  ^ -./ -.(   -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.    -.-.-.-.-.-.-.-.-.-.-.    -.-.-.-.-.-.-.    -.-.-.-.-.  -./ -.( -.  -.-.          -.-.-.-.-.                -.",
"-.-.-.    -.-.-.-.-.-.-.-.-.-.-.    -.-.-.-.-.-.-.    -.-.-.-.-.  / -.( -.)   -.-.  -.-.-.  -.-.-.-.-.  -.-.-.-.-.-.-.-.",
"-.-.-.-.                  -.-.-.    -.-.-.-.-.-.-.    -.-.-.-.-.  -.( -.)   -.-.-.  -.-.-.  -.-.-.-.-.  -.-.-.-.-.-.-.-.",
"-.-.-.-.                    -.-.    -.-.-.-.-.-.-.    -.-.-.-.-.  ) -.)   -.-.-.-.  -.-.-.  -.-.-.-.-.  -.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.-.-.-.-.    -.-.    -.-.-.-.-.-.-.    -.-.-.-.-.        -.-.-.-.-.  -.-.-.  -.-.-.-.-.  -.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.-.-.-.-.    -.-.                      -.-.-.-.-.-.-.-.-.-.-.        -.-.-.              -.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.-.-.-.-.    -.-.                    -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.-.-.-.-.    -.-.    -.-.          -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.",
"-.-.-.-.-.-.-.-.-.-.-.-.    -.-.    -.-.-.          -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.                  -.-.-.-.-.-.      -.",
"-.-.-.-.-.-.-.-.-.-.-.-.    -.-.    -.-.-.-.-.-.    -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.  -.-.-.-.-.-.-.  -.-.-.-.-.-.  -.  -.",
"-.-.-.-.-.-.-.-.-.-.-.-.    -.-.    -.-.-.-.-.-.    -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.  -.-.-.-.-.-.-.  -.-.-.-.-.-.  -.  -.",
"-.-.-.                      -.-.    -.-.-.-.-.-.    -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.  -.-.-.-.-.-.-.  -.-.-.-.-.-.  -.  -.",
"-.-.-.                    -.-.-.    -.-.-.-.-.-.    -.-.-.-.-.-.-.-.-.-.-.-.-.-.-.  -.-.-.-.-.-.-.  -.-.-.-.-.-.  -.  -.",
"-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.    -.-.-.-.-.-.    -.-.-.-.-.-.-.-.-.-.-.-.        -.-.-.-.-.-.-.                -.  -.",
"-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-.-."]
    
    return iconstring
if __name__=="__main__":
    a = QApplication(sys.argv)
    a.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(icon())))
    import ctypes
    myappid = u'mycompany.myproduct.subproduct.version2' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    loop = asyncio.get_event_loop()
    w = SrBrainGui(loop)
    loop.create_task(process_events(a))
    loop.run_until_complete(process_events(a))


