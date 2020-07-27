#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to control from the HP frequency generator'''
from qweather import QWeatherServer, QMethod
import visa
import numpy as np
import time
import struct
__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '1.0'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'

class Server(QWeatherServer):

    def __init__(self):
        self.QWeatherStationIP = "tcp://10.90.61.231:5559"
        self.servername = 'HP8648C'
        self.address = 'GPIB0::19::INSTR'
        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()

    def initialize_hardware(self):
        rm = visa.ResourceManager()
        self.hardware = rm.open_resource(self.address)
        print(self.hardware.query('*IDN?'))
        print('*'*50)
        self.hardware.timeout=2000



    @QMethod
    def setFrequency(self,frequency):
        '''Sets the frequency output (in megahertz)'''
        self.hardware.write('FREQ:CW {:3.6f}MHz'.format(frequency))

    @QMethod
    def getFrequency(self):
        '''returns the frequency output (in megahertz)'''
        return float(self.hardware.query('FREQ:CW?'))*1e-6




if __name__ == "__main__":
    server = Server()
    server.run()


