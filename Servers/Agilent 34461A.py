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
        self.QWeatherStationIP = "tcp://10.90.61.13:5559"
        self.servername = 'MMAgi'
        self.visaaddr = 'USB0::10893::4865::MY53202229::0::INSTR'
        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()
        print(self.measure_resistance())

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
#        self.hardware.write('*ese 0;*sre 0')
#        self.hardware.write('AUTO ONCE;:INP:IMP 50;')

    @QMethod
    def measure_resistance(self):
        data = self.hardware.query('MEAS:RES?')
        return data






if __name__ == "__main__":
    server = Server()
    server.run()
