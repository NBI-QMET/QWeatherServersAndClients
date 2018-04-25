#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to grab data from the Rode&Schwartz HM03004 oscilloscope'''
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
        self.QWeatherStationIP = "tcp://172.24.22.3:5559"
        self.servername = 'HM03004OSC'
        self.address = 'TCPIP0::172.24.19.1::INSTR'
        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()

    def initialize_hardware(self):
        rm = visa.ResourceManager()
        self.hardware = rm.open_resource(self.address)
        print('Oscilloscope server running Made contact with:')
        print(self.hardware.query('*IDN?'))
        print('*'*50)
        self.hardware.write('FORM REAL; FORM MSBF')
        self.hardware.timeout=2000



    def get_channel_data(self,channels):
        if not isinstance(channels,list):
            head = self.hardware.query('CHAN{:d}:DATA:HEAD?'.format(channels)).split(',')
            data = self.hardware.query_binary_values('CHAN{:d}:DATA?'.format(channels),datatype='f',is_big_endian=True)
        else:
            head = self.hardware.query('CHAN{:d}:DATA:HEAD?'.format(channels[0])).split(',')
            data = []
            for i in range(len(channels)):
                data.append(self.hardware.query_binary_values('CHAN{:d}:DATA?'.format(channels[i]),datatype='f',is_big_endian=True))
        head = [float(ah.strip()) for ah in head]
        tlist = np.linspace(head[0],head[1],head[2]*head[3])

        return [tlist,data]

    @QMethod
    def single_measurement(self,channels):
        self.hardware.write('STOP')
        self.hardware.write('RUN')
        self.hardware.write('STOP')
#        self.hardware.write('RUNS')
#        
 #       time.sleep(1)
        tlist,data = self.get_channel_data(channels)
        return [tlist,data]


    @QMethod 
    def repeat_measurements(self,channels,Nmeas):
        data = []
        self.hardware.write('STOP')
        for i in range(Nmeas):
            self.hardware.write('RUN')
            self.hardware.write('STOP')
            data.append([])
            data[-1] = self.get_channel_data(channels)
        print('did something')
        return data

    '''
    def convert_binary_to_float(self,binary):
        if not isinstance(binary,list):
            binary = [binary]
        data = []
        for abinary in binary:
            data.append([])
            abinary = abinary[7:-1]
            adata = np.zeros(int(len(abinary)/4))
            for i in range(0,len(abinary),4):
                val = abinary[i:i+4]
  #              timeb = abinary[i+4:i+8]
                val = struct.unpack('>f',val)[0]
 #               time = int.from_bytes(timeb,'big')
                adata[int(i/4)] = val
#                adata[int(i/8)] = time
            #print(len(data),len(adata))
            data[-1] = adata
        return data
        '''



if __name__ == "__main__":
    server = Server()
    server.run()


