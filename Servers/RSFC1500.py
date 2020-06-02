#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to control the Rigol DG1022 DDS'''
from qweather import QWeatherServer, QMethod
import visa
import numpy as np
import time
import struct
import sys
__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '1.0'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'


class Server(QWeatherServer):
    def __init__(self,name = None, address = None):
        self.QWeatherStationIP = "tcp://10.90.61.13:5559"
        if name is None and address is None:
            self.servername = 'RSESA1'
            self.address = 'TCPIP0::10.90.61.204::INSTR'
        else:
            self.servername = name
            self.address = 'TCPIP0::' + address + '::INSTR'

        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()

    def initialize_hardware(self):
        rm = visa.ResourceManager()
        self.hardware = rm.open_resource(self.address)
        print('Rigol DDS server running Made contact with:')
        print(self.hardware.query('*IDN?'))
        print(self.servername)
        print('*'*50)
        self.hardware.timeout=2000

if __name__ == "__main__":
    server = Server(name=name,address=addr)
    server.run()
