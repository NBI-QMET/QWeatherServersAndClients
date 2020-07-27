#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''Server (Qweather) to grab data from the Rode&Schwartz HM03004 oscilloscope'''
from qweather import QWeatherServer, QMethod
import visa
import numpy as np
import time
import struct
import sys
__author__ = 'Asbjorn Arvad Jorgensen'
__version__ = '1.1'
__email__ = 'Asbjorn.Arvad@nbi.ku.dk'

class Server(QWeatherServer):

    def __init__(self,servername,serveradress):
        self.QWeatherStationIP = "tcp://10.90.61.231:5559"
        self.servername = servername+ 'OSC'
        self.address = 'TCPIP0::' + serveradress + '::INSTR'
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



    def get_channel_data(self,channels,maxpoints):
        if not isinstance(channels,list):
            head = self.hardware.query('CHAN{:d}:DATA:HEAD?'.format(channels)).split(',')
            if maxpoints:
                self.hardware.write('CHAN{:d}:DATA:POIN MAX'.format(channels))
            else:
                self.hardware.write('CHAN{:d}:DATA:POIN DEF'.format(channels))
            data = self.hardware.query_binary_values('CHAN{:d}:DATA?'.format(channels),datatype='f',is_big_endian=False)
        else:
            head = self.hardware.query('CHAN{:d}:DATA:HEAD?'.format(channels[0])).split(',')
            data = []
            for i in range(len(channels)):
                if maxpoints:
                    self.hardware.write('CHAN{:d}:DATA:POIN MAX'.format(channels[i]))
                else:
                    self.hardware.write('CHAN{:d}:DATA:POIN DEF'.format(channels[i]))
                data.append(self.hardware.query_binary_values('CHAN{:d}:DATA?'.format(channels[i]),datatype='f',is_big_endian=False))
        head = [float(ah.strip()) for ah in head]
        tlist = np.linspace(head[0],head[1],head[2]*head[3])

        return [tlist,data,head]

    @QMethod
    def single_measurement(self,channels,maxpoints = False,quick=False):
        if not quick:
            self.hardware.write('SING')
            time.sleep(1)
        tlist,data,head = self.get_channel_data(channels,maxpoints)
        Nsamples = head[2]
        samplerate = (head[1] - head[0])/Nsamples
        if not quick:
            self.hardware.write('RUN')
        return [tlist,data,[Nsamples,samplerate]]


    @QMethod 
    def repeat_measurements(self,channels,Nmeas):
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

    @QMethod
    def measure_peakpeak(self,channel,place,stat=False,stattime = 3):
        return self._measure_value(channel,place,'PEAK',stat,stattime)
    
    @QMethod
    def measure_mean(self,channel,place,stat=False,stattime = 3):
        return self._measure_value(channel,place,'MEAN',stat,stattime)
        
    @QMethod
    def measure_std(self,channel,place,stat=False,stattime = 3):
        return self._measure_value(channel,place,'STDD',stat,stattime)

    @QMethod
    def measure_minval(self,channel,place,stat=False,stattime = 3):
        return self._measure_value(channel,place,'LPE',stat,stattime)

    @QMethod
    def measure_maxval(self,channel,place,stat=False,stattime = 3):
        return self._measure_value(channel,place,'UPE',stat,stattime)

    def _measure_value(self,channel,place,measurement,stat,stattime):
        if not isinstance(channel,list):
            self.hardware.write('MEAS{:d}:SOUR CH{:d}'.format(place,channel))
            if stat:
                self.hardware.write('MEAS{:d}:STAT ON'.format(place))
                self.hardware.write('MEAS{:d}:STAT:RES'.format(place))
                time.sleep(stattime)
                avgval = float(self.hardware.query('MEAS{:d}:RES:AVG?').format(place))
                std = float(self.hardware.query('MEAS{:d}:RES:STDD?').format(place))
                minval = float(self.hardware.query('MEAS{:d}:RES:NPE?').format(place))
                maxval = float(self.hardware.query('MEAS{:d}:RES:PPE?').format(place))
                trigevents = int(self.hardware.query('MEAS{:d}:RES:WFMC?').format(place))

                data = [avgval,std,minval,maxval,trigevents]

            else:
                data = float(self.hardware.query('MEAS{:d}:RES? {:s}'.format(place,measurement)))
        else:
            for achan in channel:
                self.hardware.write('MEAS{:d}:SOUR CH{:d}'.format(achan,achan))
                if stat:
                    self.hardware.write('MEAS{:d}:STAT ON'.format(achan))
                    self.hardware.write('MEAS{:d}:STAT:RES'.format(achan))
            time.sleep(stattime)
            data = []
            for achan in channel:
                if stat:
                    avgval = float(self.hardware.query('MEAS{:d}:RES:AVG?'.format(achan)))
                    std = float(self.hardware.query('MEAS{:d}:RES:STDD?'.format(achan)))
                    minval = float(self.hardware.query('MEAS{:d}:RES:NPE?'.format(achan)))
                    maxval = float(self.hardware.query('MEAS{:d}:RES:PPE?'.format(achan)))
                    trigevents = int(self.hardware.query('MEAS{:d}:RES:WFMC?'.format(achan)))

                    data.append([avgval,std,minval,maxval,trigevents])
                else:
                    data.append(float(self.hardware.query('MEAS{:d}:RES? {:s}'.format(achan,measurement))))
        return data




if __name__ == "__main__":
    server = Server(*sys.argv[1:])
    server.run()


