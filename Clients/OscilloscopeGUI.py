#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Gui for the oscilloscopes in our lab. Primarily to save multiple scans

"""

from PyQt5.QtWidgets import *
from PyQt5 import QtGui,QtCore
import sys
import asyncio
import datetime
from qweather import QWeatherClient

__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '0.9'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'


class OscGui(QWidget):

    def __init__(self,loop = None):
        super().__init__()
        QWeatherStationIP = "tcp://172.24.22.3:5559"
        name = 'OscilloscopeGuiSR'
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop
        self.client = QWeatherClient(QWeatherStationIP,name=name,loop=self.loop)
        self.setWindowTitle('Oscilloscopes')
        self.setFont(QtGui.QFont('Helvetica',12))
        self.initialize_osc()
        self.initialize_GUI()
        self.restore_GUI()
        self.loop.create_task(self.client.run())

    def initialize_osc(self):
        self.osclist = {}
        for aserv in self.client:
            if aserv.name[-3:] == 'OSC':
                self.osclist[aserv.name[:-3]] = aserv


    def initialize_GUI(self):
        oscselector = QComboBox()
        [oscselector.addItem(oscname) for oscname in self.osclist.keys()]


        filepath = QLineEdit()
        browsepath = QPushButton('...')

        browsepath.pressed.connect(lambda: filepath.setText(QFileDialog.getExistingDirectory() + '/'))

        scannumber = QSpinBox()
        scannumber.setRange(1,100)

        channels = self.make_channel_panel()
        

        self.savebutton = QPushButton('SAVE')


        self.savebutton.pressed.connect(lambda :self.loop.create_task((self.save_traces(filepath.text(),scannumber.value(),oscselector.currentText()))))

        layout = QGridLayout()
        layout.addWidget(oscselector)
        layout.addWidget(filepath,1,0,1,6)
        layout.addWidget(browsepath,1,6,1,1)
        layout.addWidget(channels,2,0,4,2)
        layout.addWidget(scannumber,2,4)

        layout.addWidget(self.savebutton,2,5,2,2)
        self.setLayout(layout)

        self.show()

    async def save_traces(self,path,nscans,oscname):
        self.savebutton.setFlat(True)
        self.savebutton.setText('Working...')
        osc = self.osclist[oscname]
        channels = [i+1 for i in range(len(self.channellist)) if self.channellist[i].isChecked()]
        if len(path) == 0:
            errmsg = QMessageBox()
            errmsg.setText('No file path has been specified')
            errmsg.exec()
        elif len(channels) == 0:
            errmsg = QMessageBox()
            errmsg.setText('No channels have been specified')
            errmsg.exec()
        else:
            data = await osc.repeat_measurements(channels,nscans)

        try:
            for j in range(len(data)):
                t = data[j][0]
                chandata = data[j][1]
                with open(path + oscname + '_{:03d}.txt'.format(j+1), 'w') as f:
                    headerstr = 'time(ms)'
                    for achan in channels:
                        headerstr += '\t Chan{:d} (V)'.format(achan)

                    f.write(headerstr + '\n')
                    NChans = len(chandata)
                    for apoint in zip(t,*chandata):
                        line = '{:e}'.format(apoint[0])
                        for i in range(NChans):
                            line += '\t {:e}'.format(apoint[i+1])
                        line += '\n'
                        f.write(line)
                f.close()
        except Exception as e:
            print(e)
        self.savebutton.setFlat(False)
        self.savebutton.setText('SAVE')



    def make_channel_panel(self):
        panel = QFrame()
        self.channellist = [QCheckBox() for i in range(4)]
        channellabel = [QLabel('{:d}'.format(i+1)) for i in range(4)]
        channellabel2 = QLabel('Channels')
        channellabel2.setAlignment(QtCore.Qt.AlignCenter)
        layout=QGridLayout()
        for i in range(len(self.channellist)):
            layout.addWidget(self.channellist[i],1,i)
            layout.addWidget(channellabel[i],2,i)
        layout.addWidget(channellabel2,0,0,1,4)


        panel.setLayout(layout)
        panel.setFrameStyle(0x00001)
        return panel

    def restore_GUI(self):
        settings = QtCore.QSettings('OscilloscopeGui.ini',QtCore.QSettings.IniFormat)

        for aspinbox in self.findChildren(QDoubleSpinBox) + self.findChildren(QSpinBox):
            name = aspinbox.objectName()
            if settings.contains(name):
                value = settings.value(name,type=float)
                aspinbox.setValue(value)




    def closeEvent(self,e):
        settings = QtCore.QSettings('OscilloscopeGui.ini',QtCore.QSettings.IniFormat)

        for aspinbox in self.findChildren(QDoubleSpinBox) + self.findChildren(QSpinBox):
            name = aspinbox.objectName()
            value = aspinbox.value()
            settings.setValue(name,value)

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
    iconstring = ["40 40 7 1","   c #000000",".  c #FFFFFF","+  c #D3C70C","@  c #6D6D6D","#  c #0006FF","$  c #A58D06","&  c #280CD3","                                        ",
" ...................................... "," .                            .       . "," .                            .       . "," .       ++                   .       . ",
" .      ++++                  .@@@@@@@. "," .     ++  +                  .       . "," .##   ++  ++           ####  . $$ $$ . "," . #  ++    +          ##  ## .  $ $  . ",
" . ## +      +        ##     #.       . "," .  #++      ++       #       . $  $  . "," .  ##        +      ##       .   $   . "," .  +#        ++    ##        . $$ $$ . ",
" .  +##       ++    #         .       . "," . ++ #        ++   #         .       . "," .++   #        +  ##        +.@@@@@@@. "," .+    ##       +  #        ++.    $  . ",
" .      #       + ##        + . $   $ . "," .      ##      ++#        +  .  $$  $. "," .       #       ##        +  .       . "," .       ##      #         +  . $ $   . ",
" .        #     ##+       +   .     $ . "," .        ##   ## +       +   . $$ $  . "," .         #   #  ++     ++   .      $. "," .         ## ##   +     +    .@@@@@@@. ",
" .           ##    ++   ++    .       . "," .                  +   +     . $ $$  . "," .                  ++++      .   $  $. "," .                    ++      . $     . ",
" .                            . $$    . "," .............................. $ $ $ . "," .& & && && &&&   & & &&&     .       . "," .& &     & & &   &&& & &     .@@@@@@@. ",
" .&&& &&  & &&& &   & &&&     .       . "," .                            . $  $$ . "," .+ + ++ +++   +++ + +        .   $  $. "," .+ +    + +   + + +++        . $$$$ $. ",
" .+++ ++ +++ + +++   +        .  $    . "," ...................................... ","                                        "]
    return iconstring
if __name__=="__main__":
    a = QApplication(sys.argv)
    a.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(icon())))
    import ctypes
    myappid = u'mycompany.myproduct.subproduct.version' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    loop = asyncio.get_event_loop()
    w = OscGui(loop)
    #loop.create_task(process_events(a))
    #loop.run_forever()
#    try:
    loop.run_until_complete(process_events(a))
  #  finally:
   #     loop.close()

    #loop.call_soon(process_events(a),loop)



