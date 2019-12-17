#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to grab data from the HP531813A Frequency Counter'''
from qweather import QWeatherServer, QMethod
import visa
import numpy as np
import serial
import time
import datetime
import threading
__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '1.0'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'

class logging_thread(threading.Thread):
    
    def __init__(self, *args, **kwargs):
        super(logging_thread, self).__init__(*args, **kwargs)
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

class Server(QWeatherServer):

    def __init__(self):
        self.QWeatherStationIP = "tcp://10.90.61.13:5559"
        self.servername = 'FreqCounterAgilent'
        self.TCPIPaddr = 'TCPIP0::10.90.61.212::inst0::INSTR'
        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()

    '''
        self.hardware.write('CONF:FREQ')
        self.hardware.write('FREQ:GATE:TIME {:f};:SAMP:COUN 1000000')
        self.hardware.write('INIT')
        time.sleep(1)
        data = self.hardware.query('R?')
        data = data.split(',') #split string at commas
        data[0] = data[0].split('+',1)[1] #remove first bits (status bits)
        data = np.array([float(i) for i in data])
        print(data)
    '''

    def initialize_hardware(self):
        rm = visa.ResourceManager()
        self.hardware = rm.open_resource(self.TCPIPaddr)
        print('Frequency counter server running. Made contact with:')
        print(self.hardware.query('*IDN?'))
        print('*'*50)
        self.hardware.write('*cls;*rst')
        self.hardware.timeout=2000
#        self.hardware.write('*ese 0;*sre 0')
#        self.hardware.write('AUTO ONCE;:INP:IMP 50;')

    @QMethod
    def log_frequency(self,gatetime,savelocation,syncronize = False):
        self.hardware.write('DISP OFF')
        self.hardware.write('CONF:FREQ')
        self.hardware.write('FREQ:GATE:TIME {:f};:SAMP:COUN 1;:TRIG:COUN 1000000'.format(gatetime))
        if syncronize:
            print('syncronizing')
            self.hardware.write('TRIG:SOUR EXT')
            self.hardware.write('TRIG:SLOP POS')
            self.hardware.write('ROSC:EXT:FREQ 1E7')
            self.hardware.write('ROSC:SOUR EXT')
        else:
            self.hardware.write('TRIG:SOUR  IMM')
        self.logthread = logging_thread(target = self.do_logging,args =(gatetime,savelocation))
        self.logthread.start()

    def do_logging(self,gatetime,savelocation):
        date = str(datetime.datetime.now()).split(' ')[0]
        with open(savelocation + '/AGI53230A' + date + '.txt', 'w') as f:
            self.hardware.write('INIT') #initiate measurement
            f.write('Measurement started at: ' + str(datetime.datetime.now().astimezone()) + '\n')
            f.write('Counter: Agilent 53230A\n')
            f.write('Gatetime: {:f}\n'.format(gatetime))
            while not self.logthread.stopped():
                time.sleep(1)
                data = self.hardware.query('R?')
                f.write(data)
#            self.hardware.write('*cls;*rst')



    @QMethod
    def stop_logging(self):
        self.logthread.stop()



if __name__ == "__main__":
    server = Server()
    server.run()
