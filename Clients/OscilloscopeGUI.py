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
import time
import h5py
import logging
import numpy as np
import os
import psutil
import sys
import traceback



__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '0.9'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'


class OscGui(QWidget):

    def __init__(self,loop = None):
        super().__init__()
        QWeatherStationIP = "tcp://10.90.61.13:5559"
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
        logging.getLogger().addHandler(self.logbox)
        logging.getLogger('asyncio').addHandler(self.logbox)
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('asyncio').setLevel(logging.DEBUG)
        self.logbox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                                  "%H:%M:%S"))
        self.PROCESS = psutil.Process(os.getpid())

        self.loop.create_task(self.client.run())

    def print_memory_usage(self):

        total, available, percent, used, free = psutil.virtual_memory()
        total, available, used, free = total / 10**6, available / 10**6, used / 10**6, free / 10**6
        proc = self.PROCESS.memory_info()[1] / 10**6
        print('process = %s total = %s available = %s used = %s free = %s percent = %s'
              % (proc, total, available, used, free, percent))


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
        self.progressbar = QProgressBar()
        self.progressbar.setTextVisible(True)
        self.filetype = QComboBox()
        self.filetype.addItem('txt')
        self.filetype.addItem('h5')


        self.logbox = QTextEditLogger(self)
        self.logbox.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        self.savebutton.pressed.connect(lambda :self.loop.create_task((self.save_traces(filepath.text(),scannumber.value(),oscselector.currentText()))))
        


        layout = QGridLayout()
        layout.addWidget(oscselector)
        layout.addWidget(filepath,1,0,1,6)
        layout.addWidget(browsepath,1,6,1,1)
        layout.addWidget(channels,2,0,4,2)
        layout.addWidget(scannumber,2,4)

        layout.addWidget(self.savebutton,2,5,2,2)
        layout.addWidget(self.filetype,2,7,1,2)
        layout.addWidget(self.progressbar,4,4,1,6)
        layout.addWidget(self.logbox.widget,6,0,1,10)
        self.setLayout(layout)

        self.show()

    async def save_traces(self,path,nscans,oscname):
        self.savebutton.setFlat(True)
        self.savebutton.setText('Working...')
        logging.info('Data taking begun')
        self.progressbar.setRange(0,nscans)
        osc = self.osclist[oscname]
        channels = [i+1 for i in range(len(self.channellist)) if self.channellist[i].isChecked()]
        refchannels = [i+1 for i in range(len(self.refchannellist)) if self.refchannellist[i].isChecked()]

        if len(path) == 0:
            errmsg = QMessageBox()
            errmsg.setText('No file path has been specified')
            errmsg.exec()
        elif len(channels) == 0:
            errmsg = QMessageBox()
            errmsg.setText('No channels have been specified')
            errmsg.exec()
        else:
            for j in range(nscans):
                data = []
                try:
                    for achannel in range(len(channels)-1):
                        self.print_memory_usage()
                        tmp = await osc.single_measurement(channels[achannel])
                        logging.info('got data from channel {:d}'.format(channels[achannel]))
                        data.append(tmp)
                    tmp = await osc.single_measurement(channels[-1])#,rerun=True)
                    data.append(tmp)
                    logging.info('got data from channel {:d}, rerunning oscilloscope'.format(channels[-1]))
                    newdata = [data[0][0],[adat[1] for adat in data]]
                    data = newdata
                    if len(refchannels) > 0:
                        refdata = []
                        for arefchannel in range(len(refchannels)):
                            tmp = await osc.single_measurement(refchannels[arefchannel],ref=True)
                            refdata.append(tmp)
                        newdata = [refdata[0][0],[adat[1] for adat in refdata],refdata[0][2]]
                        refdata = newdata
                    logging.info('Got data from oscilloscope')
                except Exception as e:
                    logging.exception(e)
                    self.savebutton.setText('SAVE')
                    donebox = QMessageBox()
                    donebox.setText('Failed at getting data')
                    donebox.exec()
                try:
                    t = data[0]
                    chandata = data[1]
                    if len(refchannels)> 0:
                        reftime = refdata[0]
                        refchandata = refdata[1]

                    if self.filetype.currentText() == 'h5':
                        h5f = h5py.File(path + '_{:03d}.h5'.format(j+1), 'w')
                        h5f.create_dataset('time', data=t)
                        for achan in range(len(chandata)):
                            h5f.create_dataset('chan_{:d}'.format(achan), data=chandata[achan])
                            logging.info('wrote data')
                        if len(refchannels)> 0:
                            h5f.create_dataset('reftime', data=reftime)
                            for achan in range(len(refchandata)):
                                h5f.create_dataset('refchan_{:d}'.format(achan), data=refchandata[achan])
                        h5f.close()
                    elif self.filetype.currentText() == 'txt':
                        if len(data) == 3:
                            head = data[2]
                        else:
                            head = None
                        with open(path + '_{:03d}.txt'.format(j+1), 'w') as f:
                            headerstr = ''
                            if head is not None:
                                headerstr += 'Samplerate {:.3e}, Npoints {:}\n'.format(head[1],head[0])
                            headerstr += 'time(ms)'
                            for achan in channels:
                                headerstr += '\t Chan{:d} (V)'.format(achan)
                            f.write(headerstr + '\n')
                            NChans = len(chandata)
                            for apoint in zip(t,*chandata):
                                writestring = ""
                                writestring += '{:e}'.format(apoint[0])
                                for i in range(NChans):
                                    writestring += '\t {:e}'.format(apoint[i+1])
                                writestring += '\n'
                                f.write(writestring)
                                
                        f.close()
                        if len(refchannels)>0:
                            with open(path + 'Ref__{:03d}.txt'.format(j+1), 'w') as f:
                                headerstr = ''
                                if head is not None:
                                    headerstr += 'Samplerate {:.3e}, Npoints {:}\n'.format(head[1],head[0])
                                headerstr += 'time(ms)'
                                for achan in refchannels:
                                    headerstr += '\t RefChan{:d} (V)'.format(achan)
                                f.write(headerstr + '\n')
                                NChans = len(refchandata)
                                for apoint in zip(reftime,*refchandata):
                                    writestring = ""
                                    writestring += '{:e}'.format(apoint[0])
                                    for i in range(NChans):
                                        writestring += '\t {:e}'.format(apoint[i+1])
                                    writestring += '\n'
                                    f.write(writestring)
                                    
                            f.close()
                except Exception as e:
                    logging.exception(e)
                    donebox = QMessageBox()
                    donebox.setText('Failed at saving')
                    donebox.exec()
                    print(e)
                logging.info('Saved data')
                self.progressbar.setValue(j+1)
                time.sleep(0.5)
        self.savebutton.setFlat(False)
        donebox = QMessageBox()
        donebox.setText('Measurements done')
        donebox.exec()
        self.progressbar.reset()
        self.savebutton.setText('SAVE')


    def make_channel_panel(self):
        panel = QFrame()
        self.channellist = [QCheckBox() for i in range(4)]
        self.refchannellist = [QCheckBox() for i in range(4)]
        channellabel = [QLabel('{:d}'.format(i+1)) for i in range(4)]
        refchannellabel = [QLabel('R{:d}'.format(i+1)) for i in range(4)]
        channellabel2 = QLabel('Channels')
        channellabel2.setAlignment(QtCore.Qt.AlignCenter)
        layout=QGridLayout()
        for i in range(len(self.channellist)):
            layout.addWidget(self.channellist[i],1,i)
            layout.addWidget(channellabel[i],2,i)
        for i in range(len(self.refchannellist)):
            layout.addWidget(self.refchannellist[i],3,i)
            layout.addWidget(refchannellabel[i],4,i)

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

class QTextEditLogger(logging.Handler):
    def __init__(self, parent):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


async def process_events(qapp):
    while True:
        await asyncio.sleep(0)
        qapp.processEvents()
#        print(qapp.allWidgets())
#        print(len(qapp.allWidgets()))
#        qapp.connect.lastWindowClosed(lambda: qapp.quit())


if __name__=="__main__":
    a = QApplication(sys.argv)
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



