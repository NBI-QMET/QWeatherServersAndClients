#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to grab data from the Rode&Schwartz RTO1044 (big) oscilloscope'''
from qweather import QWeatherServer, QMethod
import visa
import numpy as np
import time, datetime
import struct
import h5py
import sys
import gc
import copy
__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '1.0'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'

class Server(QWeatherServer):
    def __init__(self,servername,serveradress):
        self.QWeatherStationIP = "tcp://10.90.61.13:5559"
        self.servername = servername+ 'OSC'
        self.address = 'TCPIP0::' + serveradress + '::INSTR'
        self.verbose = False
        self.debug = False
        self.initialize_sockets()
        print('*'*50)
        print('Server Online')
        self.initialize_hardware()

        self.save_scans(10,'Z:/MicrowaveReference/data/BeatnoteMeasurements/190708/22MHz 200Msps neg30dB unlock noAOM/',[1,2])

    def save_scans(self,nscans,path,channellist):
        """Take a bunch of single_measurements and save them to a path One file for each scan Filename is automatically appended with numbers.

        :param nscans: Number of scans to save
        :type nscans: int
        :param path: savepath
        :type path: str
        :param channellist: list of channels to take data from
        :type channellist: list,int"""
        channels = channellist
        for j in range(nscans):

            data = self.single_measurement(channels)
            with open(path + '_{:03d}_1.txt'.format(j+1), 'wb') as f:
            #with open(path + '_011_1.txt', 'wb') as f:
                f.write(data[1][0])
            with open(path + '_{:03d}_2.txt'.format(j+1), 'wb') as f:
            #with open(path + '_011_2.txt', 'wb') as f:
                f.write(data[1][1])
            print('done')
            del data
            gc.collect()

    def initialize_hardware(self):
        """Open the connection to the hardware using a visa connection"""
        rm = visa.ResourceManager()
        self.hardware = rm.open_resource(self.address)
        print('Oscilloscope server running Made contact with:')
        print(self.hardware.query('*IDN?'))
        print('*'*50)
        self.hardware.write('FORM REAL, 32')
        self.hardware.write('FORM:BORD MSB')
        self.hardware.timeout=20000




    def get_channel_data(self,channels):
        """Get data from channels

        :param channels: List of channels, or single channel to get data from
        :type channels: list, int
        :return: List of data in the form [tlist, datalist ,header]
        :rtype: list"""
        if not isinstance(channels,list):
            head = self.hardware.query('CHAN{:d}:DATA:HEAD?'.format(channels)).split(',')
            data = self.hardware.query_binary_values('CHAN{:d}:DATA?'.format(channels),datatype='d',is_big_endian=True)
        else:
            head = self.hardware.query('CHAN{:d}:DATA:HEAD?'.format(channels[0])).split(',')
            print(head)
            data = []
            print('starting to get data')
            print(datetime.datetime.now())
            self.hardware.write('CHAN1:EXP OFF')
            self.hardware.write('CHAN2:EXP OFF')
            self.hardware.write('CHAN3:EXP OFF')
            self.hardware.write('CHAN4:EXP OFF')
            for i in range(len(channels)):
                self.hardware.write('CHAN{:d}:EXP ON'.format(channels[i]))
                self.hardware.write('CHAN{:d}:DATA?'.format(channels[i]))
                a = self.hardware.read_bytes(1)
                if a == b'#':
                    a = int(self.hardware.read_bytes(1))
                    if a == 0:
                        print('Unknown length, not sure how to do')
                    else:
                        length = int(self.hardware.read_bytes(int(a)))
                        print(length)
                bstring = b''
                subdiv = int(length/10)
                while len(bstring) < length:
                    bstring += self.hardware.read_bytes(subdiv)
                    print(len(bstring))
                data.append(copy.deepcopy(bstring))
                del bstring
                gc.collect()

                #data.append(self.hardware.query_binary_values('CHAN{:d}:DATA?'.format(channels[i]),datatype='f',is_big_endian=True))
                print('finished getting data')
                print(datetime.datetime.now())
                self.hardware.write('CHAN{:d}:EXP OFF'.format(channels[i]))

        head = [float(ah.strip()) for ah in head]
        tlist = np.linspace(head[0],head[1],head[2]*head[3])

        return [tlist,data,head]

    @QMethod
    def single_measurement(self,channels):
        """Do a single measurement. Initialize the measurement and RUN oscilloscope when done

        :param channels: List of channels, or single channel to take data from
        :type channels: list,int
        :return: A list of lists containing [timearray,data,[number of samples,samplerate]]
        :rtype: list"""
        self.hardware.write('SING')
        time.sleep(2)

        tlist,data,head = self.get_channel_data(channels)

        Nsamples = head[2]
        samplerate = (head[1] - head[0])/Nsamples
        self.hardware.write('RUN')
        return [tlist,data,[Nsamples,samplerate]]


    @QMethod 
    def repeat_measurements(self,channels,Nmeas):
        """Repeat measurements. Initialize the measurement and RUN oscilloscope when done. Repeat N times. Each iteration is a new trigger on the oscilloscope.


        :param channels: List of channels, or single channel to take data from
        :type channels: list,int
        :param Nmeas: number of times to repeat taking data
        :type Nmeas: int
        :return: A list of lists of lists containing [timearray,data,[number of samples,samplerate]]xNmeans
        :rtype: list"""
        data = []
        #self.hardware.write('STOP')
        for i in range(Nmeas):
            self.hardware.write('STOP')
            data.append([])
            data[-1] = self.get_channel_data(channels)
            self.hardware.write('RUN')
            time.sleep(0.1)
        #self.hardware.write('RUN')
        return data




if __name__ == "__main__":
    server = Server(*sys.argv[1:])
    server.run()


