#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to grab data from the Agilent 34461A'''
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

class Server(QWeatherServer):

    def __init__(self):
        self.QWeatherStationIP = "tcp://10.90.61.231:5559"
        self.servername = 'AgiMM1'
        self.visaaddr = 'TCPIP0::10.90.61.221::INSTR'
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
        self.hardware = rm.open_resource(self.visaaddr)
        print('Multimeter server running. Made contact with:')
        print(self.hardware.query('*IDN?'))
        print('*'*50)
        self.hardware.timeout=2000
        self.hardware.write('CALC:FUNC AVER')
        self.hardware.write('CALC:STAT ON')
        self.hardware.write('SAMP:COUN MAX')
        #self.start_resistance_measurement()
#        self.hardware.write('*ese 0;*sre 0')
#        self.hardware.write('AUTO ONCE;:INP:IMP 50;')
    
    def poll_resistance(self):
        while True:
            with threadLock:
                #print('Logged')
                #data = 2
                #data = self.hardware.query('MEAS:RES?')
                #print(data)
                self.Rlist.append(float(self.hardware.query('MEAS:RES?')))
            time.sleep(1)

    @QMethod
    def start_resistance_measurement(self):
        global threadLock
        self.Rlist = []
        threadLock = threading.Lock()
        pollthread = threading.Thread(target=self.poll_resistance)
        pollthread.daemon  = True
        pollthread.start()

    @QMethod
    def measure_resistance(self):
        data = self.hardware.query('MEAS:RES?')
        return data

    @QMethod
    def measure_voltage(self):
        data = self.hardware.query('MEAS:VOLT:DC?')
        return data

    @QMethod
    def get_statistics(self):
        """
        **QMethod** Grabs the statistics of the current measurement and resets the statistics
        Returns:
            tuple( Average (Float), Max (Float), Min (Float),Npoints (Float))
            Measurement on screen (Float)

        """
        with threadLock:
            avg = np.mean(self.Rlist)
            std = np.std(self.Rlist)
            mx = np.max(self.Rlist)
            mn = np.min(self.Rlist)
            Npoints = len(self.Rlist)
            self.Rlist = []
 
        return (avg,std,mx,mn,Npoints)






if __name__ == "__main__":
    server = Server()
    server.run()
