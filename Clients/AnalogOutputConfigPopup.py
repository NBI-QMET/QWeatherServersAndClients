#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Analog output configuration popup window

"""

from PyQt5.QtWidgets import *
from PyQt5 import QtGui,QtCore
import sys
import asyncio
import time
import numpy as np
import pyqtgraph as pg
import pandas as pd

__author__ = 'MT'
__version__ = '0.9'
__email__ = ''

class aowindow(QSplitter):

    sendAOsignal = QtCore.pyqtSignal(list) # Enables sending AO data to other scripts
    
    def __init__(self):
        super(aowindow, self).__init__()
        
        self.AOdata = [] # Contains AO data in form of time and voltage arrays to send
        self.aowaveform = {"waveform": "none"} # Dictionary with information characterizing analog signal
        
        self.setWindowTitle('Analog Output Configuration')
        self.setFont(QtGui.QFont('Helvetica',12))
        
        self.configpanel = self.make_aoconfigpanel() # Make AO configuration buttons
        self.plotpanel = self.make_aoplotpanel() # Make plot panel
        
        self.addWidget(self.configpanel)
        self.addWidget(self.plotpanel)
        self.show()
    
    def make_aoplotpanel(self):
        plotpanel = QFrame() # popup as window
        
        plotpanel.aoplotfig = pg.PlotWidget()
        plotpanel.aoplotfig.setYRange(-5,5)
        plotpanel.aoplotfig.setLabel('left', 'Voltage [V]', color='white', size=30)
        plotpanel.aoplotfig.setLabel('bottom', 'Time [s]', color='white', size=30)
        plotpanel.aoplotfig.showGrid(x=True, y=True)
    
        layout = QGridLayout()
        layout.addWidget(plotpanel.aoplotfig,0,0)

        plotpanel.setLayout(layout)
        plotpanel.show()
        return plotpanel
    
    def make_aoconfigpanel(self):
        configpanel = QFrame() # Buttons to choose waveform
        
        loadButtonObj = QPushButton('Load waveform')
        constantButtonObj = QPushButton('Constant')
        triangleButtonObj = QPushButton('Triangle')
        squareButtonObj = QPushButton('Square')
        MOTsignalButtonObj = QPushButton('MOT control signal')
        ApplyButtonObj = QPushButton('Apply')

        self.configlayout = QGridLayout()
        self.configlayout.addWidget(loadButtonObj,0,0)
        self.configlayout.addWidget(constantButtonObj,1,0)
        self.configlayout.addWidget(triangleButtonObj,2,0)
        self.configlayout.addWidget(squareButtonObj,3,0)
        self.configlayout.addWidget(MOTsignalButtonObj,4,0)
        self.configlayout.addWidget(ApplyButtonObj,5,0)
        self.nBaseWidgets = self.configlayout.count() # Find number of widgets in layout
        
        loadButtonObj.clicked.connect(lambda: self.loadButton())
        constantButtonObj.clicked.connect(lambda: self.constantButton())
        triangleButtonObj.clicked.connect(lambda: self.triangleButton())
        squareButtonObj.clicked.connect(lambda: self.squareButton())
        MOTsignalButtonObj.clicked.connect(lambda: self.MOTsignalButton())
        ApplyButtonObj.clicked.connect(lambda: self.updateWaveform())
        
        configpanel.setLayout(self.configlayout)
        configpanel.show()
        return configpanel
        
    def loadButton(self):
        self.aowaveform.clear() # Clear waveform dictionary
        self.aowaveform["waveform"] = "Load" # Waveform type
        self.modify_config(self.aowaveform,self.configlayout,self.nBaseWidgets) # Update the AO configuration GUI
        
        loadfilename, _ = QtGui.QFileDialog.getOpenFileName(None,'Load file','Z:\Dataprogrammer\Qweather\Config files','Comma-separated (*.csv)')
        
        if loadfilename != '':
            dataframe = pd.read_csv(loadfilename)
            t = np.float64(dataframe.iloc[:,0].tolist())
            U = np.float64(dataframe.iloc[:,1].tolist())
            aowindow.plotWaveform(self,self.plotpanel,t,U)
    
    def constantButton(self):
        self.aowaveform.clear() # Clear waveform dictionary
        self.aowaveform["waveform"] = "Constant" # Waveform type
        self.aowaveform["dt"] = 1e-6 # seconds
        self.aowaveform["voltage"] = 1 # Volt
        aowindow.modify_config(self,self.aowaveform,self.configlayout,self.nBaseWidgets) # Update the AO configuration GUI
        
        [t,U] = aowindow.waveformToData(self,self.aowaveform)
        aowindow.plotWaveform(self,self.plotpanel,t,U)
    
    def triangleButton(self):
        self.aowaveform.clear() # Clear waveform dictionary
        self.aowaveform["waveform"] = "Triangle" # Waveform type
        self.aowaveform["dt"] = 1e-6 # seconds
        self.aowaveform["period"] = 0.1 # seconds
        self.aowaveform["amplitude"] = 1 # Volt
        self.aowaveform["offset"] = 0 # Volt
        aowindow.modify_config(self,self.aowaveform,self.configlayout,self.nBaseWidgets) # Update the AO configuration GUI
        
        [t,U] = aowindow.waveformToData(self,self.aowaveform)
        aowindow.plotWaveform(self,self.plotpanel,t,U)
        
    def squareButton(self):
        self.aowaveform.clear() # Clear waveform dictionary
        self.aowaveform["waveform"] = "Square" # Waveform type
        self.aowaveform["dt"] = 1e-6 # seconds
        self.aowaveform["period"] = 0.1 # seconds
        self.aowaveform["amplitude"] = 1 # Volt
        self.aowaveform["offset"] = 0 # Volt
        aowindow.modify_config(self,self.aowaveform,self.configlayout,self.nBaseWidgets) # Update the AO configuration GUI
        
        [t,U] = aowindow.waveformToData(self,self.aowaveform)
        aowindow.plotWaveform(self,self.plotpanel,t,U)
        
    def MOTsignalButton(self):
        self.aowaveform.clear() # Clear waveform dictionary
        self.aowaveform["waveform"] = "MOT" # Waveform type
        self.aowaveform["dt"] = 1e-6 # seconds
        self.aowaveform["Ublue"] = 3.3 # Volt, blue MOT reference voltage
        self.aowaveform["Ured"] = 1.15 # Volt, red MOT reference voltage
        self.aowaveform["Ucompensate"] = 0 # Volt, decaying compensation voltage
        self.aowaveform["tBlue"] = 0.2 # seconds, blue MOT duration
        self.aowaveform["tRed"] = 0.2 # seconds, red MOT duration
        self.aowaveform["tau"] = 10e-3 # seconds, decay time of coil and holder B-field
        self.aowaveform["tauSafetyBlue"] = 10e-3 # seconds, safety decay time when switching to high field
        self.aowaveform["tauSafetyRed"] = 10e-3 # seconds, safety decay time when switching to low field
        self.aowaveform["tauSafetyInit"] = 0 # Boolean
        aowindow.modify_config(self,self.aowaveform,self.configlayout,self.nBaseWidgets) # Update the AO configuration GUI
        
        [t,U] = aowindow.waveformToData(self,self.aowaveform) # Translate waveform to arrays
        aowindow.plotWaveform(self,self.plotpanel,t,U) # Plot U(t)


    def updateWaveform(self): # Use this to load numbers from boxes into waveform info
        
        i = self.nBaseWidgets
        for x in self.aowaveform: # Make widgets in layout
            if x != "waveform": # Make widgets in row
                self.aowaveform[x] = self.configlayout.itemAtPosition(i,1).widget().value() # Load value from box into waveform
                i+=1
        
        if self.aowaveform["waveform"] != "Load":
            [t,U] = aowindow.waveformToData(self,self.aowaveform) # Translate waveform to arrays
            aowindow.plotWaveform(self,self.plotpanel,t,U) # Plot U(t)

    def modify_config(self,aowaveform,layout,nBaseWidgets): # Update the AO configuration GUI
        
        i = layout.count() # Find number of widgets in layout
        while(i >= nBaseWidgets): # Loop over widgets, starting from end
            if layout.itemAtPosition(i,0) != None: # Widgets exist in row; delete it
                layout.itemAtPosition(i,0).widget().hide()
                layout.removeWidget(layout.itemAtPosition(i,0).widget())
                layout.itemAtPosition(i,1).widget().hide()
                layout.removeWidget(layout.itemAtPosition(i,1).widget())
            i-=1
        
        arow = []
        i = nBaseWidgets
        
        for x in aowaveform: # Make widgets in layout
            if x != "waveform": # Make widgets in row
                spinBox = mySpinbox()
                spinBox.setMinimum(-1e15) # By default, minimum is 0, which is bad
                spinBox.setDecimals(9) # Need plenty of decimals
                arow.append(spinBox)
                arow[-1].setValue(aowaveform[x])
                value = arow[-1].value()
                layout.addWidget(QLabel(x),i,0)
                layout.addWidget(arow[-1],i,1) # Add number cell "arow" to GUI
                i+=1
    
    def waveformToData(self,aowaveform):
        
        if aowaveform["waveform"] == "Constant":
            tmax = 0.1
            dt = aowaveform["dt"]
            offset = aowaveform["voltage"]
            
            steps = round(tmax/dt)+1
            t = np.linspace(0,tmax,steps)
            #t = np.arange(0,tmax,dt)
            U = np.linspace(offset,offset+1e-10,steps)
            U = list(U)
            t = list(t)
        elif aowaveform["waveform"] == "Triangle":
            dt = aowaveform["dt"]
            tmax = aowaveform["period"]
            ampl = aowaveform["amplitude"]
            offset = aowaveform["offset"]
            
            steps = round(tmax/dt)+1
            steps1 = round(steps/2)
            steps2 = steps-steps1
            t = np.linspace(0,tmax,steps)
            #t = np.arange(0,tmax,dt).tolist()
            U1 = np.linspace(-0.5*ampl,0.5*ampl,steps1)+offset
            U2 = np.linspace(0.5*ampl,-0.5*ampl,steps2)+offset
            U = list(U1)+list(U2)
        elif aowaveform["waveform"] == "Square":
            dt = aowaveform["dt"]
            tmax = aowaveform["period"]
            ampl = aowaveform["amplitude"]
            offset = aowaveform["offset"]
            
            steps = round(tmax/dt)+1
            steps1 = round(steps/2)
            steps2 = steps-steps1
            t = np.linspace(0,tmax,steps).tolist()
            #t = np.arange(0,tmax,dt).tolist()
            U1 = np.linspace(0.5*ampl,0.5*ampl,steps1)+offset
            U2 = np.linspace(-0.5*ampl,-0.5*ampl,steps2)+offset
            U = list(U1)+list(U2)
        elif aowaveform["waveform"] == "MOT":
            dt = aowaveform["dt"]
            Ublue = aowaveform["Ublue"]
            Ured = aowaveform["Ured"]
            Ucomp = aowaveform["Ucompensate"]
            tBlue = aowaveform["tBlue"]
            tRed = aowaveform["tRed"]
            tau = aowaveform["tau"]+1e-30
            tauSafetyBlue = aowaveform["tauSafetyBlue"]+1e-30
            tauSafetyRed = aowaveform["tauSafetyRed"]+1e-30
            tauSafetyInit = aowaveform["tauSafetyInit"]+1e-30
            
            tmax = tBlue+tRed
            steps = round(tmax/dt)+1
            blueSteps = round(tBlue/dt)
            redSteps = steps-blueSteps
            #t = np.arange(0,tmax,dt)
            t = np.linspace(0,tmax,steps)
            if abs(tauSafetyInit) < 1e-20:
                U1 = Ublue + Ucomp*np.exp(-t[0:blueSteps]/tau) - (Ublue-Ured+Ucomp)*np.exp(-t[0:blueSteps]/tauSafetyBlue)
                U2 = Ured - Ucomp*np.exp(-t[0:redSteps]/tau) + (Ublue-Ured+Ucomp)*np.exp(-t[0:redSteps]/tauSafetyRed)
                U = list(U1)+list(U2)
            else:
                U = Ublue + (Ured-Ublue)*(1/(1 + np.exp(-(t-tRed)/tauSafetyRed)) + 1/(1 + np.exp((t-t[-1])/tauSafetyBlue)) - 1/(1 + np.exp((t[0]-t)/tauSafetyBlue)))
                U = U - Ucomp*np.exp(-np.power((t-tRed+1*tauSafetyRed)/tau,2))
                U = list(U)
                    
            t = list(t)
        return [t,U]
    
    def plotWaveform(self,plotpanel,xlist,ylist):
        self.AOdata = [xlist,ylist] # Export U(t) data before plotting
        self.sendAOsignal.emit(self.AOdata) # Export U(t) data before plotting
        plotpanel.aoplotfig.clear()
        plotpanel.aoplotfig.setLabel('left', 'Voltage [V]', color='white', size=30)
        plotpanel.aoplotfig.setLabel('bottom', 'Time [s]', color='white', size=30)
        plotpanel.aoplotfig.addItem(pg.PlotCurveItem(xlist,ylist,pen='w'))
        plotpanel.aoplotfig.showGrid(x=True, y=True)
        plotpanel.aoplotfig.addItem(pg.InfiniteLine(0,angle=0))

async def process_events(qapp):
    while True:
        await asyncio.sleep(0.1)
        qapp.processEvents()

class mySpinbox(QDoubleSpinBox):
    def __init__(self):
        super().__init__()
        self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.setDecimals(3)
        self.setMaximum(1000000)
        self.setLocale(QtCore.QLocale(QtCore.QLocale.English,QtCore.QLocale.UnitedStates)) #set locale to us, so decimal point means decimal point

    def textFromValue(self,value):
        return '{:.10n}'.format(value)

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
    w = aowindow()
    w.show()
    loop.create_task(process_events(a))
    loop.run_until_complete(process_events(a))


